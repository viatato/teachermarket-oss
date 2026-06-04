import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Bookmark,
  Inbox,
  LayoutGrid,
  MessageCircle,
  PackagePlus,
  Pencil,
  Search,
  Send,
  ShieldCheck,
  Sparkles,
  Store,
  Trash2,
} from "lucide-react";

import {
  adminApproveProduct,
  adminBulkHideProducts,
  adminBulkRestoreProducts,
  adminHideProduct,
  adminRestoreProduct,
  deactivateAdminPlan,
  fetchAdminPlans,
  fetchAdminProducts,
  fetchAdminReports,
  resolveAdminReport,
  saveAdminPlan,
  updateAdminSellerStatus,
  updateAdminUserBlocked,
  type AdminSubscriptionPlan,
} from "../api/admin";
import {
  buySellerProductPlacement,
  createSubscriptionCheckout,
  demoSellerDashboard,
  demoSubscriptionPlans,
  fetchSellerDashboard,
  fetchSellerProductVisibility,
  fetchSellerProfile,
  fetchSubscriptionPlans,
  deleteSellerProduct,
  markMockPaymentPaid,
  submitSellerProduct,
  updateContactRequestStatus,
  updateSellerProduct,
  updateSellerProfile,
  uploadSellerFile,
} from "../api/seller";
import { formatPrice } from "../api/products";
import { getCategoryLabel, getLanguageLabel, getLevelLabel } from "../components/ProductCard";
import type { RecentlyViewedProduct } from "../types/products";
import type { SellerDashboardData, SellerProduct, SellerProductUpdate, SellerProfile, SellerSubscriptionPlan } from "../types/seller";

type SellerDashboardPageProps = {
  accessToken?: string | null;
  isAdmin: boolean;
  activeScreen: "profile" | SellerScreen;
  favoriteCount: number;
  onOpenCatalog: () => void;
  onOpenFavorites: () => void;
  onOpenProduct: (productId: string) => void;
  onNavigate: (screen: "profile" | SellerScreen) => void;
};

export type SellerScreen = "seller" | "seller-products" | "seller-requests" | "seller-subscription" | "recently-viewed" | "admin";

const BOT_URL = import.meta.env.VITE_TELEGRAM_BOT_URL ?? "https://t.me/TeacherMarket_Bot";

const statusLabels: Record<string, string> = {
  draft: "Чернетка",
  pending_moderation: "На модерації",
  published: "Опубліковано",
  rejected: "Потрібні правки",
  hidden: "Приховано",
  deleted: "Видалено",
  handled: "Оброблено",
  archived: "Архів",
  free: "Безкоштовний",
  active: "Активна",
  suspended: "Призупинено",
  trial: "Пробний період",
};

const visibilityLabels: Record<string, { label: string; tone: "visible" | "hidden" }> = {
  paid_subscription: { label: "Видно за підпискою", tone: "visible" },
  subscription_grace: { label: "Видно в грейс-період", tone: "visible" },
  one_time_placement: { label: "Видно за разовим розміщенням", tone: "visible" },
  free_tier: { label: "Видно у free-ліміті", tone: "visible" },
  not_published: { label: "Не видно: не опубліковано", tone: "hidden" },
  hidden_after_grace: { label: "Не видно після грейс-періоду", tone: "hidden" },
};

const serviceRules = [
  "Розміщуйте тільки власні матеріали або матеріали, на які маєте права.",
  "Превʼю має чесно показувати зміст матеріалу.",
  "Покупець пише автору напряму в Telegram; ТічерМаркет не проводить оплату матеріалу і не робить виплати авторам.",
  "Підписка автора оплачує розміщення й роботу з сервісом, а не продаж конкретного матеріалу.",
];

function formatDate(value: string) {
  return new Date(value).toLocaleDateString("uk-UA");
}

