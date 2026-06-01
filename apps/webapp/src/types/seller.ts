export type SellerProduct = {
  id: string;
  title: string;
  description: string;
  language: string;
  level?: string | null;
  category: string;
  audience?: string | null;
  price_amount: number;
  currency: string;
  product_file_id?: string | null;
  delivery_method: string;
  external_file_url?: string | null;
  status: string;
  rejection_reason?: string | null;
  preview_file_ids: string[];
  preview_urls?: string[];
  created_at: string;
  updated_at: string;
  published_at?: string | null;
};

export type SellerContactRequest = {
  id: string;
  product_id: string;
  product_title: string;
  requester_telegram_id?: number | null;
  requester_username?: string | null;
  requester_display_name?: string | null;
  message?: string | null;
  status: string;
  created_at: string;
};

export type SellerSubscriptionPlan = {
  id: string;
  code: string;
  name: string;
  description?: string | null;
  price_amount: number;
  currency: string;
  duration_days: number;
  product_limit: number;
  is_active?: boolean;
};

export type SellerSubscription = {
  subscription_id?: string | null;
  status: string;
  starts_at?: string | null;
  expires_at?: string | null;
  plan?: SellerSubscriptionPlan | null;
  product_limit: number;
  product_count: number;
  can_add_product: boolean;
};

export type SellerDashboardData = {
  products: SellerProduct[];
  contactRequests: SellerContactRequest[];
  subscription: SellerSubscription;
  stats?: SellerStats | null;
};

export type SellerStats = {
  products_by_status: Record<string, number>;
  contacts_total: number;
  contacts_new: number;
  reviews_total: number;
  average_rating?: number | null;
  views_total: number;
  views_7d: number;
};

export type SubscriptionPayment = {
  id: string;
  seller_id: string;
  subscription_id?: string | null;
  plan_id: string;
  provider: string;
  provider_payment_id?: string | null;
  payment_url?: string | null;
  amount: number;
  currency: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type SellerProfile = {
  id: string;
  user_id: string;
  display_name: string;
  bio?: string | null;
  contact_username?: string | null;
  contact_url?: string | null;
  status: string;
};

export type SellerProductUpdate = {
  title?: string;
  description?: string;
  language?: string;
  level?: string | null;
  category?: string;
  audience?: string | null;
  price_amount?: number;
  currency?: string;
  product_file_id?: string | null;
  delivery_method?: string;
  external_file_url?: string | null;
  preview_file_ids?: string[];
};
