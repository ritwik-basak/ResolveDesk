// ============================================================
// ResolveDesk — useMetrics Custom Hook
// ============================================================
//
// WHAT THIS FILE DOES (will be built in Step 14):
//   A custom React hook that handles polling GET /metrics/live
//   every 5 seconds and returning the latest metrics data.
//
// WHAT IS A CUSTOM HOOK?
//   A custom hook is a JavaScript function whose name starts
//   with "use". It lets you extract reusable stateful logic
//   out of components. Instead of writing the polling logic
//   directly inside LiveMetricsPanel.jsx, we put it here so
//   it can be reused anywhere in the app.
//
// HOW IT WORKS:
//   1. On mount: immediately fetch /metrics/live
//   2. Set up a setInterval to re-fetch every 5000ms
//   3. Store result in React state
//   4. On unmount: clear the interval (cleanup)
//   5. Return the metrics data + a loading flag
//
// USAGE (in LiveMetricsPanel.jsx):
//   const { metrics, loading } = useMetrics();
// ============================================================

// Logic will be implemented in Step 14