export function SellerDashboardPage({
  accessToken,
  isAdmin,
  activeScreen,
  favoriteCount,
  onOpenCatalog,
  onOpenFavorites,
  onOpenProduct,
  onNavigate,
}: SellerDashboardPageProps) {
  const queryClient = useQueryClient();
  const [checkoutNotice, setCheckoutNotice] = useState<string | null>(null);
  const [profileNotice, setProfileNotice] = useState<string | null>(null);
  const query = useQuery({
    queryKey: ["seller-dashboard", accessToken],
    queryFn: () => fetchSellerDashboard(accessToken || ""),
    enabled: Boolean(accessToken),
    retry: false,
  });
  const plansQuery = useQuery({
    queryKey: ["subscription-plans"],
    queryFn: fetchSubscriptionPlans,
    retry: false,
  });
  const profileQuery = useQuery({
    queryKey: ["seller-profile", accessToken],
    queryFn: () => fetchSellerProfile(accessToken || ""),
    enabled: Boolean(accessToken),
    retry: false,
  });
  const profileMutation = useMutation({
    mutationFn: (payload: { display_name: string; bio?: string | null; contact_username?: string | null }) => {
      if (!accessToken) throw new Error("Потрібна авторизація.");
      return updateSellerProfile(payload, accessToken);
    },
    onSuccess: async () => {
      setProfileNotice("Профіль оновлено.");
      await queryClient.invalidateQueries({ queryKey: ["seller-profile", accessToken] });
      window.setTimeout(() => setProfileNotice(null), 3500);
    },
  });
  const checkoutMutation = useMutation({
    mutationFn: async (planId: string) => {
      if (!accessToken) {
        throw new Error("Потрібна авторизація.");
      }
      const payment = await createSubscriptionCheckout(planId, accessToken);
      if (!isAdmin) {
        if (payment.payment_url) {
          window.open(payment.payment_url, "_blank", "noopener,noreferrer");
        }
        return { payment, markedPaid: false };
      }
      return { payment: await markMockPaymentPaid(payment.id, accessToken), markedPaid: true };
    },
    onMutate: () => {
      setCheckoutNotice(null);
    },
    onSuccess: async () => {
      setCheckoutNotice(
        isAdmin
          ? "Mock-оплату підтверджено, підписку активовано."
          : "Mock-оплату створено. У закритому тесті її підтверджує адмін, реальні списання не проводяться.",
      );
      await queryClient.invalidateQueries({ queryKey: ["seller-dashboard", accessToken] });
    },
  });

  const data = query.data ?? demoSellerDashboard;
  const isDemo = !accessToken || query.isError;
  const plans = plansQuery.data ?? demoSubscriptionPlans;
  const canAddProduct = data.subscription.can_add_product;

  return (
    <main id="main-content" className="app-shell" tabIndex={-1}>
      {query.isLoading ? <p className="notice">Завантажуємо кабінет автора...</p> : null}
      {isDemo && activeScreen !== "profile" ? (
        <div className="demo-banner">
          <span>Демо-режим</span>
          <p>Показано демо-дані. Після входу через Telegram тут будуть ваші реальні дані.</p>
        </div>
      ) : null}

      {activeScreen === "profile" ? (
        <ProfileHome
          favoriteCount={favoriteCount}
          isAdmin={isAdmin}
          onOpenCatalog={onOpenCatalog}
          onOpenFavorites={onOpenFavorites}
          onOpenSeller={() => onNavigate("seller")}
          onOpenSellerProducts={() => onNavigate("seller-products")}
          onOpenRecently={() => onNavigate("recently-viewed")}
          onOpenAdmin={() => onNavigate("admin")}
        />
      ) : null}
      {activeScreen === "seller" ? (
        <SellerHome data={data} canAddProduct={canAddProduct} isAdmin={isAdmin} onNavigate={onNavigate} />
      ) : null}
      {activeScreen === "seller-products" ? (
        <SellerProducts products={data.products} canAddProduct={canAddProduct} accessToken={accessToken} botUrl={BOT_URL} onBack={() => onNavigate("seller")} />
      ) : null}
      {activeScreen === "seller-requests" ? <ContactRequests data={data} accessToken={accessToken} onBack={() => onNavigate("seller")} /> : null}
      {activeScreen === "seller-subscription" ? (
        <Subscription
          data={data}
          plans={plans}
          hasAccessToken={Boolean(accessToken)}
          isAdmin={isAdmin}
          isProcessing={checkoutMutation.isPending}
          onBack={() => onNavigate("seller")}
          onChoosePlan={(planId) => checkoutMutation.mutate(planId)}
        />
      ) : null}
      {activeScreen === "recently-viewed" ? (
        <RecentlyViewed onBack={() => onNavigate("profile")} onOpenProduct={onOpenProduct} />
      ) : null}
      {activeScreen === "admin" ? (
        <AdminPanel accessToken={accessToken} onBack={() => onNavigate("seller")} />
      ) : null}
      {profileQuery.data ? (
        <ProfileEditor
          profile={profileQuery.data}
          isSaving={profileMutation.isPending}
          onSave={(payload) => profileMutation.mutate(payload)}
        />
      ) : null}

      {checkoutMutation.isError ? <p className="notice">Не вдалося провести mock-оплату. Спробуйте ще раз.</p> : null}
      {checkoutNotice ? <p className="success-message">{checkoutNotice}</p> : null}
      {profileNotice ? <p className="success-message">{profileNotice}</p> : null}
    </main>
  );
}

function SellerHome({
  data,
  canAddProduct,
  isAdmin,
  onNavigate,
}: {
  data: SellerDashboardData;
  canAddProduct: boolean;
  isAdmin: boolean;
  onNavigate: (screen: "profile" | SellerScreen) => void;
}) {
  const publishedCount = data.products.filter((product) => product.status === "published").length;
  const stats = data.stats;
  return (
    <>
      <section className="page-header seller-header">
        <div>
          <button type="button" className="text-button back-link" onClick={() => onNavigate("profile")}>
            <ArrowLeft aria-hidden="true" size={17} />
            Мій профіль
          </button>
          <p className="eyebrow">Кабінет автора</p>
          <h1>Авторський кабінет</h1>
          <p className="lead">Матеріали, звернення покупців і підписка на розміщення в сервісі.</p>
        </div>
        {canAddProduct ? (
          <a className="primary-link-button" href={BOT_URL} target="_blank" rel="noreferrer">
            <PackagePlus aria-hidden="true" size={18} />
            Додати матеріал
          </a>
        ) : (
          <button className="primary-link-button is-disabled" type="button" disabled>
            Ліміт вичерпано
          </button>
        )}
      </section>

      <ServiceRulesPanel />

      <section className="stats-row">
        <StatTile label="Матеріали" value={data.products.length} />
        <StatTile label="Опубліковано" value={publishedCount} />
        <StatTile label="Нові звернення" value={stats?.contacts_new ?? data.contactRequests.filter((request) => request.status === "new").length} />
        <StatTile label="Ліміт" value={`${data.subscription.product_count}/${data.subscription.product_limit}`} />
        <StatTile label="Перегляди 7 днів" value={stats?.views_7d ?? 0} />
        <StatTile label="Відгуки" value={stats?.reviews_total ?? 0} />
        <StatTile label="Рейтинг" value={stats?.average_rating ? stats.average_rating.toFixed(1) : "—"} />
      </section>

      <section className="seller-menu" aria-label="Розділи профілю автора">
        <SellerMenuButton
          icon={<LayoutGrid aria-hidden="true" size={22} />}
          title="Мої матеріали"
          description="Статуси, ціни та матеріали на модерації."
          onClick={() => onNavigate("seller-products")}
        />
        <SellerMenuButton
          icon={<MessageCircle aria-hidden="true" size={22} />}
          title="Звернення"
          description={`${data.contactRequests.length} покупців чекають відповіді або історії звернень.`}
          onClick={() => onNavigate("seller-requests")}
        />
        <SellerMenuButton
          icon={<Sparkles aria-hidden="true" size={22} />}
          title="Підписка"
          description="Ліміт матеріалів, поточний план і тестова mock-оплата."
          onClick={() => onNavigate("seller-subscription")}
        />
        {isAdmin ? (
          <SellerMenuButton
            icon={<ShieldCheck aria-hidden="true" size={22} />}
            title="Адмін-панель"
            description="Правки від адміна: модерація, тарифи, скарги й керування авторами."
            onClick={() => onNavigate("admin")}
          />
        ) : null}
      </section>
    </>
  );
}

