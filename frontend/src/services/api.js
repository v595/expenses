const API_URL = import.meta.env.VITE_API_URL || "http://localhost:5000/api";

// Every API call goes through this one function. It attaches the auth token
// (if we have one), sends/parses JSON, and turns error responses into thrown
// Errors so calling code can just try/catch instead of checking .ok everywhere.
async function request(path, { method = "GET", body, token } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error(`Server returned an unreadable response (status ${response.status})`);
  }

  if (!response.ok) {
    throw new Error(data.error || "Something went wrong");
  }

  return data;
}

// --- Auth ---

export function registerUser({ name, email, password }) {
  return request("/auth/register", { method: "POST", body: { name, email, password } });
}

export function loginUser({ email, password }) {
  return request("/auth/login", { method: "POST", body: { email, password } });
}

export function getCurrentUser(token) {
  return request("/auth/me", { token });
}

export function logoutUser(token) {
  return request("/auth/logout", { method: "POST", token });
}

export function updateProfile(data, token) {
  return request("/auth/me", { method: "PUT", body: data, token });
}

// --- Transactions ---

export function getTransactions(token, filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.append(key, value);
  });
  const query = params.toString();
  return request(`/transactions${query ? `?${query}` : ""}`, { token });
}

export function getTransaction(id, token) {
  return request(`/transactions/${id}`, { token });
}

export function createTransaction(transaction, token) {
  return request("/transactions", { method: "POST", body: transaction, token });
}

export function updateTransaction(id, transaction, token) {
  return request(`/transactions/${id}`, { method: "PUT", body: transaction, token });
}

export function deleteTransaction(id, token) {
  return request(`/transactions/${id}`, { method: "DELETE", token });
}

// --- Dashboard ---

export function getDashboardSummary(token) {
  return request("/dashboard/summary", { token });
}

export function getDashboardMonthly(token) {
  return request("/dashboard/monthly", { token });
}

// --- Budgets ---

export function getBudgets(token) {
  return request("/budgets", { token });
}

export function setBudget(category, monthlyLimit, token) {
  return request("/budgets", { method: "POST", body: { category, monthly_limit: monthlyLimit }, token });
}

export function deleteBudget(category, token) {
  return request(`/budgets/${encodeURIComponent(category)}`, { method: "DELETE", token });
}
