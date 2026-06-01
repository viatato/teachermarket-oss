import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { ArrowLeft, ChevronLeft, ChevronRight, Flag, Heart, MessageCircle, RefreshCw, Share2, Star, UserRound } from "lucide-react";

import {
  createContactRequest,
  createProductReview,
  deleteProductReview,
  fetchProduct,
  fetchProductReviews,
  formatPrice,
  reportProduct,
  trackProductView,
  updateProductReview,
} from "../api/products";
import {
  getAudienceLabel,
  getCategoryLabel,
  getDeliveryLabel,
  getLanguageLabel,
  getLevelLabel,
} from "../components/ProductCard";
import type { RecentlyViewedProduct } from "../types/products";

type ProductPageProps = {
  productId: string;
  isFavorite: boolean;
  accessToken?: string | null;
  currentUserId?: string | null;
  onBack: () => void;
  onToggleFavorite: (productId: string) => void;
};

export function ProductPage({ productId, isFavorite, accessToken, currentUserId, onBack, onToggleFavorite }: ProductPageProps) {
  const [isContacting, setIsContacting] = useState(false);
  const [contactError, setContactError] = useState<string | null>(null);
  const [contactSuccess, setContactSuccess] = useState(false);
  const [isContactModalOpen, setIsContactModalOpen] = useState(false);
  const [contactMessage, setContactMessage] = useState("");
  const [activePreviewIndex, setActivePreviewIndex] = useState(0);
  const [shareFeedback, setShareFeedback] = useState<string | null>(null);
  const [reviewText, setReviewText] = useState("");
  const [reviewRating, setReviewRating] = useState(5);
  const [reportReason, setReportReason] = useState("");
  const [reportFeedback, setReportFeedback] = useState<string | null>(null);
  const queryClient = useQueryClient();
  const query = useQuery({
    queryKey: ["product", productId],
    queryFn: () => fetchProduct(productId),
    retry: false,
  });
  const reviewsQuery = useQuery({
    queryKey: ["product-reviews", productId],
    queryFn: () => fetchProductReviews(productId),
    retry: false,
  });
  const ownReview = reviewsQuery.data?.items.find((review) => review.buyer_id === currentUserId);
  const reviewMutation = useMutation({
    mutationFn: () => {
      if (!accessToken) {
        throw new Error("Потрібна авторизація.");
      }
      if (ownReview) {
        return updateProductReview(ownReview.id, accessToken, reviewRating, reviewText);
      }
      return createProductReview(productId, accessToken, reviewRating, reviewText);
    },
    onSuccess: async () => {
      if (!ownReview) {
        setReviewText("");
        setReviewRating(5);
      }
      await queryClient.invalidateQueries({ queryKey: ["product-reviews", productId] });
    },
  });
  const deleteReviewMutation = useMutation({
    mutationFn: () => {
      if (!accessToken || !ownReview) {
        throw new Error("Потрібна авторизація.");
      }
      return deleteProductReview(ownReview.id, accessToken);
    },
    onSuccess: async () => {
      setReviewText("");
      setReviewRating(5);
      await queryClient.invalidateQueries({ queryKey: ["product-reviews", productId] });
    },
  });
  const reportMutation = useMutation({
    mutationFn: () => {
      if (!accessToken) {
        throw new Error("Потрібна авторизація.");
      }
      return reportProduct(productId, accessToken, reportReason);
    },
    onSuccess: () => {
      setReportReason("");
      setReportFeedback("Скаргу надіслано на перевірку.");
      window.setTimeout(() => setReportFeedback(null), 3500);
    },
  });

  useEffect(() => {
    if (!query.data || productId.startsWith("demo-")) {
      return;
    }
    const key = "teachermarket_recently_viewed";
    const existing = JSON.parse(window.localStorage.getItem(key) || "[]") as unknown[];
    const current = existing.filter((item): item is RecentlyViewedProduct => {
      return Boolean(item && typeof item === "object" && "id" in item && "title" in item);
    });
    const snapshot: RecentlyViewedProduct = {
      id: query.data.id,
      title: query.data.title,
      category: query.data.category,
      price_amount: query.data.price_amount,
      currency: query.data.currency,
      preview_url: query.data.preview_urls?.[0] ?? null,
      seller: query.data.seller,
      viewed_at: new Date().toISOString(),
    };
    const next = [snapshot, ...current.filter((item) => item.id !== productId)].slice(0, 12);
    window.localStorage.setItem(key, JSON.stringify(next));
  }, [productId, query.data]);

  useEffect(() => {
    if (!query.data || productId.startsWith("demo-")) {
      return;
    }
    const key = "teachermarket_view_tracking";
    const today = new Date().toISOString().slice(0, 10);
    const current = JSON.parse(window.localStorage.getItem(key) || "{}") as Record<string, string>;
    if (current[productId] === today) {
      return;
    }
    trackProductView(productId, accessToken)
      .then(() => {
        window.localStorage.setItem(key, JSON.stringify({ ...current, [productId]: today }));
      })
      .catch(() => undefined);
  }, [accessToken, productId, query.data]);

  useEffect(() => {
    if (!ownReview) {
      return;
    }
    setReviewRating(ownReview.rating);
    setReviewText(ownReview.text ?? "");
  }, [ownReview?.id]);

  if (query.isLoading) {
    return (
      <main id="main-content" className="app-shell" tabIndex={-1}>
        <button className="text-button" type="button" onClick={onBack}>
          <ArrowLeft aria-hidden="true" size={17} />
          Назад
        </button>
        <section className="product-detail-skeleton" aria-label="Завантажуємо матеріал">
          <div className="skeleton-preview" />
          <div className="skeleton-content">
            <div className="skeleton-line skeleton-line-short" />
            <div className="skeleton-line" />
            <div className="skeleton-line" />
            <div className="skeleton-line skeleton-line-short" />
          </div>
        </section>
      </main>
    );
  }

  if (query.isError || !query.data) {
    return (
      <main id="main-content" className="app-shell" tabIndex={-1}>
        <button className="text-button" type="button" onClick={onBack}>
          <ArrowLeft aria-hidden="true" size={17} />
          Назад
        </button>
        <section className="error-state">
          <strong>Не вдалося завантажити матеріал</strong>
          <p>Перевірте зʼєднання і спробуйте ще раз.</p>
          <button type="button" onClick={() => query.refetch()}>
            <RefreshCw aria-hidden="true" size={17} />
            Спробувати ще
          </button>
        </section>
      </main>
    );
  }

  const product = query.data;
  const previewUrls = product.preview_urls?.filter(Boolean) ?? [];
  const displayDate = product.published_at ?? product.created_at;
  const derivedTags = [
    getCategoryLabel(product.category),
    getLanguageLabel(product.language),
    product.level ? getLevelLabel(product.level) : null,
    product.audience ? getAudienceLabel(product.audience) : null,
  ].filter(Boolean) as string[];
  const telegramUrl = product.seller.contact_username
    ? `https://t.me/${product.seller.contact_username}`
    : undefined;

  const openTelegram = (url: string) => {
    window.open(url, "_blank", "noopener,noreferrer");
  };

  const submitContactRequest = async () => {
    setContactError(null);
    setContactSuccess(false);
    if (!accessToken) {
      if (telegramUrl) {
        setContactSuccess(true);
        openTelegram(telegramUrl);
        window.setTimeout(() => setContactSuccess(false), 4500);
      }
      return;
    }

    setIsContacting(true);
    try {
      const contactRequest = await createContactRequest(product.id, accessToken, contactMessage.trim());
      setContactSuccess(true);
      setIsContactModalOpen(false);
      setContactMessage("");
      openTelegram(contactRequest.seller_telegram_url);
      window.setTimeout(() => setContactSuccess(false), 4500);
    } catch {
      setContactError("Не вдалося створити звернення. Спробуйте ще раз.");
    } finally {
      setIsContacting(false);
    }
  };

  const handleContactRequest = async () => {
    if (!accessToken) {
      await submitContactRequest();
      return;
    }
    setIsContactModalOpen(true);
  };

  const handleShare = async () => {
    const shareText = `${product.title} — ${formatPrice(product.price_amount, product.currency)} у ТічерМаркет`;
    const shareUrl = window.location.href;
    setShareFeedback(null);
    try {
      if (navigator.share) {
        await navigator.share({
          title: product.title,
          text: shareText,
          url: shareUrl,
        });
        return;
      }
      await navigator.clipboard.writeText(`${shareText}\n${shareUrl}`);
      setShareFeedback("Посилання скопійовано.");
      window.setTimeout(() => setShareFeedback(null), 3000);
    } catch {
      setShareFeedback("Не вдалося поділитися. Спробуйте ще раз.");
      window.setTimeout(() => setShareFeedback(null), 3000);
    }
  };

  return (
    <main id="main-content" className="app-shell" tabIndex={-1}>
      <button className="text-button" type="button" onClick={onBack}>
        <ArrowLeft aria-hidden="true" size={17} />
        Назад
      </button>
      <section className="product-detail">
        <div className={`detail-preview detail-preview-${product.category}`}>
          {previewUrls.length > 0 ? (
            <div className="detail-preview-gallery">
              {previewUrls.length > 1 ? (
                <button
                  type="button"
                  className="gallery-nav gallery-prev"
                  aria-label="Попереднє превʼю"
                  onClick={() => setActivePreviewIndex((current) => (current === 0 ? previewUrls.length - 1 : current - 1))}
                >
                  <ChevronLeft aria-hidden="true" size={18} />
                </button>
              ) : null}
              <img
                src={previewUrls[activePreviewIndex] ?? previewUrls[0]}
                alt={`Превʼю ${activePreviewIndex + 1}: ${product.title}`}
                loading="eager"
                decoding="async"
              />
              <span>{activePreviewIndex + 1}/{previewUrls.length}</span>
              {previewUrls.length > 1 ? (
                <button
                  type="button"
                  className="gallery-nav gallery-next"
                  aria-label="Наступне превʼю"
                  onClick={() => setActivePreviewIndex((current) => (current + 1) % previewUrls.length)}
                >
                  <ChevronRight aria-hidden="true" size={18} />
                </button>
              ) : null}
            </div>
          ) : (
            <>
              <span className="preview-label">{getCategoryLabel(product.category)}</span>
              <div className="detail-paper">
                <span>{getLanguageLabel(product.language)} · {getLevelLabel(product.level)}</span>
                <strong>{product.title}</strong>
                <i></i>
                <i></i>
                <i className="short"></i>
              </div>
            </>
          )}
        </div>
        <div className="detail-content">
          <p className="eyebrow">Матеріал</p>
          <h1>{product.title}</h1>
          <div className="product-purchase-panel">
            <strong className="detail-price">{formatPrice(product.price_amount, product.currency)}</strong>
            <p className="purchase-note">
              Натисніть CTA, і ми відкриємо чат з автором у Telegram.
            </p>
            <div className="actions detail-actions">
              <button
                type="button"
                onClick={handleContactRequest}
                disabled={!telegramUrl || isContacting}
              >
                <MessageCircle aria-hidden="true" size={18} />
                {isContacting ? "Відкриваємо..." : "Написати автору"}
              </button>
              <button type="button" className="secondary" onClick={() => onToggleFavorite(product.id)}>
                <Heart aria-hidden="true" size={18} fill={isFavorite ? "currentColor" : "none"} />
                {isFavorite ? "Збережено" : "Зберегти"}
              </button>
              <button type="button" className="secondary" onClick={handleShare}>
                <Share2 aria-hidden="true" size={18} />
                Поділитися
              </button>
            </div>
            {!telegramUrl ? <p className="notice subtle-notice">Автор ще не додав Telegram для звʼязку.</p> : null}
            {contactSuccess ? (
              <p className="success-message">Звернення створено. Зараз відкриється Telegram.</p>
            ) : null}
            {contactError ? <p className="notice">{contactError}</p> : null}
            {shareFeedback ? <p className="success-message">{shareFeedback}</p> : null}
          </div>
          <p className="lead">{product.description}</p>
          {displayDate || derivedTags.length > 0 ? (
            <div className="product-meta-info">
              {displayDate ? (
                <span className="product-meta-item">
                  <time dateTime={displayDate}>
                    {new Date(displayDate).toLocaleDateString("uk-UA", {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                    })}
                  </time>
                </span>
              ) : null}
              {derivedTags.length > 0 ? (
                <div className="product-tags">
                  {derivedTags.map((tag) => (
                    <span key={tag} className="product-tag">{tag}</span>
                  ))}
                </div>
              ) : null}
            </div>
          ) : null}
          <div className="detail-meta">
            <span>{getLanguageLabel(product.language)}</span>
            <span>{getLevelLabel(product.level)}</span>
            <span>{getAudienceLabel(product.audience)}</span>
          </div>
          <section className="seller-info" aria-label="Інформація про автора">
            <span className="seller-avatar" aria-hidden="true">
              <UserRound size={20} />
            </span>
            <div>
              <strong>{product.seller.display_name}</strong>
              <p>{product.seller.bio || "Автор матеріалу відповість на питання й передасть доступ після звернення."}</p>
            </div>
          </section>
          <p className="delivery-note">
            Доставка: {getDeliveryLabel(product.delivery_method).toLowerCase()}. Деталі й доступ узгоджуються в чаті з автором.
          </p>
          <section className="reviews-panel" aria-label="Відгуки">
            <h2>Відгуки</h2>
            <p className="muted">
              {reviewsQuery.data?.total
                ? `Середня оцінка: ${reviewsQuery.data.average_rating?.toFixed(1)} / 5`
                : "Відгуків поки немає."}
            </p>
            <div className="reviews-list">
              {reviewsQuery.data?.items.map((review) => (
                <article key={review.id} className="review-item">
                  <strong>{review.buyer_display_name ?? "Покупець"}</strong>
                  <span>{"★".repeat(review.rating)}</span>
                  {review.text ? <p>{review.text}</p> : null}
                </article>
              ))}
            </div>
            {accessToken ? (
              <form
                className="review-form"
                onSubmit={(event) => {
                  event.preventDefault();
                  reviewMutation.mutate();
                }}
              >
                <label>
                  Оцінка
                  <select value={reviewRating} onChange={(event) => setReviewRating(Number(event.target.value))}>
                    {[5, 4, 3, 2, 1].map((rating) => (
                      <option key={rating} value={rating}>{rating}</option>
                    ))}
                  </select>
                </label>
                <textarea value={reviewText} maxLength={2000} onChange={(event) => setReviewText(event.target.value)} placeholder="Короткий відгук" />
                <button type="submit" disabled={reviewMutation.isPending}>
                  <Star aria-hidden="true" size={17} />
                  {ownReview ? "Оновити відгук" : "Залишити відгук"}
                </button>
                {ownReview ? (
                  <button type="button" className="secondary" disabled={deleteReviewMutation.isPending} onClick={() => deleteReviewMutation.mutate()}>
                    Видалити
                  </button>
                ) : null}
                {reviewMutation.isError ? <p className="notice">{ownReview ? "Не вдалося оновити відгук." : "Ви вже залишили відгук або відгук не вдалося зберегти."}</p> : null}
                {deleteReviewMutation.isError ? <p className="notice">Не вдалося видалити відгук.</p> : null}
              </form>
            ) : null}
          </section>
          {accessToken ? (
            <form
              className="report-form"
              onSubmit={(event) => {
                event.preventDefault();
                if (reportReason.trim().length >= 3) {
                  reportMutation.mutate();
                }
              }}
            >
              <label>
                Скарга на матеріал
                <input value={reportReason} maxLength={2000} onChange={(event) => setReportReason(event.target.value)} placeholder="Причина" />
              </label>
              <button type="submit" className="secondary" disabled={reportMutation.isPending || reportReason.trim().length < 3}>
                <Flag aria-hidden="true" size={17} />
                Надіслати
              </button>
              {reportFeedback ? <p className="success-message">{reportFeedback}</p> : null}
            </form>
          ) : null}
        </div>
      </section>
      {isContactModalOpen ? (
        <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Повідомлення автору">
          <form
            className="contact-modal"
            onSubmit={(event) => {
              event.preventDefault();
              submitContactRequest();
            }}
          >
            <h2>Написати автору</h2>
            <textarea
              maxLength={1000}
              value={contactMessage}
              onChange={(event) => setContactMessage(event.target.value)}
              placeholder="Напишіть коротке повідомлення автору (необовʼязково)"
            />
            <div className="modal-actions">
              <button type="button" className="secondary" onClick={() => setIsContactModalOpen(false)}>Скасувати</button>
              <button type="submit" disabled={isContacting}>
                <MessageCircle aria-hidden="true" size={17} />
                Відкрити Telegram
              </button>
            </div>
          </form>
        </div>
      ) : null}
    </main>
  );
}
