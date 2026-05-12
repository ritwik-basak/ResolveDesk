# =============================================================================
# backend/db/gcs.py
# =============================================================================
# ResolveDesk — Google Cloud Storage Helper
#
# WHAT THIS DOES:
#   Simple wrapper around the GCS Python client.
#   Provides upload, delete, and list operations for a single GCS bucket.
#
# WHY GCS?
#   Cloud Run containers are ephemeral — any file written to the container
#   filesystem is lost when the container restarts. GCS is persistent storage
#   that survives restarts and is native to GCP.
#
# AUTHENTICATION:
#   Local dev:  set GOOGLE_APPLICATION_CREDENTIALS to the path of a
#               service account JSON key file downloaded from GCP Console.
#   Cloud Run:  attach a service account to the Cloud Run service in GCP.
#               The GCS client picks it up automatically via Application
#               Default Credentials — no env var needed.
#
# BUCKET:
#   Create the bucket once in GCP Console (or via gcloud).
#   Set GCS_BUCKET_NAME in .env to match.
# =============================================================================

import os

from dotenv import load_dotenv
from google.cloud import storage

load_dotenv()

GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "resolvedesk-documents")


def _client() -> storage.Client:
    return storage.Client()


# =============================================================================
# PUBLIC API
# =============================================================================

def upload_file(file_bytes: bytes, destination_blob_name: str) -> str:
    """
    Upload bytes to GCS.

    Args:
        file_bytes:            Raw file bytes (from an uploaded HTTP request).
        destination_blob_name: Path inside the bucket — e.g. "uploads/policy.pdf"

    Returns:
        The full GCS URI: "gs://{bucket}/{blob_name}"
    """
    bucket = _client().bucket(GCS_BUCKET_NAME)
    blob   = bucket.blob(destination_blob_name)
    blob.upload_from_string(file_bytes)
    return f"gs://{GCS_BUCKET_NAME}/{destination_blob_name}"


def delete_file(blob_name: str) -> None:
    """
    Delete a file from GCS.

    Args:
        blob_name: Path inside the bucket — e.g. "uploads/policy.pdf"
                   Strip "gs://{bucket}/" prefix before calling this.
    """
    bucket = _client().bucket(GCS_BUCKET_NAME)
    blob   = bucket.blob(blob_name)
    blob.delete()


def list_files(prefix: str = "uploads/") -> list[str]:
    """
    List all blob names in the bucket under the given prefix.

    Returns:
        List of blob paths — e.g. ["uploads/policy.pdf", "uploads/faq.csv"]
    """
    bucket = _client().bucket(GCS_BUCKET_NAME)
    blobs  = bucket.list_blobs(prefix=prefix)
    return [blob.name for blob in blobs]