function ProfileHome({
  favoriteCount,
  isAdmin,
  onOpenCatalog,
  onOpenFavorites,
  onOpenSeller,
  onOpenSellerProducts,
  onOpenRecently,
  onOpenAdmin,
}: {
  favoriteCount: number;
  isAdmin: boolean;
  onOpenCatalog: () => void;
  onOpenFavorites: () => void;
  onOpenSeller: () => void;
  onOpenSellerProducts: () => void;
  onOpenRecently: () => void;
  onOpenAdmin: () => void;
}) {
  const [recentItems, setRecentItems] = useState<RecentlyViewedProduct[]>([]);
  useEffect(() => {
    setRecentItems(readRecentlyViewed());
  }, []);
  return (
    <>
      <section className="page-header profile-header">
        <p className="eyebrow">Мій профіль</p>
        <h1>Ваш простір</h1>
        <p className="lead">Швидкий доступ до збережених матеріалів і авторського кабінету.</p>
      </section>

      <section className="profile-actions" aria-label="Дії профілю">
        <button type="button" className="profile-action-card" onClick={onOpenFavorites}>
          <span className="seller-menu-icon">
            <Bookmark aria-hidden="true" size={22} />
          </span>
          <span>
            <strong>Збережене</strong>
            <small>{favoriteCount > 0 ? `${favoriteCount} матеріалів для перегляду пізніше` : "Матеріали, які ви збережете, будуть тут."}</small>
          </span>
          <ArrowRight aria-hidden="true" size={20} />
        </button>
        <button type="button" className="profile-action-card" onClick={onOpenCatalog}>
          <span className="seller-menu-icon">
            <Search aria-hidden="true" size={22} />
          </span>
          <span>
            <strong>Знайти матеріали</strong>
            <small>Повернутися в каталог і підібрати матеріал до уроку.</small>
          </span>
          <ArrowRight aria-hidden="true" size={20} />
        </button>
        <button type="button" className="profile-action-card" onClick={onOpenRecently}>
          <span className="seller-menu-icon">
            <Inbox aria-hidden="true" size={22} />
          </span>
          <span>
            <strong>Нещодавно переглянуті</strong>
            <small>{recentItems.length > 0 ? `${recentItems.length} матеріалів у локальній історії` : "Історія переглядів зʼявиться після відкриття матеріалів."}</small>
          </span>
          <ArrowRight aria-hidden="true" size={20} />
        </button>
        <button type="button" className="profile-action-card author-card" onClick={onOpenSeller}>
          <span className="seller-menu-icon">
            <Store aria-hidden="true" size={22} />
          </span>
          <span>
            <strong>Кабінет автора</strong>
            <small>Додавайте матеріали, дивіться звернення та керуйте підпискою.</small>
          </span>
          <ArrowRight aria-hidden="true" size={20} />
        </button>
        <button type="button" className="profile-action-card manage-card" onClick={onOpenSellerProducts}>
          <span className="seller-menu-icon">
            <Pencil aria-hidden="true" size={22} />
          </span>
          <span>
            <strong>Керувати матеріалами</strong>
            <small>Редагування, повторна відправка на модерацію та видалення ваших матеріалів.</small>
          </span>
          <ArrowRight aria-hidden="true" size={20} />
        </button>
        {isAdmin ? (
          <button type="button" className="profile-action-card admin-card" onClick={onOpenAdmin}>
            <span className="seller-menu-icon">
              <ShieldCheck aria-hidden="true" size={22} />
            </span>
            <span>
              <strong>Адмін-панель</strong>
              <small>Правки від адміна: модерація матеріалів, тарифи, скарги й автори.</small>
            </span>
            <ArrowRight aria-hidden="true" size={20} />
          </button>
        ) : null}
      </section>
    </>
  );
}

function readRecentlyViewed(): RecentlyViewedProduct[] {
  try {
    const parsed = JSON.parse(window.localStorage.getItem("teachermarket_recently_viewed") || "[]") as unknown[];
    return parsed
      .filter((item): item is RecentlyViewedProduct => Boolean(item && typeof item === "object" && "id" in item && "title" in item))
      .slice(0, 12);
  } catch {
    return [];
  }
}

function RecentlyViewed({ onBack, onOpenProduct }: { onBack: () => void; onOpenProduct: (productId: string) => void }) {
  const [items, setItems] = useState<RecentlyViewedProduct[]>(() => readRecentlyViewed());
  const clear = () => {
    window.localStorage.removeItem("teachermarket_recently_viewed");
    setItems([]);
  };
  return (
    <>
      <ScreenHeader eyebrow="Історія" title="Нещодавно переглянуті" onBack={onBack}>
        {items.length > 0 ? <button type="button" className="secondary" onClick={clear}>Очистити</button> : null}
      </ScreenHeader>
      <section className="dashboard-panel">
        {items.length === 0 ? (
          <div className="empty-state compact-empty-state">
            <Inbox aria-hidden="true" className="empty-icon" size={28} />
            <strong>Історія порожня</strong>
            <p>Відкрийте матеріал з каталогу, і він зʼявиться тут.</p>
          </div>
        ) : null}
        <div className="compact-list">
          {items.map((item) => (
            <button type="button" className="compact-item compact-item-button" key={item.id} onClick={() => onOpenProduct(item.id)}>
              <div>
                <h3>{item.title}</h3>
                <p>{getCategoryLabel(item.category)} · {item.seller.display_name}</p>
              </div>
              <div className="compact-meta">
                <strong>{formatPrice(item.price_amount, item.currency)}</strong>
                <span>{new Date(item.viewed_at).toLocaleDateString("uk-UA")}</span>
              </div>
            </button>
          ))}
        </div>
      </section>
    </>
  );
}

