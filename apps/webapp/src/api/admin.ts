const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function authHeaders(accessToken: string) {
  return { Authorization: `Bearer ${accessToken}` };
}

export type AdminProduct = {
  id: string;
  title: string;
  description: string;
  status: string;
  price_amount: number;
  currency: string;
  seller: {
    id: string;
    user_id?: string;
    display_name: string;
    contact_username?: string | null;
    status?: string | null;
    user_is_blocked?: boolean | null;
  };
};

export type AdminProductsResponse = {
  items: AdminProduct[];
  page: number;
  limit: number;
  total: number;
};

export type AdminSubscriptionPlan = {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  price_amount: number;
  currency: string;
  product_limit: number;
  duration_days: number;
  is_active: boolean;
};

export type AdminReport = {
  id: string;
  product_id: string;
  product_title: string;
  reporter_id: string;
  reason: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export async function fetchAdminProducts(accessToken: string, status = "pending_moderation"): Promise<AdminProductsResponse> {
  const response = await fetch(`${API_BASE_URL}/admin/products?status=${encodeURIComponent(status)}`, {
    headers: authHeaders(accessToken),
  });
  if (!response.ok) {
    throw new Error("Не вдалося завантажити матеріали.");
  }
  return response.json();
}

export async function adminApproveProduct(productId: string, accessToken: string): Promise<AdminProduct> {
  const response = await fetch(`${API_BASE_URL}/admin/products/${productId}/approve`, { method: "POST", headers: authHeaders(accessToken) });
  if (!response.ok) throw new Error("Не вдалося опублікувати.");
  return response.json();
}

export async function adminHideProduct(productId: string, accessToken: string): Promise<AdminProduct> {
  const response = await fetch(`${API_BASE_URL}/admin/products/${productId}/hide`, { method: "POST", headers: authHeaders(accessToken) });
  if (!response.ok) throw new Error("Не вдалося сховати.");
  return response.json();
}

export async function adminRestoreProduct(productId: string, accessToken: string): Promise<AdminProduct> {
  const response = await fetch(`${API_BASE_URL}/admin/products/${productId}/restore`, { method: "POST", headers: authHeaders(accessToken) });
  if (!response.ok) throw new Error("Не вдалося відновити.");
  return response.json();
}

export async function adminBulkHideProducts(productIds: string[], accessToken: string): Promise<AdminProduct[]> {
  const response = await fetch(`${API_BASE_URL}/admin/products/bulk-hide`, {
    method: "POST",
    headers: { ...authHeaders(accessToken), "Content-Type": "application/json" },
    body: JSON.stringify({ product_ids: productIds }),
  });
  if (!response.ok) throw new Error("Не вдалося сховати вибрані матеріали.");
  return response.json();
}

export async function adminBulkRestoreProducts(productIds: string[], accessToken: string): Promise<AdminProduct[]> {
  const response = await fetch(`${API_BASE_URL}/admin/products/bulk-restore`, {
    method: "POST",
    headers: { ...authHeaders(accessToken), "Content-Type": "application/json" },
    body: JSON.stringify({ product_ids: productIds }),
  });
  if (!response.ok) throw new Error("Не вдалося відновити вибрані матеріали.");
  return response.json();
}

export async function fetchAdminPlans(accessToken: string): Promise<AdminSubscriptionPlan[]> {
  const response = await fetch(`${API_BASE_URL}/admin/subscription-plans?include_inactive=true`, {
    headers: authHeaders(accessToken),
  });
  if (!response.ok) throw new Error("Не вдалося завантажити тарифи.");
  return response.json();
}

export async function saveAdminPlan(
  accessToken: string,
  payload: Partial<AdminSubscriptionPlan>,
  planId?: string,
): Promise<AdminSubscriptionPlan> {
  const response = await fetch(`${API_BASE_URL}/admin/subscription-plans${planId ? `/${planId}` : ""}`, {
    method: planId ? "PATCH" : "POST",
    headers: { ...authHeaders(accessToken), "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error("Не вдалося зберегти тариф.");
  return response.json();
}

export async function deactivateAdminPlan(planId: string, accessToken: string): Promise<AdminSubscriptionPlan> {
  const response = await fetch(`${API_BASE_URL}/admin/subscription-plans/${planId}`, { method: "DELETE", headers: authHeaders(accessToken) });
  if (!response.ok) throw new Error("Не вдалося деактивувати тариф.");
  return response.json();
}

export async function fetchAdminReports(accessToken: string): Promise<AdminReport[]> {
  const response = await fetch(`${API_BASE_URL}/admin/reports?status=open`, { headers: authHeaders(accessToken) });
  if (!response.ok) throw new Error("Не вдалося завантажити скарги.");
  return response.json();
}

export async function resolveAdminReport(reportId: string, accessToken: string): Promise<AdminReport> {
  const response = await fetch(`${API_BASE_URL}/admin/reports/${reportId}/resolve`, { method: "POST", headers: authHeaders(accessToken) });
  if (!response.ok) throw new Error("Не вдалося закрити скаргу.");
  return response.json();
}

export async function updateAdminSellerStatus(sellerId: string, status: "active" | "suspended", accessToken: string) {
  const response = await fetch(`${API_BASE_URL}/admin/sellers/${sellerId}/status`, {
    method: "PATCH",
    headers: { ...authHeaders(accessToken), "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!response.ok) throw new Error("Не вдалося оновити автора.");
  return response.json();
}

export async function updateAdminUserBlocked(userId: string, isBlocked: boolean, accessToken: string) {
  const response = await fetch(`${API_BASE_URL}/admin/users/${userId}/blocked`, {
    method: "PATCH",
    headers: { ...authHeaders(accessToken), "Content-Type": "application/json" },
    body: JSON.stringify({ is_blocked: isBlocked }),
  });
  if (!response.ok) throw new Error("Не вдалося оновити користувача.");
  return response.json();
}
