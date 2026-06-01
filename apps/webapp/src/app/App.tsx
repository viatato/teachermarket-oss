import { Component, useEffect, useState, type ErrorInfo, type ReactNode } from "react";
import { QueryClient, QueryClientProvider, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bookmark, Home, Search, UserRound } from "lucide-react";

import { addFavorite, fetchFavorites, removeFavorite } from "../api/products";
import { authenticateWithTelegram, getTelegramInitData, isTelegramWebApp } from "../api/auth";
import { CatalogPage } from "../pages/CatalogPage";
import { FavoritesPage } from "../pages/FavoritesPage";
import { HomePage } from "../pages/HomePage";
import { ProductPage } from "../pages/ProductPage";
import { SellerDashboardPage, type SellerScreen } from "../pages/SellerDashboardPage";
import type { CatalogFilters } from "../types/products";

const queryClient = new QueryClient();
type View = "home" | "catalog" | "product" | "favorites" | "profile" | SellerScreen | "not-found";
type RouteState = {
  view: View;
  productId: string | null;
};
type FavoriteFeedback = {
  message: string;
  undoProductId?: string;
};

const emptyFilters: CatalogFilters = {
  search: "",
  language: "",
  level: "",
  category: "",
  audience: "",
  min_price: "",
  max_price: "",
  sort: "new",
  page: "1",
};

const sellerRoutes: Record<SellerScreen, string> = {
  seller: "/author",
  "seller-products": "/author/materials",
  "seller-requests": "/author/requests",
  "seller-subscription": "/author/subscription",
  "recently-viewed": "/profile/recently-viewed",
  admin: "/author/admin",
};

const routeViews: Record<string, RouteState> = {
  "/": { view: "home", productId: null },
  "/catalog": { view: "catalog", productId: null },
  "/saved": { view: "favorites", productId: null },
  "/profile": { view: "profile", productId: null },
  "/author": { view: "seller", productId: null },
  "/author/materials": { view: "seller-products", productId: null },
  "/author/requests": { view: "seller-requests", productId: null },
  "/author/subscription": { view: "seller-subscription", productId: null },
  "/profile/recently-viewed": { view: "recently-viewed", productId: null },
  "/author/admin": { view: "admin", productId: null },
};

function normalizePath(path: string) {
  const normalized = path.length > 1 ? path.replace(/\/+$/, "") : path;
  return normalized || "/";
}

function decodePathSegment(value: string) {
  try {
    return decodeURIComponent(value);
  } catch {
    return value;
  }
}

function routeFromPath(path: string): RouteState {
  const normalizedPath = normalizePath(path);
  const productMatch = normalizedPath.match(/^\/materials\/([^/]+)$/);
  if (productMatch) {
    return { view: "product", productId: decodePathSegment(productMatch[1]) };
  }
  return routeViews[normalizedPath] ?? { view: "not-found", productId: null };
}

function pathForView(view: View, productId?: string | null) {
  if (view === "product" && productId) {
    return `/materials/${encodeURIComponent(productId)}`;
  }
  if (view in sellerRoutes) {
    return sellerRoutes[view as SellerScreen];
  }
  switch (view) {
    case "catalog":
      return "/catalog";
    case "favorites":
      return "/saved";
    case "profile":
      return "/profile";
    case "home":
      return "/";
    default:
      return window.location.pathname;
  }
}

function telegramVersionAtLeast(version: string | undefined, minimum: string) {
  if (!version) {
    return false;
  }
  const currentParts = version.split(".").map((part) => Number.parseInt(part, 10) || 0);
  const minimumParts = minimum.split(".").map((part) => Number.parseInt(part, 10) || 0);
  const maxLength = Math.max(currentParts.length, minimumParts.length);
  for (let index = 0; index < maxLength; index += 1) {
    const current = currentParts[index] ?? 0;
    const target = minimumParts[index] ?? 0;
    if (current > target) {
      return true;
    }
    if (current < target) {
      return false;
    }
  }
  return true;
}

class AppErrorBoundary extends Component<{ children: ReactNode }, { hasError: boolean }> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error(error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <main id="main-content" className="app-shell" tabIndex={-1}>
          <section className="empty-state">
            <Search aria-hidden="true" className="empty-icon" size={28} />
            <strong>Не вдалося показати сторінку</strong>
            <p>Оновіть інтерфейс або поверніться на головну.</p>
            <button
              type="button"
              onClick={() => {
                window.history.pushState({}, "", "/");
                window.location.reload();
              }}
            >
              <Home aria-hidden="true" size={17} />
              На головну
            </button>
          </section>
        </main>
      );
    }

    return this.props.children;
  }
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppErrorBoundary>
        <AppContent />
      </AppErrorBoundary>
    </QueryClientProvider>
  );
}