function StatTile({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="stat-tile">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function ServiceRulesPanel() {
  return (
    <section className="dashboard-panel service-rules" aria-label="Правила сервісу">
      <h2>Правила сервісу</h2>
      <ul>
        {serviceRules.map((rule) => (
          <li key={rule}>{rule}</li>
        ))}
      </ul>
    </section>
  );
}

function ProfileEditor({
  profile,
  isSaving,
  onSave,
}: {
  profile: SellerProfile;
  isSaving: boolean;
  onSave: (payload: { display_name: string; bio?: string | null; contact_username?: string | null }) => void;
}) {
  const [displayName, setDisplayName] = useState(profile.display_name);
  const [bio, setBio] = useState(profile.bio ?? "");
  const [username, setUsername] = useState(profile.contact_username ?? "");

  return (
    <section className="dashboard-panel profile-editor">
      <h2>Профіль автора</h2>
      <form
        onSubmit={(event) => {
          event.preventDefault();
          onSave({ display_name: displayName, bio: bio || null, contact_username: username || null });
        }}
      >
        <input value={displayName} onChange={(event) => setDisplayName(event.target.value)} placeholder="Імʼя автора" />
        <textarea value={bio} onChange={(event) => setBio(event.target.value)} placeholder="Про автора" />
        <input value={username} onChange={(event) => setUsername(event.target.value.replace(/^@/, ""))} placeholder="telegram_username" />
        <button type="submit" disabled={isSaving}>Зберегти профіль</button>
      </form>
    </section>
  );
}

function AdminPanel({ accessToken, onBack }: { accessToken?: string | null; onBack: () => void }) {
  const queryClient = useQueryClient();
  const [productStatus, setProductStatus] = useState("pending_moderation");
  const [selectedProductIds, setSelectedProductIds] = useState<string[]>([]);
  const [editingPlanId, setEditingPlanId] = useState<string | null>(null);
  const [adminNotice, setAdminNotice] = useState<string | null>(null);
  const [planDraft, setPlanDraft] = useState<Partial<AdminSubscriptionPlan>>({
    code: "",
    name: "",
    description: "",
    price_amount: 0,
    currency: "UAH",
    duration_days: 30,
    product_limit: 10,
    is_active: true,
  });
  const productsQuery = useQuery({
    queryKey: ["admin-products", accessToken, productStatus],
    queryFn: () => fetchAdminProducts(accessToken || "", productStatus),
    enabled: Boolean(accessToken),
    retry: false,
  });
  const plansQuery = useQuery({
    queryKey: ["admin-plans", accessToken],
    queryFn: () => fetchAdminPlans(accessToken || ""),
    enabled: Boolean(accessToken),
    retry: false,
  });
  const reportsQuery = useQuery({
    queryKey: ["admin-reports", accessToken],
    queryFn: () => fetchAdminReports(accessToken || ""),
    enabled: Boolean(accessToken),
    retry: false,
  });
  const adminAction = useMutation({
    mutationFn: async ({ action, id }: { action: string; id: string }) => {
      if (!accessToken) throw new Error("Потрібна авторизація.");
      if (action === "approve") return adminApproveProduct(id, accessToken);
      if (action === "hide") return adminHideProduct(id, accessToken);
      return adminRestoreProduct(id, accessToken);
    },
    onSuccess: async () => {
      setAdminNotice("Дію виконано.");
      await queryClient.invalidateQueries({ queryKey: ["admin-products"] });
      window.setTimeout(() => setAdminNotice(null), 3500);
    },
  });
  const planMutation = useMutation({
    mutationFn: () => {
      if (!accessToken) throw new Error("Потрібна авторизація.");
      return saveAdminPlan(accessToken, planDraft, editingPlanId ?? undefined);
    },
    onSuccess: async () => {
      setAdminNotice(editingPlanId ? "Тариф оновлено." : "Тариф створено.");
      setEditingPlanId(null);
      setPlanDraft({ code: "", name: "", description: "", price_amount: 0, currency: "UAH", duration_days: 30, product_limit: 10, is_active: true });
      await queryClient.invalidateQueries({ queryKey: ["admin-plans", accessToken] });
      window.setTimeout(() => setAdminNotice(null), 3500);
    },
  });
  const deactivatePlanMutation = useMutation({
    mutationFn: (planId: string) => {
      if (!accessToken) throw new Error("Потрібна авторизація.");
      return deactivateAdminPlan(planId, accessToken);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-plans", accessToken] }),
  });
  const togglePlanMutation = useMutation({
    mutationFn: ({ planId, isActive }: { planId: string; isActive: boolean }) => {
      if (!accessToken) throw new Error("Потрібна авторизація.");
      return saveAdminPlan(accessToken, { is_active: isActive }, planId);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-plans", accessToken] }),
  });
  const reportMutation = useMutation({
    mutationFn: (reportId: string) => {
      if (!accessToken) throw new Error("Потрібна авторизація.");
      return resolveAdminReport(reportId, accessToken);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-reports", accessToken] }),
  });
  const sellerStatusMutation = useMutation({
    mutationFn: ({ sellerId, status }: { sellerId: string; status: "active" | "suspended" }) => {
      if (!accessToken) throw new Error("Потрібна авторизація.");
      return updateAdminSellerStatus(sellerId, status, accessToken);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-products"] }),
  });
  const userBlockMutation = useMutation({
    mutationFn: ({ userId, isBlocked }: { userId: string; isBlocked: boolean }) => {
      if (!accessToken) throw new Error("Потрібна авторизація.");
      return updateAdminUserBlocked(userId, isBlocked, accessToken);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["admin-products"] }),
  });
  const bulkProductMutation = useMutation({
    mutationFn: ({ action, ids }: { action: "hide" | "restore"; ids: string[] }) => {
      if (!accessToken) throw new Error("Потрібна авторизація.");
      return action === "hide" ? adminBulkHideProducts(ids, accessToken) : adminBulkRestoreProducts(ids, accessToken);
    },
    onSuccess: async () => {
      setSelectedProductIds([]);
      setAdminNotice("Вибрані матеріали оновлено.");
      await queryClient.invalidateQueries({ queryKey: ["admin-products"] });
      window.setTimeout(() => setAdminNotice(null), 3500);
    },
  });
  const toggleSelection = (productId: string) => {
    setSelectedProductIds((current) => current.includes(productId) ? current.filter((id) => id !== productId) : [...current, productId]);
  };
  const startEditPlan = (plan: AdminSubscriptionPlan) => {
    setEditingPlanId(plan.id);
    setPlanDraft(plan);
  };

  return (
    <>
      <ScreenHeader eyebrow="Адмін-панель" title="Правки від адміна" onBack={onBack}>
        <p className="muted">Тут вносяться адмінські правки: модерація матеріалів, відновлення прихованих, тарифи й скарги.</p>
      </ScreenHeader>
      <section className="dashboard-panel">
        <h2>Матеріали</h2>
        <select value={productStatus} onChange={(event) => setProductStatus(event.target.value)}>
          <option value="pending_moderation">На модерації</option>
          <option value="published">Опубліковані</option>
          <option value="hidden">Приховані</option>
          <option value="rejected">Відхилені</option>
          <option value="deleted">Видалені</option>
        </select>
        {selectedProductIds.length > 0 ? (
          <div className="bulk-action-bar">
            <span>Вибрано: {selectedProductIds.length}</span>
            <button type="button" disabled={bulkProductMutation.isPending || productStatus !== "published"} onClick={() => bulkProductMutation.mutate({ action: "hide", ids: selectedProductIds })}>Сховати вибрані</button>
            <button type="button" disabled={bulkProductMutation.isPending || productStatus !== "hidden"} onClick={() => bulkProductMutation.mutate({ action: "restore", ids: selectedProductIds })}>Відновити вибрані</button>
            <button type="button" className="secondary" onClick={() => setSelectedProductIds([])}>Скинути</button>
          </div>
        ) : null}
        <div className="compact-list">
          {productsQuery.data?.items.map((product) => (
            <article className="compact-item" key={product.id}>
              <label className="compact-checkbox">
                <input
                  type="checkbox"
                  checked={selectedProductIds.includes(product.id)}
                  onChange={() => toggleSelection(product.id)}
                  aria-label={`Вибрати ${product.title}`}
                />
              </label>
              <div>
                <h3>{product.title}</h3>
                <p>{product.seller.display_name} · {formatPrice(product.price_amount, product.currency)}</p>
              </div>
              <div className="compact-meta">
                <span className={`status-pill status-${product.status}`}>{statusLabels[product.status] ?? product.status}</span>
                {product.status === "pending_moderation" ? <button type="button" onClick={() => adminAction.mutate({ action: "approve", id: product.id })}>Опублікувати</button> : null}
                {product.status === "published" ? <button type="button" onClick={() => adminAction.mutate({ action: "hide", id: product.id })}>Сховати</button> : null}
                {product.status === "hidden" ? <button type="button" onClick={() => adminAction.mutate({ action: "restore", id: product.id })}>Відновити</button> : null}
                <button
                  type="button"
                  className="text-button"
                  onClick={() => sellerStatusMutation.mutate({ sellerId: product.seller.id, status: product.seller.status === "suspended" ? "active" : "suspended" })}
                >
                  {product.seller.status === "suspended" ? "Активувати автора" : "Призупинити автора"}
                </button>
                {product.seller.user_id ? (
                  <button
                    type="button"
                    className="text-button"
                    onClick={() => userBlockMutation.mutate({ userId: product.seller.user_id || "", isBlocked: !product.seller.user_is_blocked })}
                  >
                    {product.seller.user_is_blocked ? "Розблокувати user" : "Заблокувати user"}
                  </button>
                ) : null}
              </div>
            </article>
          ))}
        </div>
      </section>
      <section className="dashboard-panel">
        <h2>Тарифи</h2>
        <div className="compact-list">
          {plansQuery.data?.map((plan) => (
            <article className="compact-item" key={plan.id}>
              <div>
                <h3>{plan.name}</h3>
                <p>{plan.code} · {formatPrice(plan.price_amount, plan.currency)} · {plan.product_limit} матеріалів · {plan.is_active ? "активний" : "вимкнений"}</p>
              </div>
              <div className="compact-meta">
                <button type="button" className="text-button" onClick={() => startEditPlan(plan)}>Редагувати</button>
                <button type="button" className="text-button" onClick={() => togglePlanMutation.mutate({ planId: plan.id, isActive: !plan.is_active })}>
                  {plan.is_active ? "Вимкнути" : "Активувати"}
                </button>
                {plan.is_active ? <button type="button" className="text-button" onClick={() => deactivatePlanMutation.mutate(plan.id)}>Деактивувати</button> : null}
              </div>
            </article>
          ))}
        </div>
        <form
          className="edit-product-form"
          onSubmit={(event) => {
            event.preventDefault();
            planMutation.mutate();
          }}
        >
          <h3>{editingPlanId ? "Редагування тарифу" : "Новий тариф"}</h3>
          <input placeholder="code" value={planDraft.code ?? ""} onChange={(event) => setPlanDraft({ ...planDraft, code: event.target.value })} />
          <input placeholder="Назва" value={planDraft.name ?? ""} onChange={(event) => setPlanDraft({ ...planDraft, name: event.target.value })} />
          <textarea placeholder="Опис" value={planDraft.description ?? ""} onChange={(event) => setPlanDraft({ ...planDraft, description: event.target.value })} />
          <input placeholder="Ціна, коп." inputMode="numeric" value={planDraft.price_amount ?? 0} onChange={(event) => setPlanDraft({ ...planDraft, price_amount: Number(event.target.value) })} />
          <input placeholder="Днів" inputMode="numeric" value={planDraft.duration_days ?? 30} onChange={(event) => setPlanDraft({ ...planDraft, duration_days: Number(event.target.value) })} />
          <input placeholder="Ліміт" inputMode="numeric" value={planDraft.product_limit ?? 10} onChange={(event) => setPlanDraft({ ...planDraft, product_limit: Number(event.target.value) })} />
          <label className="inline-toggle">
            <input type="checkbox" checked={Boolean(planDraft.is_active)} onChange={(event) => setPlanDraft({ ...planDraft, is_active: event.target.checked })} />
            Активний тариф
          </label>
          <div className="modal-actions">
            {editingPlanId ? (
              <button type="button" className="secondary" onClick={() => {
                setEditingPlanId(null);
                setPlanDraft({ code: "", name: "", description: "", price_amount: 0, currency: "UAH", duration_days: 30, product_limit: 10, is_active: true });
              }}>Скасувати</button>
            ) : null}
            <button type="submit">{editingPlanId ? "Зберегти тариф" : "Створити тариф"}</button>
          </div>
        </form>
      </section>
      <section className="dashboard-panel">
        <h2>Скарги</h2>
        <div className="compact-list">
          {reportsQuery.data?.map((report) => (
            <article className="compact-item" key={report.id}>
              <div>
                <h3>{report.product_title}</h3>
                <p>{report.reason}</p>
              </div>
              <button type="button" onClick={() => reportMutation.mutate(report.id)}>Закрити</button>
            </article>
          ))}
        </div>
      </section>
      {adminNotice ? <p className="success-message">{adminNotice}</p> : null}
      {adminAction.isError || planMutation.isError || deactivatePlanMutation.isError || togglePlanMutation.isError || reportMutation.isError || sellerStatusMutation.isError || userBlockMutation.isError || bulkProductMutation.isError ? (
        <p className="notice">Адмін-дію не виконано. Перевірте статус обʼєкта й спробуйте ще раз.</p>
      ) : null}
    </>
  );
}

function SellerMenuButton({
  icon,
  title,
  description,
  onClick,
}: {
  icon: ReactNode;
  title: string;
  description: string;
  onClick: () => void;
}) {
  return (
    <button className="seller-menu-item" type="button" onClick={onClick}>
      <span className="seller-menu-icon">{icon}</span>
      <span>
        <strong>{title}</strong>
        <small>{description}</small>
      </span>
      <ArrowRight aria-hidden="true" size={20} />
    </button>
  );
}

function ScreenHeader({
  eyebrow,
  title,
  children,
  onBack,
}: {
  eyebrow: string;
  title: string;
  children?: ReactNode;
  onBack: () => void;
}) {
  return (
    <section className="page-header seller-subscreen-header">
      <button type="button" className="text-button back-link" onClick={onBack}>
        <ArrowLeft aria-hidden="true" size={17} />
        Назад
      </button>
      <p className="eyebrow">{eyebrow}</p>
      <h1>{title}</h1>
      {children}
    </section>
  );
}

function SellerProducts({
  products,
  canAddProduct,
  accessToken,
  botUrl,
  onBack,
}: {
  products: SellerProduct[];
  canAddProduct: boolean;
  accessToken?: string | null;
  botUrl: string;
  onBack: () => void;
}) {
  const queryClient = useQueryClient();
  const [editingProduct, setEditingProduct] = useState<SellerProduct | null>(null);
  const productMutation = useMutation({
    mutationFn: async ({ product, payload }: { product: SellerProduct; payload: SellerProductUpdate }) => {
      if (!accessToken) throw new Error("Потрібна авторизація.");
      return updateSellerProduct(product.id, payload, accessToken);
    },
    onSuccess: async () => {
      setEditingProduct(null);
      await queryClient.invalidateQueries({ queryKey: ["seller-dashboard", accessToken] });
    },
  });
  const submitMutation = useMutation({
    mutationFn: (productId: string) => {
      if (!accessToken) throw new Error("Потрібна авторизація.");
      return submitSellerProduct(productId, accessToken);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["seller-dashboard", accessToken] }),
  });
  const deleteMutation = useMutation({
    mutationFn: (productId: string) => {
      if (!accessToken) throw new Error("Потрібна авторизація.");
      return deleteSellerProduct(productId, accessToken);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["seller-dashboard", accessToken] }),
  });

  return (
    <>
      <ScreenHeader eyebrow="Матеріали" title="Мої матеріали" onBack={onBack}>
        {canAddProduct ? (
          <a className="primary-link-button" href={botUrl} target="_blank" rel="noreferrer">
            <PackagePlus aria-hidden="true" size={18} />
            Додати
          </a>
        ) : null}
      </ScreenHeader>
      <section className="dashboard-panel">
        <div className="management-hint">
          <strong>Редагування і видалення</strong>
          <p>Кнопки керування знаходяться в кожному матеріалі. Чернетки й відхилені матеріали можна редагувати, відхилені — повторно відправити на модерацію, будь-який свій матеріал — видалити.</p>
        </div>
        {products.length === 0 ? (
          <div className="empty-state compact-empty-state">
            <LayoutGrid aria-hidden="true" className="empty-icon" size={28} />
            <strong>Матеріалів ще немає</strong>
            <p>Додайте перший матеріал через Telegram bot.</p>
            <a className="primary-link-button" href={botUrl} target="_blank" rel="noreferrer">
              Додати матеріал
            </a>
          </div>
        ) : null}
        <div className="compact-list">
          {products.map((product) => (
            <article className="compact-item" key={product.id}>
              <div>
                <h3>{product.title}</h3>
                <p>
                  {getLanguageLabel(product.language)} · {getLevelLabel(product.level)} · {getCategoryLabel(product.category)}
                </p>
                {product.rejection_reason ? <p className="warning-text">{product.rejection_reason}</p> : null}
              </div>
              <div className="compact-meta product-management-meta">
                <span className={`status-pill status-${product.status}`}>{statusLabels[product.status] ?? product.status}</span>
                <strong>{formatPrice(product.price_amount, product.currency)}</strong>
              </div>
              <SellerProductVisibilityBlock product={product} accessToken={accessToken} />
              <div className="product-action-row" aria-label={`Керування матеріалом ${product.title}`}>
                {["draft", "rejected"].includes(product.status) ? (
                  <button type="button" className="secondary" onClick={() => setEditingProduct(product)}>
                    <Pencil aria-hidden="true" size={16} />
                    Редагувати
                  </button>
                ) : (
                  <button type="button" className="secondary" disabled title="Редагування доступне для чернеток і відхилених матеріалів">
                    <Pencil aria-hidden="true" size={16} />
                    Редагувати
                  </button>
                )}
                {product.status === "rejected" ? (
                  <button type="button" onClick={() => submitMutation.mutate(product.id)}>
                    <Send aria-hidden="true" size={16} />
                    На модерацію
                  </button>
                ) : null}
                {["draft", "rejected", "hidden", "published"].includes(product.status) ? (
                  <button
                    type="button"
                    className="danger-button"
                    onClick={() => {
                      const message = product.status === "published"
                        ? "Опублікований матеріал буде приховано як видалений. Видалити?"
                        : "Видалити матеріал?";
                      if (window.confirm(message)) {
                        deleteMutation.mutate(product.id);
                      }
                    }}
                  >
                    <Trash2 aria-hidden="true" size={16} />
                    Видалити
                  </button>
                ) : null}
              </div>
            </article>
          ))}
        </div>
        {editingProduct ? (
          <EditProductForm
            product={editingProduct}
            accessToken={accessToken}
            isSaving={productMutation.isPending}
            onCancel={() => setEditingProduct(null)}
            onSave={(payload) => productMutation.mutate({ product: editingProduct, payload })}
          />
        ) : null}
        {productMutation.isError || submitMutation.isError || deleteMutation.isError ? (
          <p className="notice">Не вдалося оновити матеріал. Перевірте дані й спробуйте ще раз.</p>
        ) : null}
      </section>
    </>
  );
}

function SellerProductVisibilityBlock({
  product,
  accessToken,
}: {
  product: SellerProduct;
  accessToken?: string | null;
}) {
  const queryClient = useQueryClient();
  const [placementNotice, setPlacementNotice] = useState<string | null>(null);
  const visibilityQuery = useQuery({
    queryKey: ["seller-product-visibility", accessToken, product.id],
    queryFn: () => fetchSellerProductVisibility(product.id, accessToken || ""),
    enabled: Boolean(accessToken),
    retry: false,
  });
  const placementMutation = useMutation({
    mutationFn: () => {
      if (!accessToken) throw new Error("Потрібна авторизація.");
      return buySellerProductPlacement(product.id, accessToken);
    },
    onMutate: () => {
      setPlacementNotice(null);
    },
    onSuccess: async () => {
      setPlacementNotice("Розміщення активовано.");
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["seller-dashboard", accessToken] }),
        queryClient.invalidateQueries({ queryKey: ["seller-product-visibility", accessToken, product.id] }),
      ]);
      window.setTimeout(() => setPlacementNotice(null), 3500);
    },
    onError: () => {
      setPlacementNotice("Не вдалося оформити розміщення.");
      window.setTimeout(() => setPlacementNotice(null), 3500);
    },
  });

  if (!accessToken) {
    return (
      <div className="visibility-block">
        <span className="visibility-title">Видимість у каталозі</span>
        <span className="visibility-muted">Доступно після входу через Telegram.</span>
      </div>
    );
  }

  if (visibilityQuery.isLoading) {
    return (
      <div className="visibility-block">
        <span className="visibility-title">Видимість у каталозі</span>
        <span className="visibility-muted">Перевіряємо...</span>
      </div>
    );
  }

  if (visibilityQuery.isError || !visibilityQuery.data) {
    return (
      <div className="visibility-block visibility-block-hidden">
        <span className="visibility-title">Видимість у каталозі</span>
        <span className="visibility-muted">Не вдалося завантажити статус.</span>
      </div>
    );
  }

  const visibility = visibilityQuery.data;
  const fallbackTone: "visible" | "hidden" = visibility.is_visible ? "visible" : "hidden";
  const meta = visibilityLabels[visibility.primary_reason] ?? {
    label: visibility.is_visible ? "Видно в каталозі" : "Не видно в каталозі",
    tone: fallbackTone,
  };
  const canBuyPlacement =
    product.status === "published" &&
    visibility.primary_reason === "hidden_after_grace" &&
    !visibility.has_active_placement;

  return (
    <div className={`visibility-block visibility-block-${meta.tone}`}>
      <div className="visibility-summary">
        <span className="visibility-title">{meta.label}</span>
        {visibility.published_rank != null ? (
          <span className="visibility-muted">
            Позиція #{visibility.published_rank} / free-ліміт {visibility.free_tier_limit}
          </span>
        ) : null}
        {visibility.subscription_grace_until ? (
          <span className="visibility-muted">Грейс до {formatDate(visibility.subscription_grace_until)}</span>
        ) : null}
      </div>
      {canBuyPlacement ? (
        <button
          type="button"
          className="secondary placement-button"
          disabled={placementMutation.isPending}
          onClick={() => {
            if (window.confirm("Розмістити матеріал за 40 грн?")) {
              placementMutation.mutate();
            }
          }}
        >
          {placementMutation.isPending ? "Розміщуємо..." : "Розмістити за 40 грн"}
        </button>
      ) : null}
      {placementNotice ? <span className={placementMutation.isError ? "visibility-error" : "visibility-success"}>{placementNotice}</span> : null}
    </div>
  );
}

