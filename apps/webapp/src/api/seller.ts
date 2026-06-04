import type {
  SellerContactRequest,
  SellerDashboardData,
  SellerPlacementPurchaseResponse,
  SellerProfile,
  SellerProduct,
  SellerProductUpdate,
  SellerProductVisibility,
  SellerStats,
  SellerSubscription,
  SellerSubscriptionPlan,
  SubscriptionPayment,
} from "../types/seller";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

const demoProducts: SellerProduct[] = [
  {
    id: "demo-speaking-cards",
    title: "30 Speaking Cards for A2 Teens",
    description: "Картки для розмовної практики з підлітками.",
    language: "english",
    level: "a2",
    category: "speaking_cards",
    audience: "teens",
    price_amount: 14900,
    currency: "UAH",
    delivery_method: "uploaded_file",
    external_file_url: null,
    status: "published",
    preview_file_ids: [],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    published_at: new Date().toISOString(),
  },
  {
    id: "demo-new-worksheet",
    title: "Past Simple Worksheet",
    description: "Worksheet для повторення Past Simple.",
    language: "english",
    level: "a1",
    category: "worksheet",
    audience: "adults",
    price_amount: 8900,
    currency: "UAH",
    delivery_method: "private_message",
    external_file_url: null,
    status: "rejected",
    rejection_reason: "Додайте чіткіше превʼю і коротко поясніть, що входить у матеріал.",
    preview_file_ids: [],
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    published_at: null,
  },
];

const demoContactRequests: SellerContactRequest[] = [
  {
    id: "demo-request-1",
    product_id: "demo-speaking-cards",
    product_title: "30 Speaking Cards for A2 Teens",
    requester_telegram_id: 123456,
    requester_username: "teacher_anna",
    requester_display_name: "@teacher_anna",
    message: "Хочу придбати набір для групи підлітків.",
    status: "new",
    created_at: new Date().toISOString(),
  },
];

export const demoSubscriptionPlans: SellerSubscriptionPlan[] = [
  {
    id: "demo-free-plan",
    code: "free",
    name: "Free",
    description: "До 3 матеріалів для старту.",
    price_amount: 0,
    currency: "UAH",
    duration_days: 3650,
    product_limit: 3,
  },
  {
    id: "demo-pro-monthly",
    code: "pro_monthly",
    name: "Pro щомісяця",
    description: "До 50 матеріалів у каталозі.",
    price_amount: 20000,
    currency: "UAH",
    duration_days: 30,
    product_limit: 50,
  },
  {
    id: "demo-pro-yearly",
    code: "pro_yearly",
    name: "Pro на рік",
    description: "Річний доступ для активних авторів.",
    price_amount: 200000,
    currency: "UAH",
    duration_days: 365,
    product_limit: 50,
  },
];

export const demoSellerDashboard: SellerDashboardData = {
  products: demoProducts,
  contactRequests: demoContactRequests,
  subscription: {
    subscription_id: null,
    status: "free",
    starts_at: null,
    expires_at: null,
    plan: null,
    product_limit: 3,
    product_count: 1,
    can_add_product: true,
  },
  stats: {
    products_by_status: { published: 1, rejected: 1 },
    contacts_total: 1,
    contacts_new: 1,
    reviews_total: 0,
    average_rating: null,
    views_total: 0,
    views_7d: 0,
  },
};

function authHeaders(accessToken: string) {
  return { Authorization: `Bearer ${accessToken}` };
}

export async function fetchSellerProducts(accessToken: string): Promise<SellerProduct[]> {
  const response = await fetch(`${API_BASE_URL}/seller/products`, {
    headers: authHeaders(accessToken),
  });
  if (!response.ok) {
    throw new Error("Не вдалося завантажити матеріали автора.");
  }
  return response.json();
}

export async function fetchSellerContactRequests(accessToken: string): Promise<SellerContactRequest[]> {
  const response = await fetch(`${API_BASE_URL}/seller/contact-requests`, {
    headers: authHeaders(accessToken),
  });
  if (!response.ok) {
    throw new Error("Не вдалося завантажити звернення.");
  }
  return response.json();
}

export async function fetchSellerSubscription(accessToken: string): Promise<SellerSubscription> {
  const response = await fetch(`${API_BASE_URL}/seller/subscription`, {
    headers: authHeaders(accessToken),
  });
  if (!response.ok) {
    throw new Error("Не вдалося завантажити підписку.");
  }
  return response.json();
}

export async function fetchSellerStats(accessToken: string): Promise<SellerStats> {
  const response = await fetch(`${API_BASE_URL}/seller/stats`, {
    headers: authHeaders(accessToken),
  });
  if (!response.ok) {
    throw new Error("Не вдалося завантажити статистику автора.");
  }
  return response.json();
}

export async function fetchSellerProfile(accessToken: string): Promise<SellerProfile | null> {
  const response = await fetch(`${API_BASE_URL}/seller/profile`, {
    headers: authHeaders(accessToken),
  });
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error("Не вдалося завантажити профіль автора.");
  }
  return response.json();
}

