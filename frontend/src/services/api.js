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

// --- Recurring transactions ---

export function getRecurring(token) {
  return request("/recurring", { token });
}

export function createRecurring(data, token) {
  return request("/recurring", { method: "POST", body: data, token });
}

export function deleteRecurring(id, token) {
  return request(`/recurring/${id}`, { method: "DELETE", token });
}

// --- Transaction import ---

export function importTransactions(rows, token) {
  return request("/transactions/import", { method: "POST", body: { rows }, token });
}

// --- Settings ---

export function updateSettings(data, token) {
  return request("/settings", { method: "PUT", body: data, token });
}

export function deleteAccountPermanently(token) {
  return request("/settings/account", { method: "DELETE", token });
}

// --- Notifications ---

export function getNotifications(token) {
  return request("/notifications", { token });
}

export function getUnreadNotificationCount(token) {
  return request("/notifications/unread-count", { token });
}

export function markNotificationRead(id, token) {
  return request(`/notifications/${id}/read`, { method: "POST", token });
}

export function markAllNotificationsRead(token) {
  return request("/notifications/read-all", { method: "POST", token });
}

export function deleteNotification(id, token) {
  return request(`/notifications/${id}`, { method: "DELETE", token });
}

// --- Categories ---

export function getCategories(token) {
  return request("/categories", { token });
}

export function createCategory(data, token) {
  return request("/categories", { method: "POST", body: data, token });
}

export function deleteCategory(id, token) {
  return request(`/categories/${id}`, { method: "DELETE", token });
}

// --- Accounts / wallets ---

export function getAccounts(token) {
  return request("/accounts", { token });
}

export function createAccount(data, token) {
  return request("/accounts", { method: "POST", body: data, token });
}

export function updateAccount(id, data, token) {
  return request(`/accounts/${id}`, { method: "PUT", body: data, token });
}

export function deleteAccount(id, token) {
  return request(`/accounts/${id}`, { method: "DELETE", token });
}

// --- Goals ---

export function getGoals(token) {
  return request("/goals", { token });
}

export function createGoal(data, token) {
  return request("/goals", { method: "POST", body: data, token });
}

export function addGoalFunds(id, amount, token) {
  return request(`/goals/${id}/add-funds`, { method: "POST", body: { amount }, token });
}

export function deleteGoal(id, token) {
  return request(`/goals/${id}`, { method: "DELETE", token });
}

// --- Bills ---

export function getBills(token) {
  return request("/bills", { token });
}

export function createBill(data, token) {
  return request("/bills", { method: "POST", body: data, token });
}

export function payBill(id, token) {
  return request(`/bills/${id}/pay`, { method: "POST", token });
}

export function deleteBill(id, token) {
  return request(`/bills/${id}`, { method: "DELETE", token });
}

// --- Tags ---

export function getTags(token) {
  return request("/tags", { token });
}

export function deleteTag(id, token) {
  return request(`/tags/${id}`, { method: "DELETE", token });
}

// --- Insights ---

export function getDashboardInsights(token) {
  return request("/dashboard/insights", { token });
}

// --- Activity ---

export function logPageView(path, token) {
  return request("/activity/pageview", { method: "POST", body: { path }, token });
}