function EditProductForm({
  product,
  accessToken,
  isSaving,
  onCancel,
  onSave,
}: {
  product: SellerProduct;
  accessToken?: string | null;
  isSaving: boolean;
  onCancel: () => void;
  onSave: (payload: SellerProductUpdate) => void;
}) {
  const [title, setTitle] = useState(product.title);
  const [description, setDescription] = useState(product.description);
  const [language, setLanguage] = useState(product.language);
  const [level, setLevel] = useState(product.level ?? "");
  const [category, setCategory] = useState(product.category);
  const [audience, setAudience] = useState(product.audience ?? "");
  const [price, setPrice] = useState(String(Math.round(product.price_amount / 100)));
  const [deliveryMethod, setDeliveryMethod] = useState(product.delivery_method);
  const [externalUrl, setExternalUrl] = useState(product.external_file_url ?? "");
  const [productFileId, setProductFileId] = useState(product.product_file_id ?? null);
  const [previewIds, setPreviewIds] = useState(product.preview_file_ids);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const uploadFile = async (file: File, kind: "product_file" | "preview_image") => {
    if (!accessToken) return;
    try {
      const uploaded = await uploadSellerFile(file, kind, accessToken);
      if (kind === "product_file") {
        setProductFileId(uploaded.id);
      } else {
        setPreviewIds((current) => [...current, uploaded.id].slice(0, 3));
      }
      setUploadError(null);
    } catch {
      setUploadError("Не вдалося завантажити файл.");
    }
  };

  return (
    <form
      className="edit-product-form"
      onSubmit={(event) => {
        event.preventDefault();
        onSave({
          title,
          description,
          language,
          level: level || null,
          category,
          audience: audience || null,
          price_amount: Number(price) * 100,
          currency: product.currency,
          delivery_method: deliveryMethod,
          external_file_url: deliveryMethod === "external_link" ? externalUrl : null,
          product_file_id: deliveryMethod === "uploaded_file" ? productFileId : null,
          preview_file_ids: previewIds,
        });
      }}
    >
      <h3>Редагування матеріалу</h3>
      <input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Назва" />
      <textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Опис" />
      <div className="form-grid">
        <input value={language} onChange={(event) => setLanguage(event.target.value)} placeholder="Мова" />
        <input value={level} onChange={(event) => setLevel(event.target.value)} placeholder="Рівень" />
        <input value={category} onChange={(event) => setCategory(event.target.value)} placeholder="Тип" />
        <input value={audience} onChange={(event) => setAudience(event.target.value)} placeholder="Аудиторія" />
        <input value={price} inputMode="numeric" onChange={(event) => setPrice(event.target.value.replace(/\D/g, ""))} placeholder="Ціна, грн" />
        <select value={deliveryMethod} onChange={(event) => setDeliveryMethod(event.target.value)}>
          <option value="uploaded_file">Файл у сервісі</option>
          <option value="external_link">Зовнішнє посилання</option>
          <option value="private_message">Приватне повідомлення</option>
        </select>
      </div>
      {deliveryMethod === "external_link" ? <input value={externalUrl} onChange={(event) => setExternalUrl(event.target.value)} placeholder="https://..." /> : null}
      {deliveryMethod === "uploaded_file" ? (
        <label className="file-control">
          Основний файл
          <input type="file" onChange={(event) => event.target.files?.[0] && uploadFile(event.target.files[0], "product_file")} />
        </label>
      ) : null}
      <label className="file-control">
        Превʼю ({previewIds.length}/3)
        <input type="file" accept="image/*" onChange={(event) => event.target.files?.[0] && uploadFile(event.target.files[0], "preview_image")} />
      </label>
      {uploadError ? <p className="notice">{uploadError}</p> : null}
      <div className="modal-actions">
        <button type="button" className="secondary" onClick={onCancel}>Скасувати</button>
        <button type="submit" disabled={isSaving || previewIds.length === 0}>Зберегти</button>
      </div>
    </form>
  );
}

