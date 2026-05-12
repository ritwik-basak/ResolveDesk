from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.analytics.tracker import supabase as _db
from backend.db.gcs import delete_file as gcs_delete
from backend.db.gcs import upload_file as gcs_upload
from backend.rag.ingest import SUPPORTED_EXTENSIONS, delete_file_data, ingest_file

router = APIRouter(prefix="/ingest", tags=["documents"])


# =============================================================================
# POST /ingest/upload
# =============================================================================

@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document and ingest it into the RAG pipeline.

    Supported formats: PDF, DOCX, TXT, MD, PPTX, CSV

    Steps:
      1. Validate extension
      2. Upload to GCS → get persistent URI
      3. Run LlamaIndex ingest: split → embed → Pinecone + Supabase chunks
      4. Rebuild BM25 index in the live retriever singleton
    """
    ext = Path(file.filename).suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type '{ext}'. "
                f"Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}"
            ),
        )

    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # ── Store raw file in GCS ─────────────────────────────────────────────
    gcs_blob = f"uploads/{file.filename}"
    try:
        gcs_uri = gcs_upload(file_bytes, gcs_blob)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GCS upload failed: {e}")

    # ── Run LlamaIndex ingest pipeline ───────────────────────────────────
    try:
        chunk_count = ingest_file(
            file_bytes=file_bytes,
            filename=file.filename,
            gcs_path=gcs_uri,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingest pipeline failed: {e}")

    # ── Rebuild BM25 in the live retriever ────────────────────────────────
    try:
        from backend.rag.retriever import retriever
        retriever.rebuild_bm25()
    except Exception:
        pass  # Non-fatal — retriever will use the previous BM25 index

    return {
        "status":      "ok",
        "filename":    file.filename,
        "chunk_count": chunk_count,
        "gcs_path":    gcs_uri,
    }


# =============================================================================
# DELETE /ingest/delete/{filename}
# =============================================================================

@router.delete("/delete/{filename}")
async def delete_document(filename: str):
    """
    Delete a document from all three storage layers:
      Pinecone (vectors) → Supabase chunks + documents → GCS (raw file)

    After deletion the BM25 index is rebuilt so keyword search no longer
    returns chunks from the deleted document.
    """
    # Look up GCS path stored at upload time
    result = (
        _db.table("documents")
        .select("gcs_path")
        .eq("filename", filename)
        .execute()
    )
    if not result.data:
        raise HTTPException(
            status_code=404, detail=f"Document '{filename}' not found."
        )

    gcs_uri  = result.data[0]["gcs_path"]
    # Convert "gs://bucket/uploads/file.pdf" → "uploads/file.pdf"
    blob_name = gcs_uri.split("/", 3)[-1] if gcs_uri.startswith("gs://") else gcs_uri

    # ── Delete from Pinecone + Supabase ──────────────────────────────────
    try:
        delete_file_data(filename)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Data deletion failed: {e}")

    # ── Delete from GCS ───────────────────────────────────────────────────
    try:
        gcs_delete(blob_name)
    except Exception:
        pass  # File may have been deleted manually — not fatal

    # ── Rebuild BM25 ─────────────────────────────────────────────────────
    try:
        from backend.rag.retriever import retriever
        retriever.rebuild_bm25()
    except Exception:
        pass

    return {"status": "ok", "filename": filename}


# =============================================================================
# GET /ingest/documents
# =============================================================================

@router.get("/documents")
async def list_documents():
    """
    Return all documents stored in the system with metadata.

    Each entry includes: doc_id, filename, upload_date, chunk_count,
    gcs_path, file_type.
    """
    result = (
        _db.table("documents")
        .select("*")
        .order("upload_date", desc=True)
        .execute()
    )
    return {"documents": result.data or []}
