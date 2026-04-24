const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      // keep fallback
    }
    throw new Error(message);
  }
  return response.json();
}

export function getDashboard() {
  return request("/dashboard");
}

export function getReceipts() {
  return request("/receipts");
}

export function getTransactions() {
  return request("/transactions");
}

export function getReport() {
  return request("/report");
}

export function runReconciliation() {
  return request("/reconcile", { method: "POST" });
}

export function confirmMatch(matchId) {
  return request(`/reconcile/confirm/${matchId}`, { method: "POST" });
}

export function rejectMatch(matchId) {
  return request(`/reconcile/reject/${matchId}`, { method: "DELETE" });
}

export function uploadReceipt(file) {
  const formData = new FormData();
  formData.append("file", file);
  return request("/receipts/upload", { method: "POST", body: formData });
}

export function uploadTransactions(file) {
  const formData = new FormData();
  formData.append("file", file);
  return request("/transactions/upload", { method: "POST", body: formData });
}
