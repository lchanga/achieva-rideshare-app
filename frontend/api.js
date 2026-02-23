import { API_BASE_URL, ENDPOINTS } from "./config.js";

async function jsonFetch(path, { method = "GET", body } = {}) {
  const url = `${API_BASE_URL}${path}`;
  const res = await fetch(url, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });

  const text = await res.text();
  const data = text ? JSON.parse(text) : null;

  if (!res.ok) {
    const message = data?.error || `HTTP ${res.status}`;
    const err = new Error(message);
    err.status = res.status;
    err.data = data;
    throw err;
  }

  return data;
}

// this is the function that calls the backend api
export async function optimizeTours(optimizeToursRequest) {
  return await jsonFetch(ENDPOINTS.optimizeTours, {
    method: "POST",
    body: optimizeToursRequest,
  });
}

