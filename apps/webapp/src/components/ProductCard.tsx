import { FileText, Heart } from "lucide-react";

import { formatPrice } from "../api/products";
import type { CatalogProductListItem } from "../types/products";

type ProductCardProps = {
  product: CatalogProductListItem;
  onOpen: (productId: string) => void;
  isFavorite: boolean;
  onToggleFavorite: (productId: string) => void;
};

const categoryLabels: Record<string, string> = {
  worksheet: "Робочий аркуш",
  speaking_cards: "Картки для говоріння",
  test: "Тест",
  presentation: "Презентація",
  game: "Гра",
  template: "Шаблон",
};

const languageLabels: Record<string, string> = {
  english: "Англійська",
  german: "Німецька",
  polish: "Польська",
  ukrainian: "Українська",
};

const levelLabels: Record<string, string> = {
  a1: "A1",
  a2: "A2",
  b1: "B1",
  b2: "B2",
  kids: "Діти",
  teens: "Підлітки",
  mixed: "Змішаний",
};

const audienceLabels: Record<string, string> = {
  teachers: "Викладачі",
  teens: "Підлітки",
  kids: "Діти",
  business: "Бізнес",
  adults: "Дорослі",
};

const deliveryLabels: Record<string, string> = {
  uploaded_file: "Файл у сервісі",
  external_link: "Автор має посилання",
  private_message: "Передача напряму",
};

export function getCategoryLabel(category: string) {
  return categoryLabels[category] ?? category.replace("_", " ");
}

export function getLanguageLabel(language: string) {
  return languageLabels[language] ?? language;
}

export function getLevelLabel(level?: string | null) {
  if (!level) {
    return "Змішаний";
  }
  return levelLabels[level] ?? level;
}

export function getAudienceLabel(audience?: string | null) {
  if (!audience) {
    return "Викладачі";
  }
  return audienceLabels[audience] ?? audience;
}

export function getDeliveryLabel(deliveryMethod?: string | null) {
  if (!deliveryMethod) {
    return deliveryLabels.uploaded_file;
  }
  return deliveryLabels[deliveryMethod] ?? deliveryMethod;
}

export function ProductCard({ product, onOpen, isFavorite, onToggleFavorite }: ProductCardProps) {
  return (
    <article className={`product-card product-card-${product.category}`}>
      <button className="preview-button" type="button" onClick={() => onOpen(product.id)}>
        {product.preview_url ? (
          <span className="preview-image-frame">
            <img
              className="preview-image"
              src={product.preview_url}
              alt={`Превʼю: ${product.title}`}
              loading="lazy"
              decoding="async"
            />
          </span>
        ) : (
          <span className="preview-placeholder">
            <span className="preview-label">{getCategoryLabel(product.category)}</span>
            <span className="preview-placeholder-icon">
              <FileText aria-hidden="true" size={24} />
            </span>
            <span className="preview-placeholder-text">
              <span>
                {getLanguageLabel(product.language)} · {getLevelLabel(product.level)}
              </span>
              <strong>{getCategoryLabel(product.category)}</strong>
            </span>
          </span>
        )}
      </button>
      <div className="product-card-body">
        <button className="product-title-button" type="button" onClick={() => onOpen(product.id)}>
          {product.title}
        </button>
        <div className="product-card-footer">
          <strong className="product-price">{formatPrice(product.price_amount, product.currency)}</strong>
          <button
            type="button"
            className={`icon-button favorite-button ${isFavorite ? "is-saved" : ""}`}
            aria-label={isFavorite ? "Прибрати зі збереженого" : "Зберегти матеріал"}
            aria-pressed={isFavorite}
            onClick={() => onToggleFavorite(product.id)}
          >
            <Heart aria-hidden="true" size={18} fill={isFavorite ? "currentColor" : "none"} />
          </button>
        </div>
      </div>
    </article>
  );
}
