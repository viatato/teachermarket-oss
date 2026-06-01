import { useEffect, useMemo, useState, type KeyboardEvent } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, RotateCcw, Search, SlidersHorizontal, X } from "lucide-react";

import { demoProducts, fetchProducts } from "../api/products";
import { ProductCard } from "../components/ProductCard";
import type { CatalogFilters } from "../types/products";

type CatalogPageProps = {
  filters: CatalogFilters;
  favoriteIds: string[];
  isFavoritesSyncing: boolean;
  onFiltersChange: (filters: CatalogFilters) => void;
  onOpenProduct: (productId: string) => void;
  onToggleFavorite: (productId: string) => void;
};

const languages = ["", "english", "german", "polish", "ukrainian"];
const categories = ["", "worksheet", "speaking_cards", "test", "presentation", "game", "template"];
const levels = ["", "a1", "a2", "b1", "b2", "kids", "teens", "mixed"];
const audiences = ["", "kids", "teens", "adults", "business", "teachers"];
const sortOptions = [
  { value: "new", label: "Нові" },
  { value: "cheap", label: "Дешевші" },
  { value: "expensive", label: "Дорожчі" },
];
const sortValues = sortOptions.map((option) => option.value);
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

const languageOptions: Record<string, string> = {
  english: "Англійська",
  german: "Німецька",
  polish: "Польська",
  ukrainian: "Українська",
};

const categoryOptions: Record<string, string> = {
  worksheet: "Робочі аркуші",
  speaking_cards: "Картки для говоріння",
  test: "Тести",
  presentation: "Презентації",
  game: "Ігри",
  template: "Шаблони",
};

const levelOptions: Record<string, string> = {
  a1: "A1",
  a2: "A2",
  b1: "B1",
  b2: "B2",
  kids: "Діти",
  teens: "Підлітки",
  mixed: "Змішаний",
};

const audienceOptions: Record<string, string> = {
  kids: "Діти",
  teens: "Підлітки",
  adults: "Дорослі",
  business: "Business",
  teachers: "Викладачі",
};