function ContactRequests({ data, accessToken, onBack }: { data: SellerDashboardData; accessToken?: string | null; onBack: () => void }) {
  const queryClient = useQueryClient();
  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: "new" | "handled" | "archived" }) => {
      if (!accessToken) throw new Error("Потрібна авторизація.");
      return updateContactRequestStatus(id, status, accessToken);
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["seller-dashboard", accessToken] }),
  });
  return (
    <>
      <ScreenHeader eyebrow="Звернення" title="Покупці" onBack={onBack} />
      <section className="dashboard-panel">
        {data.contactRequests.length === 0 ? (
          <div className="empty-state compact-empty-state">
            <Inbox aria-hidden="true" className="empty-icon" size={28} />
            <strong>Нових звернень немає</strong>
            <p>Коли покупець зацікавиться матеріалом, звернення зʼявиться тут.</p>
          </div>
        ) : null}
        <div className="compact-list">
          {data.contactRequests.map((request) => (
            <article className="compact-item" key={request.id}>
              <div>
                <h3>{request.requester_display_name ?? request.requester_username ?? "Покупець"}</h3>
                <p>{request.product_title}</p>
                {request.message ? <p className="message-text">{request.message}</p> : null}
                <span className={`status-pill status-${request.status}`}>{request.status}</span>
              </div>
              <div className="compact-meta">
                {request.requester_username ? (
                  <a className="text-link" href={`https://t.me/${request.requester_username}`} target="_blank" rel="noreferrer">
                    Telegram
                  </a>
                ) : null}
                <button type="button" className="text-button" onClick={() => statusMutation.mutate({ id: request.id, status: "handled" })}>Оброблено</button>
                <button type="button" className="text-button" onClick={() => statusMutation.mutate({ id: request.id, status: "archived" })}>Архів</button>
              </div>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}

function Subscription({
  data,
  plans,
  hasAccessToken,
  isAdmin,
  isProcessing,
  onBack,
  onChoosePlan,
}: {
  data: SellerDashboardData;
  plans: SellerSubscriptionPlan[];
  hasAccessToken: boolean;
  isAdmin: boolean;
  isProcessing: boolean;
  onBack: () => void;
  onChoosePlan: (planId: string) => void;
}) {
  const subscription = data.subscription;
  return (
    <>
      <ScreenHeader eyebrow="Підписка" title={subscription.plan?.name ?? "Free"} onBack={onBack} />
      <section className="dashboard-panel">
        <div className="subscription-meter">
          <span>
            {subscription.product_count} з {subscription.product_limit} матеріалів
          </span>
          <progress max={subscription.product_limit} value={subscription.product_count} />
        </div>
        <p className="muted">Статус: {statusLabels[subscription.status] ?? subscription.status}</p>
        {subscription.expires_at ? <p className="muted">Діє до: {new Date(subscription.expires_at).toLocaleDateString("uk-UA")}</p> : null}
        {!subscription.can_add_product ? <p className="warning-text">Ліміт матеріалів вичерпано.</p> : null}
        {!isAdmin ? (
          <p className="muted">У закритому тесті mock-оплату після оформлення підтверджує адмін. Реальні списання не проводяться.</p>
        ) : null}
        <div className="plans-list">
          {plans.map((plan) => {
            const isCurrent = subscription.plan?.id === plan.id || (!subscription.plan && plan.code === "free");
            return (
              <article className="plan-item" key={plan.id}>
                <div>
                  <h3>{plan.name}</h3>
                  <p>{plan.description ?? `${plan.product_limit} матеріалів`}</p>
                  <strong>{formatPrice(plan.price_amount, plan.currency)}</strong>
                </div>
                {plan.price_amount > 0 ? (
                  <button type="button" disabled={!hasAccessToken || isProcessing} onClick={() => onChoosePlan(plan.id)}>
                    {isProcessing ? "Створюємо..." : isCurrent ? "Продовжити mock" : "Оформити mock"}
                  </button>
                ) : (
                  <span className="plan-badge">{isCurrent ? "Поточний" : "Free"}</span>
                )}
              </article>
            );
          })}
        </div>
      </section>
    </>
  );
}
