import type {
  CatalogFilters,
  CatalogProductDetail,
  CatalogProductListItem,
  CatalogProductsResponse,
  ContactRequestResponse,
  ProductReportResponse,
  ProductReview,
  ProductReviewsResponse,
} from "../types/products";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const demoProducts: CatalogProductsResponse = {
  items: [
    {
      id: "demo-speaking-cards",
      title: "30 Speaking Cards for A2 Teens",
      language: "english",
      level: "a2",
      category: "speaking_cards",
      audience: "teens",
      price_amount: 14900,
      currency: "UAH",
      preview_file_id: null,
      delivery_method: "uploaded_file",
      created_at: "2026-05-15T10:30:00Z",
      published_at: "2026-05-16T08:00:00Z",
      seller: {
        id: "seller-maria",
        display_name: "Марія",
        bio: "Викладачка англійської, створюю speaking activities для підлітків.",
        contact_username: "maria_teacher",
      },
    },
    {
      id: "demo-present-perfect",
      title: "Present Perfect Test B1",
      language: "english",
      level: "b1",
      category: "test",
      audience: "teens",
      price_amount: 9900,
      currency: "UAH",
      preview_file_id: null,
      delivery_method: "private_message",
      created_at: "2026-05-12T14:20:00Z",
      published_at: "2026-05-13T09:00:00Z",
      seller: {
        id: "seller-olena",
        display_name: "Олена",
        bio: "Авторка тестів і worksheets для індивідуальних занять.",
        contact_username: "olena_teacher",
      },
    },
    {
      id: "demo-business-phrases",
      title: "Business English Meeting Phrases",
      language: "english",
      level: "b2",
      category: "worksheet",
      audience: "business",
      price_amount: 17900,
      currency: "UAH",
      preview_file_id: null,
      delivery_method: "external_link",
      created_at: "2026-05-10T11:00:00Z",
      published_at: "2026-05-11T10:00:00Z",
      seller: {
        id: "seller-ira",
        display_name: "Ірина",
        bio: "Готую матеріали для business English і корпоративних груп.",
        contact_username: "ira_business_english",
      },
    },
  ],
  page: 1,
  limit: 20,
  total: 3,
};

export function formatPrice(priceAmount: number, currency: string) {
  return `${Math.round(priceAmount / 100)} ${currency === "UAH" ? "грн" : currency}`;
}

export async function fetchProducts(filters: CatalogFilters): Promise<CatalogProductsResponse> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) {
      params.set(key, key === "min_price" || key === "max_price" ? String(Number(value) * 100) : value);
    }
  });
  params.set("page", filters.page || "1");
  params.set("limit", "20");

  const response = await fetch(`${API_BASE_URL}/products?${params.toString()}`);
  if (!response.ok) {
    throw new Error("Не вдалося завантажити каталог.");
  }
  return response.json();
}

export async function fetchProduct(productId: string): Promise<CatalogProductDetail> {
  if (productId.startsWith("demo-")) {
    return demoProductDetail(productId);
  }

  const response = await fetch(`${API_BASE_URL}/products/${productId}`);
  if (!response.ok) {
    throw new Error("Не вдалося завантажити матеріал.");
  }
  return response.json();
}

export async function fetchFavorites(accessToken: string): Promise<CatalogProductListItem[]> {
  const response = await fetch(`${API_BASE_URL}/favorites`, {
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!response.ok) {
    throw new Error("Не вдалося завантажити збережене.");
  }
  return response.json();
}

export async function addFavorite(productId: string, accessToken: string) {
  const response = await fetch(`${API_BASE_URL}/products/${productId}/favorite`, {
    method: "POST",
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!response.ok) {
    throw new Error("Не вдалося зберегти матеріал.");
  }
}

export async function removeFavorite(productId: string, accessToken: string) {
  const response = await fetch(`${API_BASE_URL}/products/${productId}/favorite`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!response.ok) {
    throw new Error("Не вдалося прибрати матеріал зі збереженого.");
  }
}

export async function createContactRequest(
  productId: string,
  accessToken: string,
  message?: string,
): Promise<ContactRequestResponse> {
  const response = await fetch(`${API_BASE_URL}/products/${productId}/contact-request`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message: message || null }),
  });
  if (!response.ok) {
    throw new Error("Не вдалося створити звернення.");
  }
  return response.json();
}

export async function fetchProductReviews(productId: string): Promise<ProductReviewsResponse> {
  if (productId.startsWith("demo-")) {
    return { items: [], average_rating: null, total: 0 };
  }
  const response = await fetch(`${API_BASE_URL}/products/${productId}/reviews`);
  if (!response.ok) {
    throw new Error("Не вдалося завантажити відгуки.");
  }
  return response.json();
}

export async function createProductReview(
  productId: string,
  accessToken: string,
  rating: number,
  text?: string,
) {
  const response = await fetch(`${API_BASE_URL}/products/${productId}/reviews`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ rating, text: text || null }),
  });
  if (!response.ok) {
    throw new Error("Не вдалося зберегти відгук.");
  }
  return response.json();
}

export async function updateProductReview(
  reviewId: string,
  accessToken: string,
  rating: number,
  text?: string,
): Promise<ProductReview> {
  const response = await fetch(`${API_BASE_URL}/reviews/${reviewId}`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ rating, text: text || null }),
  });
  if (!response.ok) {
    throw new Error("Не вдалося оновити відгук.");
  }
  return response.json();
}

export async function deleteProductReview(reviewId: string, accessToken: string) {
  const response = await fetch(`${API_BASE_URL}/reviews/${reviewId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${accessToken}` },
  });
  if (!response.ok) {
    throw new Error("Не вдалося видалити відгук.");
  }
}

export async function trackProductView(productId: string, accessToken?: string | null): Promise<{ tracked: boolean }> {
  if (productId.startsWith("demo-")) {
    return { tracked: false };
  }
  const response = await fetch(`${API_BASE_URL}/products/${productId}/view`, {
    method: "POST",
    headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : undefined,
  });
  if (!response.ok) {
    throw new Error("Не вдалося зафіксувати перегляд.");
  }
  return response.json();
}

export async function reportProduct(
  productId: string,
  accessToken: string,
  reason: string,
): Promise<ProductReportResponse> {
  const response = await fetch(`${API_BASE_URL}/products/${productId}/report`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ reason }),
  });
  if (!response.ok) {
    throw new Error("Не вдалося надіслати скаргу.");
  }
  return response.json();
}

export function demoProductDetail(productId: string): CatalogProductDetail {
  const product = demoProducts.items.find((item) => item.id === productId) ?? demoProducts.items[0];
  return {
    ...product,
    description:
      "Готовий матеріал для уроку з чіткою структурою, превʼю для швидкої оцінки та контактами автора для прямої покупки.",
    preview_file_ids: [],
    is_favorite: false,
  };
}