export function CatalogPage({
  filters,
  favoriteIds,
  isFavoritesSyncing,
  onFiltersChange,
  onOpenProduct,
  onToggleFavorite,
}: CatalogPageProps) {
  const [searchInput, setSearchInput] = useState(filters.search);
  const [isRefineOpen, setIsRefineOpen] = useState(false);
  const query = useQuery({
    queryKey: ["products", filters],
    queryFn: () => fetchProducts(filters),
    retry: false,
  });

  useEffect(() => {
    setSearchInput(filters.search);
  }, [filters.search]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      if (searchInput !== filters.search) {
        onFiltersChange({ ...filters, search: searchInput, page: "1" });
      }
    }, 300);
    return () => window.clearTimeout(timer);
  }, [filters, filters.search, onFiltersChange, searchInput]);

  const products = query.data ?? demoProducts;
  const isRealData = Boolean(query.data);
  const filteredDemoItems = useMemo(() => {
    if (query.data) {
      return products.items;
    }
    return products.items.filter((product) => {
      const searchMatch =
        !filters.search || product.title.toLowerCase().includes(filters.search.toLowerCase());
      const languageMatch = !filters.language || product.language === filters.language;
      const levelMatch = !filters.level || product.level === filters.level;
      const categoryMatch = !filters.category || product.category === filters.category;
      const audienceMatch = !filters.audience || product.audience === filters.audience;
      const minPriceMatch = !filters.min_price || product.price_amount >= Number(filters.min_price) * 100;
      const maxPriceMatch = !filters.max_price || product.price_amount <= Number(filters.max_price) * 100;
      return searchMatch && languageMatch && levelMatch && categoryMatch && audienceMatch && minPriceMatch && maxPriceMatch;
    });
  }, [filters, products.items, query.data]);
  const resultCount = query.data?.total ?? filteredDemoItems.length;
  const currentPage = Number(filters.page) || 1;
  const totalPages = query.data ? Math.max(1, Math.ceil(query.data.total / query.data.limit)) : 1;
  const activeFilters = [
    filters.search ? { key: "search", label: `Пошук: ${filters.search}` } : null,
    filters.language ? { key: "language", label: languageOptions[filters.language] ?? filters.language } : null,
    filters.level ? { key: "level", label: levelOptions[filters.level] ?? filters.level } : null,
    filters.category ? { key: "category", label: categoryOptions[filters.category] ?? filters.category } : null,
    filters.audience ? { key: "audience", label: audienceOptions[filters.audience] ?? filters.audience } : null,
    filters.min_price ? { key: "min_price", label: `Від ${filters.min_price} грн` } : null,
    filters.max_price ? { key: "max_price", label: `До ${filters.max_price} грн` } : null,
  ].filter(Boolean) as Array<{ key: keyof CatalogFilters; label: string }>;
  const hasActiveFilters = activeFilters.length > 0;
  const hasNoResults = filteredDemoItems.length === 0;

  const updateFilter = (key: keyof CatalogFilters, value: string) => {
    if (key === "page") {
      onFiltersChange({ ...filters, page: value });
    } else {
      onFiltersChange({ ...filters, [key]: value, page: "1" });
    }
  };

  const handleSelectKeyDown = (
    event: KeyboardEvent<HTMLSelectElement>,
    key: keyof CatalogFilters,
    values: string[],
  ) => {
    if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) {
      return;
    }
    event.preventDefault();
    const currentIndex = Math.max(0, values.indexOf(event.currentTarget.value));
    let nextIndex = currentIndex;
    if (event.key === "Home") {
      nextIndex = 0;
    } else if (event.key === "End") {
      nextIndex = values.length - 1;
    } else if (event.key === "ArrowDown") {
      nextIndex = Math.min(values.length - 1, currentIndex + 1);
    } else {
      nextIndex = Math.max(0, currentIndex - 1);
    }
    updateFilter(key, values[nextIndex]);
  };

  const clearFilter = (key: keyof CatalogFilters) => {
    if (key === "search") {
      setSearchInput("");
    }
    onFiltersChange({ ...filters, [key]: "", page: "1" });
  };

  const resetFilters = () => {
    setSearchInput("");
    onFiltersChange({ ...emptyFilters });
  };

  return (
    <main id="main-content" className="app-shell" tabIndex={-1}>
      <section className="page-header catalog-header">
        <p className="eyebrow">Каталог</p>
        <h1>Матеріали для уроків</h1>
        <p className="lead">Фільтруйте за мовою, рівнем і типом матеріалу, а далі пишіть автору напряму.</p>
      </section>

      <section className="catalog-search" aria-label="Пошук матеріалів">
        <Search aria-hidden="true" size={19} />
        <input
          aria-label="Пошук матеріалів"
          placeholder="Назва матеріалу або тема уроку"
          value={searchInput}
          onChange={(event) => setSearchInput(event.target.value)}
        />
      </section>

      <section className="quick-filters" aria-label="Швидкі фільтри">
        <div className="quick-filter-heading">
          <SlidersHorizontal aria-hidden="true" size={18} />
          <span>Фільтри</span>
        </div>
        <div className="mobile-category-grid" aria-label="Тип матеріалу">
          {categories.map((category) => (
            <button
              key={category || "all-categories"}
              type="button"
              className={filters.category === category ? "is-active" : ""}
              onClick={() => updateFilter("category", category)}
            >
              {categoryOptions[category] || "Усі"}
            </button>
          ))}
        </div>
        <button
          type="button"
          className={`refine-toggle ${isRefineOpen ? "is-open" : ""}`}
          aria-expanded={isRefineOpen}
          onClick={() => setIsRefineOpen((current) => !current)}
        >
          Уточнити мову, рівень і порядок
          <ChevronDown aria-hidden="true" size={17} />
        </button>
        {isRefineOpen ? (
          <div className="refine-panel">
            <FilterButtonGroup
              label="Мова"
              options={languages.map((language) => ({
                value: language,
                label: languageOptions[language] || "Усі",
              }))}
              value={filters.language}
              onChange={(value) => updateFilter("language", value)}
            />
            <FilterButtonGroup
              label="Рівень"
              options={levels.map((level) => ({
                value: level,
                label: levelOptions[level] || "Усі",
              }))}
              value={filters.level}
              onChange={(value) => updateFilter("level", value)}
            />
            <FilterButtonGroup
              label="Аудиторія"
              options={audiences.map((audience) => ({
                value: audience,
                label: audienceOptions[audience] || "Усі",
              }))}
              value={filters.audience}
              onChange={(value) => updateFilter("audience", value)}
            />
            <div className="price-filter-row">
              <label>
                Від, грн
                <input
                  inputMode="numeric"
                  value={filters.min_price}
                  onChange={(event) => updateFilter("min_price", event.target.value.replace(/\D/g, ""))}
                />
              </label>
              <label>
                До, грн
                <input
                  inputMode="numeric"
                  value={filters.max_price}
                  onChange={(event) => updateFilter("max_price", event.target.value.replace(/\D/g, ""))}
                />
              </label>
            </div>
            <FilterButtonGroup
              label="Порядок"
              options={sortOptions}
              value={filters.sort}
              onChange={(value) => updateFilter("sort", value)}
            />
          </div>
        ) : null}
      </section>

      <section className="filters-panel desktop-filters" aria-label="Додаткові фільтри">
        <select
          aria-label="Мова"
          value={filters.language}
          onChange={(event) => updateFilter("language", event.target.value)}
          onKeyDown={(event) => handleSelectKeyDown(event, "language", languages)}
        >
          {languages.map((language) => (
            <option key={language} value={language}>
              {languageOptions[language] || "Усі мови"}
            </option>
          ))}
        </select>
        <select
          aria-label="Аудиторія"
          value={filters.audience}
          onChange={(event) => updateFilter("audience", event.target.value)}
          onKeyDown={(event) => handleSelectKeyDown(event, "audience", audiences)}
        >
          {audiences.map((audience) => (
            <option key={audience} value={audience}>
              {audienceOptions[audience] || "Усі аудиторії"}
            </option>
          ))}
        </select>
        <input
          aria-label="Мінімальна ціна"
          inputMode="numeric"
          placeholder="Від, грн"
          value={filters.min_price}
          onChange={(event) => updateFilter("min_price", event.target.value.replace(/\D/g, ""))}
        />
        <input
          aria-label="Максимальна ціна"
          inputMode="numeric"
          placeholder="До, грн"
          value={filters.max_price}
          onChange={(event) => updateFilter("max_price", event.target.value.replace(/\D/g, ""))}
        />
        <select
          aria-label="Рівень"
          value={filters.level}
          onChange={(event) => updateFilter("level", event.target.value)}
          onKeyDown={(event) => handleSelectKeyDown(event, "level", levels)}
        >
          {levels.map((level) => (
            <option key={level} value={level}>
              {levelOptions[level] || "Усі рівні"}
            </option>
          ))}
        </select>
        <select
          aria-label="Тип матеріалу"
          value={filters.category}
          onChange={(event) => updateFilter("category", event.target.value)}
          onKeyDown={(event) => handleSelectKeyDown(event, "category", categories)}
        >
          {categories.map((category) => (
            <option key={category} value={category}>
              {categoryOptions[category] || "Усі типи"}
            </option>
          ))}
        </select>
        <select
          aria-label="Сортування"
          value={filters.sort}
          onChange={(event) => updateFilter("sort", event.target.value)}
          onKeyDown={(event) => handleSelectKeyDown(event, "sort", sortValues)}
        >
          {sortOptions.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </section>

      <section className="catalog-summary" aria-live="polite">
        <div>
          <strong>
            {resultCount} {resultCount === 1 ? "матеріал" : "матеріалів"}
          </strong>
          <span>{isRealData ? "Реальні дані каталогу" : "Демо-приклади для перегляду інтерфейсу"}</span>
        </div>
        {hasActiveFilters && !hasNoResults ? (
          <button type="button" className="text-button filters-reset" onClick={resetFilters}>
            <RotateCcw aria-hidden="true" size={15} />
            Скинути
          </button>
        ) : null}
      </section>

      {hasActiveFilters ? (
        <section className="active-filter-chips" aria-label="Активні фільтри">
          {activeFilters.map((filter) => (
            <button key={filter.key} type="button" onClick={() => clearFilter(filter.key)}>
              {filter.label}
              <X aria-hidden="true" size={14} />
            </button>
          ))}
        </section>
      ) : null}

      {!isRealData && !query.isLoading ? (
        <div className="demo-banner">
          <span>Демо-режим</span>
          <p>API поки недоступний, тому показуємо приклади матеріалів.</p>
        </div>
      ) : null}
      {query.isLoading ? <p className="notice subtle-notice">Оновлюємо каталог...</p> : null}
      {isFavoritesSyncing ? <p className="notice subtle-notice">Оновлюємо збережене...</p> : null}

      {hasNoResults ? (
        <section className="empty-state">
          <Search aria-hidden="true" className="empty-icon" size={28} />
          <strong>Матеріалів не знайдено</strong>
          <p>Спробуйте змінити пошук або скинути фільтри.</p>
          {hasActiveFilters ? (
            <button type="button" onClick={resetFilters}>
              <RotateCcw aria-hidden="true" size={17} />
              Скинути фільтри
            </button>
          ) : null}
        </section>
      ) : (
        <section className="product-grid">
          {filteredDemoItems.map((product) => (
            <ProductCard
              key={product.id}
              product={product}
              isFavorite={favoriteIds.includes(product.id)}
              onOpen={onOpenProduct}
              onToggleFavorite={onToggleFavorite}
            />
          ))}
        </section>
      )}

      {isRealData && totalPages > 1 ? (
        <nav className="catalog-pagination" aria-label="Сторінки каталогу">
          <button
            type="button"
            disabled={currentPage <= 1}
            onClick={() => updateFilter("page", String(currentPage - 1))}
            aria-label="Попередня сторінка"
          >
            ← Назад
          </button>
          <span>
            Сторінка {currentPage} з {totalPages}
          </span>
          <button
            type="button"
            disabled={currentPage >= totalPages}
            onClick={() => updateFilter("page", String(currentPage + 1))}
            aria-label="Наступна сторінка"
          >
            Далі →
          </button>
        </nav>
      ) : null}
    </main>
  );
}

function FilterButtonGroup({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: Array<{ value: string; label: string }>;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="filter-button-group">
      <span>{label}</span>
      <div>
        {options.map((option) => (
          <button
            key={option.value || `${label}-all`}
            type="button"
            className={value === option.value ? "is-active" : ""}
            onClick={() => onChange(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}
