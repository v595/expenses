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

export function loginWithGoogle(accessToken) {
  return request("/auth/google", { method: "POST", body: { accessToken } });
}

export function loginWithFacebook(accessToken) {
  return request("/auth/facebook", { method: "POST", body: { accessToken } });
}

export function loginWithFirebase(idToken) {
  return request("/auth/firebase", { method: "POST", body: { idToken } });
}

export function verifyTwoFactor(ticket, code) {
  return request("/auth/2fa/verify", { method: "POST", body: { ticket, code } });
}

export function setupTwoFactor(token) {
  return request("/auth/2fa/setup", { method: "POST", token });
}

export function enableTwoFactor(code, token) {
  return request("/auth/2fa/enable", { method: "POST", body: { code }, token });
}

export function disableTwoFactor(password, code, token) {
  return request("/auth/2fa/disable", { method: "POST", body: { password, code }, token });
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

export function getBudgetShares(category, token) {
  return request(`/budgets/${encodeURIComponent(category)}/share`, { token });
}

export function shareBudget(category, email, token) {
  return request(`/budgets/${encodeURIComponent(category)}/share`, { method: "POST", body: { email }, token });
}

export function unshareBudget(category, userId, token) {
  return request(`/budgets/${encodeURIComponent(category)}/share/${userId}`, { method: "DELETE", token });
}

export function getBudgetsSharedWithMe(token) {
  return request("/budgets/shared-with-me", { token });
}

// --- Recurring transactions ---

export function getRecurring(token) {
  return request("/recurring", { token });
}

export function createRecurring(data, token) {
  return request("/recurring", { method: "POST", body: data, token });
}

export function updateRecurring(id, data, token) {
  return request(`/recurring/${id}`, { method: "PUT", body: data, token });
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

export function updateCategory(id, data, token) {
  return request(`/categories/${id}`, { method: "PUT", body: data, token });
}

export function deleteCategory(id, token) {
  return request(`/categories/${id}`, { method: "DELETE", token });
}

// --- Debts (payoff planner) ---

export function getDebts(token) {
  return request("/debts", { token });
}

export function createDebt(data, token) {
  return request("/debts", { method: "POST", body: data, token });
}

export function updateDebt(id, data, token) {
  return request(`/debts/${id}`, { method: "PUT", body: data, token });
}

export function deleteDebt(id, token) {
  return request(`/debts/${id}`, { method: "DELETE", token });
}

export function getDebtPayoffPlan(data, token) {
  return request("/debts/payoff-plan", { method: "POST", body: data, token });
}

// --- Accounts / wallets ---

export function getAccounts(token) {
  return request("/accounts", { token });
}

export function getNetWorth(token) {
  return request("/accounts/net-worth", { token });
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

export function updateGoal(id, data, token) {
  return request(`/goals/${id}`, { method: "PUT", body: data, token });
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

export function updateBill(id, data, token) {
  return request(`/bills/${id}`, { method: "PUT", body: data, token });
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

export function getDetectedSubscriptions(token) {
  return request("/dashboard/subscriptions", { token });
}

// --- Activity ---

export function logPageView(path, token) {
  return request("/activity/pageview", { method: "POST", body: { path }, token });
}

// --- Books (ledger workspaces) ---

export function getBooks(token) {
  return request("/books", { token });
}

export function createBook(data, token) {
  return request("/books", { method: "POST", body: data, token });
}

export function updateBook(id, data, token) {
  return request(`/books/${id}`, { method: "PUT", body: data, token });
}

export function setDefaultBook(id, token) {
  return request(`/books/${id}/default`, { method: "POST", token });
}

export function deleteBook(id, token) {
  return request(`/books/${id}`, { method: "DELETE", token });
}

// --- Parties (ledger customers/suppliers) ---

export function getParties(token, { bookId, type } = {}) {
  const params = new URLSearchParams();
  if (bookId) params.append("book_id", bookId);
  if (type) params.append("type", type);
  const query = params.toString();
  return request(`/parties${query ? `?${query}` : ""}`, { token });
}

export function getParty(id, token) {
  return request(`/parties/${id}`, { token });
}

export function createParty(data, token) {
  return request("/parties", { method: "POST", body: data, token });
}

export function updateParty(id, data, token) {
  return request(`/parties/${id}`, { method: "PUT", body: data, token });
}

export function deleteParty(id, token) {
  return request(`/parties/${id}`, { method: "DELETE", token });
}

// --- Ledger entries (credit/debit lines against a party) ---

export function getLedgerEntries(partyId, token, filters = {}) {
  const params = new URLSearchParams({ party_id: partyId });
  if (filters.start_date) params.append("start_date", filters.start_date);
  if (filters.end_date) params.append("end_date", filters.end_date);
  return request(`/ledger?${params.toString()}`, { token });
}

export function createLedgerEntry(data, token) {
  return request("/ledger", { method: "POST", body: data, token });
}

export function updateLedgerEntry(id, data, token) {
  return request(`/ledger/${id}`, { method: "PUT", body: data, token });
}

export function deleteLedgerEntry(id, token) {
  return request(`/ledger/${id}`, { method: "DELETE", token });
}

// --- Payment reminders ---

export function getPendingDues(token, { bookId, overdueOnly } = {}) {
  const params = new URLSearchParams();
  if (bookId) params.append("book_id", bookId);
  if (overdueOnly) params.append("overdue_only", "true");
  const query = params.toString();
  return request(`/reminders/pending${query ? `?${query}` : ""}`, { token });
}

export function getReminders(token, { bookId, partyId } = {}) {
  const params = new URLSearchParams();
  if (bookId) params.append("book_id", bookId);
  if (partyId) params.append("party_id", partyId);
  const query = params.toString();
  return request(`/reminders${query ? `?${query}` : ""}`, { token });
}

export function createReminder(data, token) {
  return request("/reminders", { method: "POST", body: data, token });
}

export function markReminderSent(id, token) {
  return request(`/reminders/${id}/sent`, { method: "POST", token });
}

// --- Cashbook & party reports ---

export function getCashbook(token, { bookId, start_date, end_date } = {}) {
  const params = new URLSearchParams();
  if (bookId) params.append("book_id", bookId);
  if (start_date) params.append("start_date", start_date);
  if (end_date) params.append("end_date", end_date);
  const query = params.toString();
  return request(`/cashbook${query ? `?${query}` : ""}`, { token });
}

export function getPartiesSummary(token, { bookId, start_date, end_date } = {}) {
  const params = new URLSearchParams();
  if (bookId) params.append("book_id", bookId);
  if (start_date) params.append("start_date", start_date);
  if (end_date) params.append("end_date", end_date);
  const query = params.toString();
  return request(`/reports/parties/summary${query ? `?${query}` : ""}`, { token });
}

export function getPartyStatement(partyId, token, { start_date, end_date } = {}) {
  const params = new URLSearchParams();
  if (start_date) params.append("start_date", start_date);
  if (end_date) params.append("end_date", end_date);
  const query = params.toString();
  return request(`/reports/parties/${partyId}/statement${query ? `?${query}` : ""}`, { token });
}