export async function fetchSellerDashboard(accessToken: string): Promise<SellerDashboardData> {
  const [products, contactRequests, subscription, stats] = await Promise.all([
    fetchSellerProducts(accessToken),
    fetchSellerContactRequests(accessToken),
    fetchSellerSubscription(accessToken),
    fetchSellerStats(accessToken),
  ]);
  return { products, contactRequests, subscription, stats };
}

export async function updateSellerProduct(
  productId: string,
  payload: SellerProductUpdate,
  accessToken: string,
): Promise<SellerProduct> {
  const response = await fetch(`${API_BASE_URL}/products/${productId}`, {
    method: "PATCH",
    headers: {
      ...authHeaders(accessToken),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Не вдалося оновити матеріал.");
  }
  return response.json();
}

export async function submitSellerProduct(productId: string, accessToken: string): Promise<SellerProduct> {
  const response = await fetch(`${API_BASE_URL}/products/${productId}/submit`, {
    method: "POST",
    headers: authHeaders(accessToken),
  });
  if (!response.ok) {
    throw new Error("Не вдалося відправити матеріал на модерацію.");
  }
  return response.json();
}

export async function deleteSellerProduct(productId: string, accessToken: string): Promise<SellerProduct> {
  const response = await fetch(`${API_BASE_URL}/products/${productId}`, {
    method: "DELETE",
    headers: authHeaders(accessToken),
  });
  if (!response.ok) {
    throw new Error("Не вдалося видалити матеріал.");
  }
  return response.json();
}

export async function fetchSellerProductVisibility(
  productId: string,
  accessToken: string,
): Promise<SellerProductVisibility> {
  const response = await fetch(`${API_BASE_URL}/seller/products/${productId}/visibility`, {
    headers: authHeaders(accessToken),
  });
  if (!response.ok) {
    throw new Error("Не вдалося завантажити видимість матеріалу.");
  }
  return response.json();
}

export async function buySellerProductPlacement(
  productId: string,
  accessToken: string,
): Promise<SellerPlacementPurchaseResponse> {
  const response = await fetch(`${API_BASE_URL}/seller/products/${productId}/buy-placement`, {
    method: "POST",
    headers: authHeaders(accessToken),
  });
  if (!response.ok) {
    throw new Error("Не вдалося оформити разове розміщення.");
  }
  return response.json();
}

export async function uploadSellerFile(
  file: File,
  fileKind: "product_file" | "preview_image",
  accessToken: string,
): Promise<{ id: string }> {
  const formData = new FormData();
  formData.set("file_kind", fileKind);
  formData.set("file", file);
  const response = await fetch(`${API_BASE_URL}/files/upload`, {
    method: "POST",
    headers: authHeaders(accessToken),
    body: formData,
  });
  if (!response.ok) {
    throw new Error("Не вдалося завантажити файл.");
  }
  return response.json();
}

export async function updateSellerProfile(
  payload: Pick<SellerProfile, "display_name" | "bio" | "contact_username">,
  accessToken: string,
): Promise<SellerProfile> {
  const response = await fetch(`${API_BASE_URL}/seller/profile`, {
    method: "PATCH",
    headers: {
      ...authHeaders(accessToken),
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Не вдалося оновити профіль.");
  }
  return response.json();
}

export async function updateContactRequestStatus(
  requestId: string,
  status: "new" | "handled" | "archived",
  accessToken: string,
): Promise<SellerContactRequest> {
  const response = await fetch(`${API_BASE_URL}/seller/contact-requests/${requestId}`, {
    method: "PATCH",
    headers: {
      ...authHeaders(accessToken),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ status }),
  });
  if (!response.ok) {
    throw new Error("Не вдалося оновити звернення.");
  }
  return response.json();
}

export async function fetchSubscriptionPlans(): Promise<SellerSubscriptionPlan[]> {
  const response = await fetch(`${API_BASE_URL}/subscription-plans`);
  if (!response.ok) {
    throw new Error("Не вдалося завантажити тарифи.");
  }
  return response.json();
}

export async function createSubscriptionCheckout(
  planId: string,
  accessToken: string,
): Promise<SubscriptionPayment> {
  const response = await fetch(`${API_BASE_URL}/seller/subscription/checkout`, {
    method: "POST",
    headers: {
      ...authHeaders(accessToken),
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ plan_id: planId }),
  });
  if (!response.ok) {
    throw new Error("Не вдалося створити оплату.");
  }
  return response.json();
}

export async function markMockPaymentPaid(paymentId: string, accessToken: string): Promise<SubscriptionPayment> {
  const response = await fetch(`${API_BASE_URL}/subscription-payments/mock/${paymentId}/mark-paid`, {
    method: "POST",
    headers: authHeaders(accessToken),
  });
  if (!response.ok) {
    throw new Error("Не вдалося підтвердити mock-оплату.");
  }
  return response.json();
}
