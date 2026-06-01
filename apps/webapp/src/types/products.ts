export type CatalogSeller = {
  id: string;
  display_name: string;
  bio?: string | null;
  contact_username?: string | null;
};

export type CatalogProductListItem = {
  id: string;
  title: string;
  language: string;
  level?: string | null;
  category: string;
  audience?: string | null;
  price_amount: number;
  currency: string;
  preview_file_id?: string | null;
  preview_url?: string | null;
  delivery_method: string;
  created_at: string;
  published_at?: string | null;
  is_favorite?: boolean;
  seller: CatalogSeller;
};

export type CatalogProductDetail = CatalogProductListItem & {
  description: string;
  preview_file_ids: string[];
  preview_urls?: string[];
  is_favorite: boolean;
};

export type CatalogProductsResponse = {
  items: CatalogProductListItem[];
  page: number;
  limit: number;
  total: number;
};

export type CatalogFilters = {
  search: string;
  language: string;
  level: string;
  category: string;
  audience: string;
  min_price: string;
  max_price: string;
  sort: string;
  page: string;
};

export type ContactRequestResponse = {
  id: string;
  product_id: string;
  seller_id: string;
  seller_telegram_url: string;
  status: string;
  created_at: string;
};

export type ProductReview = {
  id: string;
  product_id: string;
  buyer_id: string;
  buyer_display_name?: string | null;
  rating: number;
  text?: string | null;
  created_at: string;
};

export type ProductReviewsResponse = {
  items: ProductReview[];
  average_rating?: number | null;
  total: number;
};

export type ProductReportResponse = {
  id: string;
  product_id: string;
  reporter_id: string;
  reason: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type RecentlyViewedProduct = {
  id: string;
  title: string;
  category: string;
  price_amount: number;
  currency: string;
  preview_url?: string | null;
  seller: CatalogSeller;
  viewed_at: string;
};