function AppContent() {
  const queryClientInstance = useQueryClient();
  const initialRoute = routeFromPath(window.location.pathname);
  const [view, setView] = useState<View>(initialRoute.view);
  const [selectedProductId, setSelectedProductId] = useState<string | null>(initialRoute.productId);
  const [filters, setFilters] = useState<CatalogFilters>(emptyFilters);
  const [favoriteIds, setFavoriteIds] = useState<string[]>([]);
  const [favoriteFeedback, setFavoriteFeedback] = useState<FavoriteFeedback | null>(null);
  const telegramInitData = getTelegramInitData();
  const hasTelegramInitData = isTelegramWebApp();

  const navigateToView = (nextView: View, productId?: string | null, options?: { replace?: boolean }) => {
    const nextProductId = nextView === "product" ? productId ?? null : null;
    setSelectedProductId(nextProductId);
    setView(nextView);

    const nextPath = pathForView(nextView, nextProductId);
    if (nextPath !== window.location.pathname) {
      const method = options?.replace ? "replaceState" : "pushState";
      window.history[method]({}, "", nextPath);
    }
  };

  useEffect(() => {
    window.Telegram?.WebApp?.ready?.();
    window.Telegram?.WebApp?.expand?.();
  }, []);

  useEffect(() => {
    const handlePopState = () => {
      const nextRoute = routeFromPath(window.location.pathname);
      setSelectedProductId(nextRoute.productId);
      setView(nextRoute.view);
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [view, selectedProductId]);

  useEffect(() => {
    if (!favoriteFeedback) {
      return;
    }
    const timer = window.setTimeout(() => setFavoriteFeedback(null), 5000);
    return () => window.clearTimeout(timer);
  }, [favoriteFeedback]);

  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    const backButton = tg?.BackButton;
    if (!backButton || !telegramVersionAtLeast(tg?.version, "6.1")) {
      return;
    }

    const handleBackClick = () => {
      if (view === "product") {
        navigateToView("catalog", null, { replace: true });
        return;
      }
      if (view === "favorites") {
        navigateToView("catalog", null, { replace: true });
        return;
      }
      if (view === "seller-products" || view === "seller-requests" || view === "seller-subscription") {
        navigateToView("seller", null, { replace: true });
        return;
      }
      if (view === "recently-viewed") {
        navigateToView("profile", null, { replace: true });
        return;
      }
      if (view === "seller") {
        navigateToView("profile", null, { replace: true });
        return;
      }
      if (view === "profile") {
        navigateToView("home", null, { replace: true });
        return;
      }
      if (view === "not-found") {
        navigateToView("home", null, { replace: true });
        return;
      }
      tg.close?.();
    };

    backButton.onClick(handleBackClick);
    if (view === "home") {
      backButton.hide();
    } else {
      backButton.show();
    }

    return () => {
      backButton.offClick(handleBackClick);
    };
  }, [view]);

  const authQuery = useQuery({
    queryKey: ["telegram-auth", telegramInitData],
    queryFn: () => authenticateWithTelegram(telegramInitData),
    enabled: hasTelegramInitData,
    retry: false,
    staleTime: 1000 * 60 * 15,
  });

  const accessToken = authQuery.data?.access_token ?? null;

  const favoritesQuery = useQuery({
    queryKey: ["favorites", accessToken],
    queryFn: () => fetchFavorites(accessToken || ""),
    enabled: Boolean(accessToken),
    retry: false,
  });

  useEffect(() => {
    if (favoritesQuery.data) {
      setFavoriteIds(favoritesQuery.data.map((product) => product.id));
    }
  }, [favoritesQuery.data]);

  const favoriteMutation = useMutation({
    mutationFn: async ({ productId, shouldSave }: { productId: string; shouldSave: boolean }) => {
      if (!accessToken) {
        return;
      }
      if (shouldSave) {
        await addFavorite(productId, accessToken);
      } else {
        await removeFavorite(productId, accessToken);
      }
    },
    onSuccess: async () => {
      await queryClientInstance.invalidateQueries({ queryKey: ["favorites", accessToken] });
    },
  });

  const openProduct = (productId: string) => navigateToView("product", productId);

  const isCatalogActive = view === "catalog" || view === "product";
  const isProfileActive =
    view === "profile" ||
    view === "seller" ||
    view === "seller-products" ||
    view === "seller-requests" ||
    view === "seller-subscription" ||
    view === "recently-viewed" ||
    view === "admin";

  const toggleFavorite = (productId: string) => {
    setFavoriteIds((current) => {
      const shouldSave = !current.includes(productId);
      const updated = shouldSave ? [...current, productId] : current.filter((id) => id !== productId);
      favoriteMutation.mutate(
        { productId, shouldSave },
        {
          onSuccess: () => {
            setFavoriteFeedback(
              shouldSave
                ? { message: "Додано до збереженого." }
                : { message: "Прибрано зі збереженого.", undoProductId: productId },
            );
          },
          onError: () => {
            setFavoriteIds(current);
            setFavoriteFeedback({ message: "Не вдалося оновити збережене. Спробуйте ще раз." });
          },
        },
      );
      return updated;
    });
  };

  return (
    <>
      <a className="skip-link" href="#main-content">
        Перейти до контенту
      </a>
      <nav className="bottom-nav" aria-label="Основна навігація">
        <span className="nav-brand-mark" aria-hidden="true">ТМ</span>
        <button
          type="button"
          className={view === "home" ? "is-active" : ""}
          aria-label="Головна"
          onClick={() => navigateToView("home")}
        >
          <Home aria-hidden="true" size={20} />
          <span className="nav-home-label">Головна</span>
          <span className="nav-home-short">ТМ</span>
        </button>
        <button
          type="button"
          className={isCatalogActive ? "is-active" : ""}
          aria-label="Каталог"
          onClick={() => navigateToView("catalog")}
        >
          <Search aria-hidden="true" size={20} />
          <span>Каталог</span>
        </button>
        <button
          type="button"
          className={view === "favorites" ? "is-active" : ""}
          aria-label="Збережене"
          onClick={() => navigateToView("favorites")}
        >
          <Bookmark aria-hidden="true" size={20} />
          <span>Збережене</span>
          {favoriteIds.length > 0 ? <span className="nav-badge">{favoriteIds.length}</span> : null}
        </button>
        <button
          type="button"
          className={isProfileActive ? "is-active" : ""}
          aria-label="Мій профіль"
          onClick={() => navigateToView("profile")}
        >
          <UserRound aria-hidden="true" size={20} />
          <span>Мій профіль</span>
        </button>
      </nav>
      {authQuery.isError ? (
        <div className="auth-banner">
          <span>Не вдалося увійти через Telegram. Показуємо демо-режим.</span>
          <button type="button" onClick={() => authQuery.refetch()}>
            Спробувати ще
          </button>
        </div>
      ) : null}
      {favoriteFeedback ? (
        <div className="status-toast" role="status">
          <span>{favoriteFeedback.message}</span>
          {favoriteFeedback.undoProductId ? (
            <button type="button" onClick={() => toggleFavorite(favoriteFeedback.undoProductId || "")}>
              Скасувати
            </button>
          ) : null}
        </div>
      ) : null}
      {view === "home" ? (
        <HomePage
          onOpenCatalog={() => navigateToView("catalog")}
          onOpenSeller={() => navigateToView("seller")}
          onCategorySelect={(category) => {
            setFilters({ ...emptyFilters, category });
            navigateToView("catalog");
          }}
        />
      ) : null}
      {view === "catalog" ? (
        <CatalogPage
          filters={filters}
          favoriteIds={favoriteIds}
          isFavoritesSyncing={favoriteMutation.isPending || favoritesQuery.isFetching}
          onFiltersChange={setFilters}
          onOpenProduct={openProduct}
          onToggleFavorite={toggleFavorite}
        />
      ) : null}
      {view === "product" && selectedProductId ? (
        <ProductPage
          productId={selectedProductId}
          isFavorite={favoriteIds.includes(selectedProductId)}
          accessToken={accessToken}
          currentUserId={authQuery.data?.user.id ?? null}
          onBack={() => navigateToView("catalog")}
          onToggleFavorite={toggleFavorite}
        />
      ) : null}
      {view === "favorites" ? (
        <FavoritesPage
          favoriteIds={favoriteIds}
          accessToken={accessToken}
          onOpenCatalog={() => navigateToView("catalog")}
          onOpenProduct={openProduct}
          onToggleFavorite={toggleFavorite}
        />
      ) : null}
      {isProfileActive ? (
        <SellerDashboardPage
          accessToken={accessToken}
          isAdmin={Boolean(authQuery.data?.user.is_admin)}
          activeScreen={view as "profile" | SellerScreen}
          favoriteCount={favoriteIds.length}
          onOpenCatalog={() => navigateToView("catalog")}
          onOpenFavorites={() => navigateToView("favorites")}
          onOpenProduct={openProduct}
          onNavigate={(screen) => navigateToView(screen)}
        />
      ) : null}
      {view === "not-found" ? <NotFoundPage onGoHome={() => navigateToView("home", null, { replace: true })} /> : null}
    </>
  );
}

function NotFoundPage({ onGoHome }: { onGoHome: () => void }) {
  return (
    <main id="main-content" className="app-shell" tabIndex={-1}>
      <section className="empty-state">
        <Search aria-hidden="true" className="empty-icon" size={28} />
        <strong>Сторінку не знайдено</strong>
        <p>Цей розділ не існує або посилання застаріло.</p>
        <button type="button" onClick={onGoHome}>
          <Home aria-hidden="true" size={17} />
          На головну
        </button>
      </section>
    </main>
  );
}
