import { ArrowRight, BookOpen, CheckCircle2, MessageCircle, Search, Store } from "lucide-react";

const categories = [
  { label: "Картки для говоріння", value: "speaking_cards" },
  { label: "Робочі аркуші", value: "worksheet" },
  { label: "Тести", value: "test" },
  { label: "Презентації", value: "presentation" },
  { label: "Ігри", value: "game" },
];

type HomePageProps = {
  onOpenCatalog: () => void;
  onOpenSeller: () => void;
  onCategorySelect: (category: string) => void;
};

export function HomePage({ onOpenCatalog, onOpenSeller, onCategorySelect }: HomePageProps) {
  return (
    <main id="main-content" className="app-shell" tabIndex={-1}>
      <section className="hero hero-simple">
        <div className="hero-copy">
          <p className="eyebrow">Каталог матеріалів для викладачів</p>
          <h1>ТічерМаркет</h1>
          <p className="lead">
            Готові матеріали для уроків. Обирайте, зберігайте й пишіть автору в Telegram.
          </p>
          <div className="actions">
            <button type="button" onClick={onOpenCatalog}>
              <Search aria-hidden="true" size={18} />
              Знайти матеріали
            </button>
          </div>
        </div>
      </section>

      <section className="section category-section">
        <div className="section-heading">
          <BookOpen aria-hidden="true" size={20} />
          <h2>Популярні категорії</h2>
        </div>
        <div className="category-grid">
          {categories.map((category) => (
            <button
              key={category.value}
              type="button"
              className="category-chip"
              onClick={() => onCategorySelect(category.value)}
            >
              {category.label}
              <ArrowRight aria-hidden="true" size={16} />
            </button>
          ))}
        </div>
      </section>

      <section className="section testing-guide" aria-labelledby="testing-guide-title">
        <div className="section-heading">
          <CheckCircle2 aria-hidden="true" size={20} />
          <h2 id="testing-guide-title">Як протестувати</h2>
        </div>
        <div className="testing-guide-grid">
          <article>
            <span className="testing-guide-icon" aria-hidden="true">
              <Search size={20} />
            </span>
            <h3>Знайти матеріал</h3>
            <ol>
              <li>Відкрийте каталог.</li>
              <li>Спробуйте пошук, фільтри й сторінку матеріалу.</li>
              <li>Натисніть “Зберегти”.</li>
            </ol>
            <button type="button" className="text-button" onClick={onOpenCatalog}>
              До каталогу
              <ArrowRight aria-hidden="true" size={16} />
            </button>
          </article>
          <article>
            <span className="testing-guide-icon" aria-hidden="true">
              <MessageCircle size={20} />
            </span>
            <h3>Написати автору</h3>
            <ol>
              <li>Відкрийте будь-який матеріал.</li>
              <li>Натисніть “Написати автору”.</li>
              <li>Перевірте, що відкрився Telegram автора.</li>
            </ol>
          </article>
          <article>
            <span className="testing-guide-icon" aria-hidden="true">
              <Store size={20} />
            </span>
            <h3>Додати матеріал</h3>
            <ol>
              <li>Відкрийте кабінет автора.</li>
              <li>Створіть профіль і додайте файл з превʼю через бота.</li>
              <li>Надішліть матеріал на модерацію.</li>
            </ol>
            <button type="button" className="text-button" onClick={onOpenSeller}>
              Кабінет автора
              <ArrowRight aria-hidden="true" size={16} />
            </button>
          </article>
        </div>
      </section>

      <section className="section home-author-card">
        <span className="home-author-icon" aria-hidden="true">
          <Store size={22} />
        </span>
        <div>
          <h2>Поширюєте власні матеріали?</h2>
          <p>Відкрийте кабінет автора, щоб додавати матеріали, проходити модерацію й відповідати покупцям напряму.</p>
        </div>
        <button type="button" className="secondary" onClick={onOpenSeller}>
          Кабінет автора
          <ArrowRight aria-hidden="true" size={16} />
        </button>
      </section>
    </main>
  );
}
