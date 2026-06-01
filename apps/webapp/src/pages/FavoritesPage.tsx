import { useQuery } from "@tanstack/react-query";
import { Bookmark, Search } from "lucide-react";

import { demoProducts, fetchFavorites } from "../api/products";
import { ProductCard } from "../components/ProductCard";

type FavoritesPageProps = {
  favoriteIds: string[];
  accessToken?: string | null;
  onOpenCatalog: () => void;
  onOpenProduct: (productId: string) => void;
  onToggleFavorite: (productId: string) => void;
};

export function FavoritesPage({
  favoriteIds,
  accessToken,
  onOpenCatalog,
  onOpenProduct,
  onToggleFavorite,
}: FavoritesPageProps) {
  const query = useQuery({
    queryKey: ["favorites", accessToken],
    queryFn: () => fetchFavorites(accessToken || ""),
    enabled: Boolean(accessToken),
    retry: false,
  });
  const favoriteProducts = query.data ?? demoProducts.items.filter((product) => favoriteIds.includes(product.id));
  const isDemo = !accessToken || query.isError;

  return (
    <main id="main-content" className="app-shell" tabIndex={-1}>
      <section className="page-header">
        <p className="eyebrow">Збережене</p>
        <h1>Обрані матеріали</h1>
        <p className="lead">Тут зібрані матеріали, які ви хочете переглянути пізніше.</p>
      </section>
      {query.isLoading ? <p className="notice">Завантажуємо збережене...</p> : null}
      {isDemo ? (
        <div className="demo-banner subtle-demo-banner">
          <span>Локально</span>
          <p>У Telegram збережене синхронізується з вашим акаунтом.</p>
        </div>
      ) : null}
      {favoriteProducts.length === 0 ? (
        <section className="empty-state favorites-empty-state">
          <Bookmark aria-hidden="true" className="empty-icon" size={34} />
          <strong>Поки що немає збережених матеріалів</strong>
          <p>Натискайте сердечко на картках, щоб зібрати короткий список для наступного уроку.</p>
          <button type="button" onClick={onOpenCatalog}>
            <Search aria-hidden="true" size={17} />
            Знайти матеріали
          </button>
        </section>
      ) : (
        <section className="product-grid">
          {favoriteProducts.map((product) => (
            <ProductCard
              key={product.id}
              product={product}
              isFavorite
              onOpen={onOpenProduct}
              onToggleFavorite={onToggleFavorite}
            />
          ))}
        </section>
      )}
    </main>
  );
}
