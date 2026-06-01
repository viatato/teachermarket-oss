# ТічерМаркет — MVP-спецификация для вайбкодинга

**Продукт:** отдельный Telegram-бот + Telegram Mini App  
**Идея:** каталог-витрина учебных материалов для преподавателей: розробки уроків, worksheets, тести, speaking cards, презентації, шаблони.  
**MVP-цель:** быстро проверить спрос: готовы ли преподаватели размещать материалы и платить за подписку на сервис, который связывает их с другими преподавателями.

---

## 0. Коротко: что строим

Строим не “огромный Etsy”, а **курируемый каталог материалов от преподавателей**.

ТічерМаркет не проводит сделки между преподавателями и не выплачивает деньги авторам. Сервис помогает авторам показать материалы и получить обращения от покупателей, а монетизация сервиса — подписка автора за размещение и продвижение.

В MVP есть 2 интерфейса:

1. **Telegram Bot**
   - онбординг;
   - быстрые кнопки;
   - загрузка материалов продавцом;
   - модерация админом;
   - уведомления;
   - управление подпиской автора;
   - обращения к авторам;
   - “Кабінет автора”.

2. **Telegram Mini App**
   - красивый каталог;
   - поиск;
   - фильтры;
   - карточки материалов;
   - превью;
   - связь с автором;
   - сохраненные материалы;
   - кабинет автора в минимальном виде.

Оба интерфейса работают через **один общий backend** и **одну базу данных**.

---

## 1. MVP scope

### 1.1. Для покупателя / преподавателя, который ищет материал

Обязательно в MVP:

- открыть Mini App из бота;
- просматривать каталог;
- фильтровать материалы по языку / уровню / типу / аудитории / цене;
- открывать карточку товара;
- смотреть превью;
- видеть условия автора: цена, формат, что внутри;
- связаться с автором через Telegram;
- сохранить материал в избранное.

Не обязательно в первой версии:

- корзина;
- рекомендации;
- сложный рейтинг;
- реферальная система;
- встроенная покупка материалов;
- раздел покупок внутри платформы;
- авто-выдача файлов после оплаты;
- промокоды;
- сложная система возвратов.

### 1.2. Для продавца

Обязательно в MVP:

- стать автором / продавцом;
- заполнить профиль автора;
- добавить материал через пошаговый сценарий в боте;
- загрузить основной файл до лимита сервиса или указать способ передачи большого файла;
- загрузить 1–3 превью;
- отправить материал на модерацию;
- видеть свои материалы и их статусы;
- видеть обращения по своим материалам;
- видеть статус подписки;
- оплатить или продлить подписку на сервис.

Не обязательно в первой версии:

- встроенные продажи материалов;
- балансы авторов;
- выплаты авторам;
- сложная аналитика;
- редактирование файлов после публикации без повторной модерации;
- массовая загрузка товаров;
- купоны автора.

### 1.3. Для админа

Обязательно в MVP:

- видеть материалы на модерации;
- открыть файл и превью;
- одобрить материал;
- отклонить материал;
- попросить правки;
- скрыть опубликованный материал;
- видеть активные подписки авторов;
- вручную активировать/продлить подписку при необходимости;
- видеть обращения к материалам.

Не обязательно в первой версии:

- большая web-admin;
- сложные роли модераторов;
- система арбитражей;
- автоматическое распознавание плагиата.

---

## 2. Архитектура

### 2.1. Общая схема

```text
User
 │
 ├── Telegram Bot ───────────────┐
 │                               │
 └── Telegram Mini App ──────── Backend API ───── PostgreSQL
                                  │
                                  ├── Object Storage
                                  │   ├── private product files
                                  │   └── public/limited preview images
                                  │
                                  ├── Subscription Payment Provider
                                  │   └── webhook → Backend API
                                  │
                                  └── Telegram Bot API
                                      └── notifications + author contact
```

### 2.2. Главный принцип

**Один backend. Одна база. Одна бизнес-логика.**

Плохо:

```text
Bot has own DB
Mini App has own DB
Admin has own DB
```

Хорошо:

```text
Bot → Backend API
Mini App → Backend API
Admin mode → Backend API
Subscription payment webhook → Backend API
```

---

## 3. Рекомендованный стек

### 3.1. Backend

Рекомендованный вариант:

```text
Python
FastAPI
SQLAlchemy 2.x
Alembic
Pydantic
PostgreSQL
```

Почему:

- удобно быстро собирать API;
- хорошо дружит с aiogram;
- легко писать понятную бизнес-логику;
- норм для MVP и дальнейшего роста.

### 3.2. Telegram Bot

```text
Python
aiogram 3.x
Telegram Bot API
Webhook mode for production
Long polling only for local dev
```

### 3.3. Telegram Mini App

```text
React
TypeScript
Vite
Telegram WebApp SDK
TanStack Query / React Query
Zustand or simple Context for state
Tailwind CSS
```

Для MVP можно без UI-библиотеки, просто Tailwind + свои компоненты.

### 3.4. Database

```text
PostgreSQL
```

Не использовать SQLite для боевого MVP, потому что будут подписки, платежи за сервис, статусы, конкурентные записи.

### 3.5. Storage

Варианты:

```text
Cloudflare R2
AWS S3
Supabase Storage
DigitalOcean Spaces
```

Для MVP важно:

- приватное хранение основных файлов;
- превью можно хранить отдельно;
- не отдавать основной файл публичной вечной ссылкой.

### 3.6. Subscription payments

Для MVP сделать через абстракцию `PaymentProvider`.

Сначала:

```text
MockPaymentProvider
```

Потом подключить реального провайдера:

```text
WayForPay / LiqPay / Monobank acquiring / Stripe
```

Важно: платежный провайдер нужен только для оплаты подписки автора на сервис. Он не используется для покупки материалов у авторов.

### 3.7. Deploy

Варианты для MVP:

```text
VPS + Docker Compose
Railway
Render
Fly.io
Hetzner VPS
DigitalOcean Droplet
```

Самый контролируемый вариант:

```text
VPS + Docker Compose + nginx/caddy + PostgreSQL backups
```

Самый быстрый для старта:

```text
Railway / Render
```

---

## 4. Монорепозиторий

Рекомендуемая структура проекта:

```text
teachermarket/
  README.md
  .env.example
  docker-compose.yml

  apps/
    api/
      app/
        main.py
        config.py
        database.py
        dependencies.py

        modules/
          auth/
          users/
          sellers/
          products/
          files/
          subscriptions/
          leads/
          admin/
          notifications/

        db/
          migrations/
          models/

        services/
          storage/
          payments/
          telegram/

        tests/

      pyproject.toml
      alembic.ini
      Dockerfile

    bot/
      bot/
        main.py
        config.py
        routers/
          start.py
          buyer.py
          seller.py
          admin.py
        keyboards/
        states/
        api_client.py
      pyproject.toml
      Dockerfile

    webapp/
      src/
        main.tsx
        app/
        pages/
          HomePage.tsx
          CatalogPage.tsx
          ProductPage.tsx
          FavoritesPage.tsx
          SellerDashboardPage.tsx
        components/
        api/
        auth/
        types/
        utils/
      package.json
      vite.config.ts
      Dockerfile

  docs/
    product.md
    api.md
    security.md
```

---

## 5. Переменные окружения

Создать `.env.example`.

```env
# App
APP_ENV=local
APP_NAME=teachermarket
API_BASE_URL=http://localhost:8000
WEBAPP_URL=http://localhost:5173

# Database
DATABASE_URL=postgresql+asyncpg://teachermarket:teachermarket@localhost:5432/teachermarket

# Telegram
TELEGRAM_BOT_TOKEN=123456:replace_me
TELEGRAM_BOT_USERNAME=TeacherMarket_Bot
TELEGRAM_WEBHOOK_SECRET=replace_me
ADMIN_TELEGRAM_IDS=111111111,222222222

# Auth
JWT_SECRET=replace_with_long_random_secret
JWT_EXPIRES_MINUTES=10080

# Storage
STORAGE_PROVIDER=s3
S3_ENDPOINT_URL=https://replace-me
S3_ACCESS_KEY_ID=replace_me
S3_SECRET_ACCESS_KEY=replace_me
S3_BUCKET=teachermarket
S3_REGION=auto

# Files
MAX_PRODUCT_FILE_MB=100
MAX_PREVIEW_IMAGE_MB=10
ALLOWED_PRODUCT_EXTENSIONS=pdf,doc,docx,ppt,pptx,zip
ALLOWED_PREVIEW_EXTENSIONS=jpg,jpeg,png,webp

# Subscription payments
PAYMENT_PROVIDER=mock
PAYMENT_WEBHOOK_SECRET=replace_me
PAYMENT_SUCCESS_URL=https://t.me/TeacherMarket_Bot
PAYMENT_FAILURE_URL=https://t.me/TeacherMarket_Bot

# Subscriptions
DEFAULT_FREE_PRODUCT_LIMIT=3
PRO_AUTHOR_PRODUCT_LIMIT=50

# Security
CORS_ALLOWED_ORIGINS=http://localhost:5173
RATE_LIMIT_ENABLED=true
```

---

## 6. База данных

### 6.1. Основные сущности

- `users`
- `seller_profiles`
- `products`
- `product_previews`
- `files`
- `subscription_plans`
- `subscriptions`
- `subscription_payments`
- `contact_requests`
- `reviews`
- `favorites`
- `audit_logs`

### 6.2. users

```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  telegram_id BIGINT UNIQUE NOT NULL,
  username TEXT,
  first_name TEXT,
  last_name TEXT,
  language_code TEXT,
  is_blocked BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Один пользователь может быть и покупателем/искателем материалов, и автором.

### 6.3. seller_profiles

```sql
CREATE TABLE seller_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  display_name TEXT NOT NULL,
  bio TEXT,
  contact_username TEXT,
  contact_url TEXT,
  status TEXT NOT NULL DEFAULT 'active',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Статусы:

```text
active
blocked
pending_verification
```

### 6.4. files

```sql
CREATE TABLE files (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  owner_id UUID REFERENCES users(id),
  storage_key TEXT NOT NULL,
  original_filename TEXT NOT NULL,
  mime_type TEXT,
  file_size_bytes BIGINT,
  file_kind TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

`file_kind`:

```text
product_file
preview_image
other
```

### 6.5. products

```sql
CREATE TABLE products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  seller_id UUID NOT NULL REFERENCES seller_profiles(id),
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  language TEXT NOT NULL,
  level TEXT,
  category TEXT NOT NULL,
  audience TEXT,
  price_amount INTEGER NOT NULL,
  currency TEXT NOT NULL DEFAULT 'UAH',
  product_file_id UUID REFERENCES files(id),
  status TEXT NOT NULL DEFAULT 'draft',
  rejection_reason TEXT,
  published_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Статусы товара:

```text
draft
pending_moderation
published
rejected
hidden
deleted
```

### 6.6. product_previews

```sql
CREATE TABLE product_previews (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  file_id UUID NOT NULL REFERENCES files(id),
  sort_order INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 6.7. subscription_plans

```sql
CREATE TABLE subscription_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  price_amount INTEGER NOT NULL,
  currency TEXT NOT NULL DEFAULT 'UAH',
  duration_days INTEGER NOT NULL,
  product_limit INTEGER NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Примеры планов:

```text
free
pro_monthly
pro_yearly
```

### 6.8. subscriptions

```sql
CREATE TABLE subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  seller_id UUID NOT NULL REFERENCES seller_profiles(id),
  plan_id UUID NOT NULL REFERENCES subscription_plans(id),
  status TEXT NOT NULL DEFAULT 'active',
  starts_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Статусы подписки:

```text
active
expired
cancelled
trial
```

### 6.9. subscription_payments

```sql
CREATE TABLE subscription_payments (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  seller_id UUID NOT NULL REFERENCES seller_profiles(id),
  subscription_id UUID REFERENCES subscriptions(id),
  plan_id UUID NOT NULL REFERENCES subscription_plans(id),
  provider TEXT NOT NULL,
  provider_payment_id TEXT,
  payment_url TEXT,
  amount INTEGER NOT NULL,
  currency TEXT NOT NULL DEFAULT 'UAH',
  status TEXT NOT NULL DEFAULT 'created',
  raw_payload JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Статусы платежа за подписку:

```text
created
pending
paid
failed
expired
refunded
```

### 6.10. contact_requests

```sql
CREATE TABLE contact_requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  requester_id UUID REFERENCES users(id),
  product_id UUID NOT NULL REFERENCES products(id),
  seller_id UUID NOT NULL REFERENCES seller_profiles(id),
  requester_telegram_id BIGINT,
  requester_username TEXT,
  message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Это не сделка и не заказ. Запись нужна для аналитики: сколько раз покупатели хотели связаться с автором.

### 6.11. reviews

```sql
CREATE TABLE reviews (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id UUID NOT NULL REFERENCES products(id),
  buyer_id UUID NOT NULL REFERENCES users(id),
  rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
  text TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Для MVP можно заложить таблицу, но не выводить отзывы сразу.

### 6.12. favorites

```sql
CREATE TABLE favorites (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES users(id),
  product_id UUID NOT NULL REFERENCES products(id),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(user_id, product_id)
);
```

### 6.13. audit_logs

```sql
CREATE TABLE audit_logs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  actor_user_id UUID REFERENCES users(id),
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id UUID,
  meta JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

Примеры action:

```text
product.submitted
product.approved
product.rejected
subscription.paid
subscription.activated
contact.requested
admin.hide_product
```

---

## 7. Категории и фильтры

### 7.1. Языки

```text
english
german
polish
french
italian
spanish
ukrainian
other
```

UI labels:

```text
🇬🇧 Англійська
🇩🇪 Німецька
🇵🇱 Польська
🇫🇷 Французька
🇮🇹 Італійська
🇪🇸 Іспанська
🇺🇦 Українська
Інше
```

### 7.2. Уровни

```text
a1
a2
b1
b2
c1
c2
kids
teens
adults
exam
business
mixed
```

### 7.3. Типы материалов

```text
lesson_plan
worksheet
speaking_cards
test
presentation
game
homework
template
lead_magnet
mini_course
other
```

### 7.4. Аудитория

```text
kids
teens
adults
business
exam_prep
teachers
mixed
```

---

## 8. Backend modules

### 8.1. auth

Задачи:

- авторизация Mini App через Telegram `initData`;
- создание пользователя при первом входе;
- выдача JWT/session token;
- проверка админских прав.

API:

```http
POST /auth/telegram
GET /auth/me
```

### 8.2. users

Задачи:

- профиль пользователя;
- блокировка пользователя;
- связь с Telegram ID.

API:

```http
GET /users/me
PATCH /users/me
```

### 8.3. sellers

Задачи:

- создать профиль автора;
- обновить профиль;
- посмотреть статус подписки;
- посмотреть обращения по материалам;
- оплатить или продлить подписку.

API:

```http
POST /seller/profile
GET /seller/profile
PATCH /seller/profile
GET /seller/products
GET /seller/subscription
GET /seller/contact-requests
POST /seller/subscription/checkout
```

### 8.4. products

Задачи:

- создать товар;
- редактировать черновик;
- отправить на модерацию;
- получить каталог;
- получить карточку товара.

API:

```http
GET /products
GET /products/{product_id}
POST /products
PATCH /products/{product_id}
POST /products/{product_id}/submit
```

Публичный каталог должен показывать только:

```text
status = published
```

### 8.5. files

Задачи:

- загрузить файл;
- проверить размер;
- проверить расширение;
- сохранить в storage;
- сохранить запись в БД;
- выдать основной файл только автору или админу для модерации.

API:

```http
POST /files/upload
GET /files/{file_id}/download
```

Для MVP основной файл лучше отправлять через бота, а не давать прямой download URL.

### 8.6. subscriptions

Задачи:

- показать доступные планы;
- создать оплату подписки автора;
- обработать webhook;
- активировать/продлить подписку;
- ограничивать публикацию по подписке.

API:

```http
GET /subscription-plans
POST /seller/subscription/checkout
POST /subscription-payments/webhook/{provider}
```

### 8.7. contact_requests

Задачи:

- зафиксировать, что пользователь нажал “Написати автору”;
- открыть Telegram-ссылку автора;
- уведомить автора о новом обращении;
- показать автору статистику обращений.

API:

```http
POST /products/{product_id}/contact
GET /seller/contact-requests
```

### 8.8. admin

Задачи:

- модерация;
- скрытие товара;
- просмотр подписок авторов;
- просмотр обращений.

API:

```http
GET /admin/products/pending
POST /admin/products/{product_id}/approve
POST /admin/products/{product_id}/reject
POST /admin/products/{product_id}/request-changes
POST /admin/products/{product_id}/hide
GET /admin/subscriptions
POST /admin/sellers/{seller_id}/activate-subscription
GET /admin/contact-requests
```

### 8.9. notifications

Задачи:

- отправить пользователю сообщение в Telegram;
- уведомить автора о новом обращении;
- уведомить автора о статусе подписки;
- уведомить продавца о модерации;
- уведомить админа о новом товаре.

---

## 9. API contracts

### 9.1. POST /auth/telegram

Request:

```json
{
  "init_data": "query_id=...&user=...&auth_date=...&hash=..."
}
```

Response:

```json
{
  "access_token": "jwt",
  "user": {
    "id": "uuid",
    "telegram_id": 123456789,
    "username": "teacher"
  }
}
```

### 9.2. GET /products

Query params:

```text
language
level
category
audience
min_price
max_price
search
sort
page
limit
```

Response:

```json
{
  "items": [
    {
      "id": "uuid",
      "title": "30 Speaking Cards for A2 Teens",
      "language": "english",
      "level": "a2",
      "category": "speaking_cards",
      "price_amount": 14900,
      "currency": "UAH",
      "preview_url": "https://...",
      "seller": {
        "display_name": "Марія"
      }
    }
  ],
  "page": 1,
  "limit": 20,
  "total": 100
}
```

Рекомендация по цене: хранить в копейках/центах.

```text
149 грн = 14900
```

### 9.3. GET /products/{id}

Response:

```json
{
  "id": "uuid",
  "title": "30 Speaking Cards for A2 Teens",
  "description": "Матеріал для speaking practice...",
  "language": "english",
  "level": "a2",
  "category": "speaking_cards",
  "audience": "teens",
  "price_amount": 14900,
  "currency": "UAH",
  "previews": [
    {
      "url": "https://..."
    }
  ],
  "seller": {
    "id": "uuid",
    "display_name": "Марія",
    "bio": "Викладачка англійської...",
    "contact_username": "maria_teacher"
  },
  "is_favorite": false
}
```

### 9.4. POST /products/{id}/contact

Request:

```json
{
  "message": "Хочу придбати цей матеріал"
}
```

Response:

```json
{
  "contact_request_id": "uuid",
  "seller_telegram_url": "https://t.me/maria_teacher"
}
```

### 9.5. POST /seller/subscription/checkout

Request:

```json
{
  "plan_code": "pro_monthly"
}
```

Response:

```json
{
  "subscription_payment_id": "uuid",
  "payment_url": "https://payment-provider/...",
  "status": "pending"
}
```

### 9.6. GET /seller/subscription

Response:

```json
{
  "plan": "pro_monthly",
  "status": "active",
  "expires_at": "2026-06-20T10:00:00Z",
  "product_limit": 50,
  "published_products_count": 12
}
```

### 9.7. POST /products

Request:

```json
{
  "title": "30 Speaking Cards for A2 Teens",
  "description": "Матеріал для speaking practice...",
  "language": "english",
  "level": "a2",
  "category": "speaking_cards",
  "audience": "teens",
  "price_amount": 14900,
  "currency": "UAH",
  "product_file_id": "uuid",
  "preview_file_ids": ["uuid", "uuid"]
}
```

Response:

```json
{
  "id": "uuid",
  "status": "draft"
}
```

---

## 10. Telegram Bot UX

### 10.1. Главное меню

```text
👋 Вітаємо в ТічерМаркет

Тут викладачі знаходять і продають готові матеріали для уроків напряму одне одному.

[🛍 Відкрити маркет]
[🔎 Знайти матеріали]
[➕ Продати матеріал]
[⭐ Збережене]
[👤 Кабінет автора]
[❓ Допомога]
```

### 10.2. Покупательский сценарий

Покупатель чаще всего должен идти в Mini App:

```text
Натисніть кнопку нижче, щоб відкрити каталог матеріалів:
[🛍 Відкрити ТічерМаркет]
```

Кнопка открывает Mini App.

В боте оставить быстрый доступ:

```text
[⭐ Збережене]
```

### 10.3. Продавец: добавление материала

FSM-сценарий в aiogram:

```text
seller_add_product_title
seller_add_product_description
seller_add_product_language
seller_add_product_level
seller_add_product_category
seller_add_product_audience
seller_add_product_price
seller_add_product_file
seller_add_product_previews
seller_add_product_confirm
```

Шаги:

1. Название.
2. Описание.
3. Язык.
4. Уровень.
5. Тип материала.
6. Аудитория.
7. Цена.
8. Основной файл или способ передачи большого файла.
9. Превью.
10. Подтверждение.
11. Отправка на модерацию.

Сообщение после отправки:

```text
✅ Матеріал відправлено на модерацію.

Ми перевіримо:
— чи файл відкривається;
— чи опис відповідає матеріалу;
— чи немає очевидно чужого контенту;
— чи матеріал підходить для ТічерМаркету.

Статус можна подивитись у кабінеті автора.
```

### 10.4. Админская модерация

Админ получает сообщение:

```text
🆕 Новий матеріал на модерацію

Назва: 30 Speaking Cards A2
Автор: @username
Ціна: 149 грн
Мова: Англійська
Рівень: A2
Тип: Speaking cards

[👀 Подивитись файл]
[🖼 Превʼю]
[✅ Опублікувати]
[❌ Відхилити]
[✏️ Попросити правки]
```

Действия:

- `approve` → статус `published`, продавцу уведомление.
- `reject` → статус `rejected`, продавцу причина.
- `request_changes` → статус `rejected` или отдельный `changes_requested`.

Для MVP можно использовать `rejected` + комментарий.

### 10.5. Уведомление автору о новом обращении

```text
📩 Нове звернення щодо матеріалу

Матеріал: {product_title}
Від: @{buyer_username}

[Відповісти в Telegram]
```

### 10.6. Уведомление автору о подписке

```text
✅ Підписку активовано

План: {plan_name}
Діє до: {expires_at}

Тепер ви можете публікувати більше матеріалів у ТічерМаркеті.
```

---

## 11. Telegram Mini App UX

### 11.1. Главная

Блоки:

```text
ТічерМаркет
Маркет готових матеріалів для викладачів

[Пошук матеріалів]

Категорії:
- Англійська
- Німецька
- Speaking cards
- Worksheets
- Тести
- Презентації

Новинки
Популярне
Добірки редакції
```

### 11.2. Каталог

Фильтры:

```text
Мова
Рівень
Тип матеріалу
Аудиторія
Ціна
Формат
```

Сортировки:

```text
Нові
Популярні
Дешевші
Дорожчі
```

### 11.3. Карточка товара в списке

```text
[preview image]

30 Speaking Cards for A2 Teens
Англійська · A2 · Speaking cards
Автор: Марія
149 грн
```

### 11.4. Страница товара

Содержимое:

```text
Обложка / превью
Название
Цена
Автор
Категории
Описание
Что внутри
Формат файла
Кнопка “Написати автору”
Кнопка “Зберегти”
```

### 11.5. Сохраненное

```text
Збережене

- 30 Speaking Cards for A2 Teens
  [Написати автору]

- Present Perfect Test B1
  [Написати автору]
```

### 11.6. Кабинет автора

MVP-экраны:

```text
Мої матеріали
Звернення
Підписка
Профіль автора
```

---

## 12. Subscription and contact flow

### 12.1. Сценарий связи с автором

```text
1. User opens product in Mini App.
2. User clicks “Написати автору”.
3. Mini App calls POST /products/{id}/contact.
4. Backend checks product status = published.
5. Backend creates contact_request for analytics.
6. Backend writes audit log.
7. Backend notifies seller.
8. Mini App opens Telegram chat with seller.
9. Buyer and seller agree on payment and file delivery outside the platform.
```

### 12.2. Сценарий оплаты подписки автором

```text
1. Author opens “Кабінет автора”.
2. Author chooses subscription plan.
3. Mini App or bot calls POST /seller/subscription/checkout.
4. Backend creates subscription_payment.
5. Backend returns payment_url.
6. Author pays.
7. Payment provider calls webhook.
8. Backend verifies webhook signature.
9. Backend checks amount, currency and plan.
10. Backend marks subscription_payment as paid.
11. Backend activates or extends subscription.
12. Backend writes audit log.
13. Backend notifies author.
```

### 12.3. Idempotency

Webhook подписки может прийти несколько раз.

Нужно:

- искать subscription_payment by `provider_payment_id`;
- если уже `paid`, не продлевать подписку повторно;
- все обновления делать в транзакции;
- не отправлять 10 уведомлений, если webhook повторился.

Простой вариант:

```text
if subscription_payment.status == paid:
    return 200 OK
else:
    mark paid
    activate_or_extend_subscription
```

### 12.4. Подписка вместо комиссии

ТічерМаркет не берет комиссию с продаж материалов и не выплачивает авторам деньги.

```text
Доход сервиса = подписки авторов
Доход автора = сделки, которые автор проводит напрямую с покупателем
```

Примеры ограничений:

```text
Free: до 3 опубликованных материалов
Pro monthly: до 50 опубликованных материалов
Pro yearly: до 50 опубликованных материалов + приоритет в каталоге later
```

---

## 13. File flow

### 13.1. Загрузка файла продавцом

```text
1. Продавец отправляет файл в Telegram bot.
2. Bot скачивает файл с Telegram.
3. Bot отправляет файл в Backend /files/upload.
4. Backend проверяет размер и расширение.
5. Backend кладет файл в private storage.
6. Backend создает запись в files.
7. Backend возвращает file_id.
8. Bot привязывает file_id к product draft.
```

Если основной файл больше `MAX_PRODUCT_FILE_MB`, сервис не хранит его. Автор выбирает один из вариантов:

- добавить ссылку на файл для модерации и дальнейшей передачи покупателю;
- не прикреплять файл в сервисе и передать его покупателю лично после обращения.

Покупателю публично не показывается вечная ссылка на основной файл. В карточке можно показать только способ передачи: файл в сервисе, ссылка у автора или передача напрямую.

### 13.2. Загрузка превью

Превью могут быть:

- изображения;
- скриншоты PDF;
- mockup;
- первые страницы.

Для MVP продавец сам загружает 1–3 картинки.

### 13.3. Доступ к основному файлу

В новой модели сервис не выдает покупателю основной файл после оплаты, потому что сделка происходит напрямую между преподавателями.

```text
Основной файл хранится приватно.
Автор загружает его для модерации.
Админ может открыть файл и проверить материал.
Покупатель видит только превью, описание и контакты автора.
```

Почему так проще для MVP:

- ТічерМаркет не становится платежным посредником между авторами и покупателями;
- нет выплат авторам;
- нет споров по файлам внутри платформы;
- основной файл не лежит в публичном доступе.

---

## 14. Security checklist

### 14.1. Telegram Mini App auth

Нельзя доверять данным из frontend.

Правильно:

```text
Mini App получает Telegram initData
Mini App отправляет initData на backend
Backend проверяет подпись initData через bot token
Backend проверяет auth_date
Backend создает/обновляет user
Backend выдает короткий JWT/session token
Frontend ходит в API с Bearer token
```

Важно:

- не принимать `telegram_id` просто из body;
- не давать frontend самому выбирать пользователя;
- проверять срок жизни `auth_date`.

### 14.2. Telegram Bot webhook security

Для production:

- использовать webhook с secret token;
- принимать запросы только на случайном/секретном пути;
- проверять заголовок secret token;
- не светить bot token в логах;
- хранить bot token только в env.

### 14.3. Admin access

Админ — только Telegram ID из `ADMIN_TELEGRAM_IDS`.

Нужно:

- проверять каждое admin-действие;
- писать audit log;
- не делать админские endpoints без auth;
- не доверять роли, которую прислал frontend.

### 14.4. Subscription payment webhook security

Обязательно:

- проверять подпись webhook;
- проверять сумму;
- проверять валюту;
- проверять subscription_payment_id / plan_id;
- проверять provider payment id;
- делать webhook idempotent;
- не активировать подписку, если сумма не совпадает;
- не продлевать подписку повторно при duplicate webhook.

### 14.5. Storage security

Основной файл:

- private bucket;
- не публичный URL;
- доступ только автору и админу;
- signed URL только короткого TTL, если нужен;
- покупателю основной файл не выдается через платформу в MVP.
- если файл больше лимита, он не загружается в storage; автор прикрепляет ссылку или передает файл покупателю лично.

Превью:

- можно сделать публичными;
- но лучше хранить отдельно от основного файла;
- на превью добавлять watermark на уровне контента, если возможно.

### 14.6. Upload security

Проверять:

- размер файла;
- расширение;
- MIME type;
- количество превью;
- максимальную длину названия/описания;
- отсутствие исполняемых расширений;
- архивы `.zip` разрешать осторожно.
- для основного файла действует лимит `MAX_PRODUCT_FILE_MB`; при превышении лимита автору предлагается ссылка или личная передача файла покупателю.

Запретить в MVP:

```text
.exe
.js
sh
bat
cmd
app
dmg
apk
```

Разрешить:

```text
pdf
doc
docx
ppt
pptx
zip
jpg
jpeg
png
webp
```

### 14.7. Rate limiting

Нужно ограничить:

- количество upload-запросов;
- количество contact-запросов;
- частоту auth-запросов;
- частоту checkout-запросов на подписку.

Для MVP можно:

```text
per user simple rate limit in Redis or database
```

Если Redis не хочется в MVP:

```text
простая таблица rate_limit_events
```

### 14.8. Data privacy

Минимум персональных данных:

- Telegram ID;
- username;
- имя;
- избранное;
- обращения к авторам;
- статус подписки автора.

Важно:

- не хранить payment details авторов для выплат;
- показывать автору только данные, нужные для ответа на обращение;
- не хранить платежные карты;
- не логировать webhook payload с чувствительными данными полностью.

### 14.9. Backups

Минимум:

```text
ежедневный backup PostgreSQL
backup storage
хранить 7–14 дней
```

### 14.10. Abuse / copyright

Нужно заложить правила:

- продавец подтверждает, что материал его;
- маркет может снять материал с публикации;
- есть кнопка “Поскаржитись”;
- повторные нарушения = блокировка продавца;
- явный чужой контент не публиковать.

---

## 15. Legal / operational notes

Для MVP не надо усложнять, но нужно понимать:

### 15.1. Правила сервиса

Нужен простой текст:

- что можно продавать;
- что нельзя продавать;
- что ТічерМаркет только связывает преподавателей;
- что сделки, оплата и передача материалов происходят напрямую между преподавателями;
- условия подписки автора;
- ответственность автора за контент;
- политика возврата оплаты за подписку;
- что делать при жалобе на материал.

### 15.2. Подписки авторов

MVP-логика:

```text
Автор платит подписку за размещение материалов.
Free-план может дать лимит 1–3 материала.
Pro-план дает больше материалов и/или промо-возможности.
Сервис не принимает оплату за материалы и не выплачивает авторам деньги.
```

В базе:

```text
subscription_plans описывают тарифы
subscriptions фиксируют активный доступ автора
subscription_payments фиксируют оплаты подписки
```

### 15.3. Возвраты и споры

Для MVP:

- возврат по подписке возможен вручную через поддержку;
- споры между покупателем и автором по материалу не обрабатываются как платежный dispute внутри платформы;
- админ может скрыть материал, если есть жалоба или нарушение правил.

---

## 16. Development roadmap

### Этап 1. Repo skeleton

Цель:

- создать монорепо;
- поднять docker-compose;
- поднять PostgreSQL;
- запустить FastAPI;
- запустить aiogram bot;
- запустить React Mini App.

Acceptance criteria:

```text
GET /health returns ok
Bot responds to /start
Mini App opens locally
Database connection works
```

### Этап 2. Database + migrations

Цель:

- SQLAlchemy models;
- Alembic migrations;
- базовые таблицы.

Acceptance criteria:

```text
alembic upgrade head creates all MVP tables
```

### Этап 3. Auth

Цель:

- Telegram Mini App auth через initData;
- Bot user upsert by telegram_id;
- JWT for Mini App.

Acceptance criteria:

```text
Mini App can login
GET /auth/me returns current user
```

### Этап 4. Seller onboarding

Цель:

- продавец может создать профиль;
- бот умеет провести сценарий создания seller profile.

Acceptance criteria:

```text
User clicks “Кабінет автора”
Bot creates seller profile if missing
Seller profile visible in API
```

### Этап 5. File upload

Цель:

- загрузка файлов из бота в backend;
- storage integration;
- file records in DB.

Acceptance criteria:

```text
Seller uploads PDF
File appears in storage
files table has record
```

### Этап 6. Product submission

Цель:

- пошаговое добавление товара;
- черновик;
- отправка на модерацию.

Acceptance criteria:

```text
Seller creates product
Product status = pending_moderation
Admin receives notification
```

### Этап 7. Admin moderation

Цель:

- admin buttons in bot;
- approve/reject/request changes.

Acceptance criteria:

```text
Admin approves product
Product status = published
Product appears in Mini App catalog
Seller gets notification
```

### Этап 8. Mini App catalog

Цель:

- главная;
- список товаров;
- фильтры;
- карточка товара.

Acceptance criteria:

```text
User opens Mini App
Sees published products
Can filter by language/category/level
Can open product page
```

### Этап 9. Contact requests

Цель:

- кнопка “Написати автору”;
- запись обращения;
- уведомление автору;
- открытие Telegram-чата автора.

Acceptance criteria:

```text
User clicks “Написати автору”
Contact request is created
Seller gets notification
Mini App opens seller Telegram link
```

### Этап 10. Author subscriptions + mock payments

Цель:

- subscription plans;
- mock payment URL;
- endpoint to mark subscription payment paid for dev;
- activate/extend author subscription.

Acceptance criteria:

```text
Author chooses plan
Mock payment marks subscription paid
Subscription becomes active
Product limit is applied
```

### Этап 11. Real subscription payments

Цель:

- подключить выбранного провайдера для подписок;
- webhook;
- signature validation;
- idempotent subscription activation.

Acceptance criteria:

```text
Real subscription payment activates subscription
Duplicate webhook does not extend subscription twice
```

### Этап 12. Seller dashboard

Цель:

- мои материалы;
- обращения;
- подписка.

Acceptance criteria:

```text
Seller sees products, contact requests and subscription status
```

### Этап 13. Admin subscription management

Цель:

- admin sees author subscriptions;
- admin can manually activate/extend subscription;
- audit logs for subscription actions.

Acceptance criteria:

```text
Admin activates subscription for seller
Seller can publish within plan limit
Audit log is created
```

---

## 17. Coding prompts for vibe coding

Ниже — промпты, которые можно по очереди давать coding agent. Лучше идти маленькими шагами и после каждого шага запускать проект.

### Prompt 1 — repo skeleton

```text
Create a monorepo for a Telegram-first materials catalog MVP called teachermarket.

Stack:
- apps/api: FastAPI, SQLAlchemy async, Alembic, PostgreSQL
- apps/bot: aiogram 3
- apps/webapp: React + TypeScript + Vite + Tailwind
- docker-compose with postgres
- .env.example

Implement:
- API health endpoint GET /health
- database connection check
- bot /start command
- webapp basic HomePage

Do not implement business logic yet.
Make sure everything can run locally with clear commands in README.
```

### Prompt 2 — database models

```text
Implement SQLAlchemy async models and Alembic migrations for:
users, seller_profiles, files, products, product_previews, subscription_plans, subscriptions, subscription_payments, contact_requests, reviews, favorites, audit_logs.

Use UUID primary keys.
Use timestamptz created_at/updated_at.
Use text statuses matching the MVP spec.
Add useful indexes for product catalog filters, subscriptions and contact requests.

Add seed script with one admin user placeholder and 5 demo products.
```

### Prompt 3 — Telegram auth for Mini App

```text
Implement Telegram Mini App authentication.

Backend:
- POST /auth/telegram receives init_data
- verifies Telegram initData using TELEGRAM_BOT_TOKEN
- checks auth_date freshness
- upserts user by telegram_id
- returns JWT access token
- GET /auth/me returns current user

Frontend:
- read window.Telegram.WebApp.initData
- call /auth/telegram
- store token
- attach Bearer token to API requests

Do not trust telegram_id from frontend body.
```

### Prompt 4 — bot API client and user upsert

```text
In apps/bot, implement an API client for the backend.

When user sends /start:
- bot sends telegram user data to backend
- backend upserts user
- bot shows main menu:
  🛍 Відкрити маркет
  🔎 Знайти матеріали
  ➕ Продати матеріал
  ⭐ Збережене
  👤 Кабінет автора
  ❓ Допомога

Use inline keyboard. The "Open market" button should open WEBAPP_URL as Telegram Web App.
```

### Prompt 5 — seller profile

```text
Implement seller profile flow.

Backend:
- POST /seller/profile
- GET /seller/profile
- PATCH /seller/profile

Bot:
- when user clicks "Кабінет автора", check if seller profile exists
- if not, ask display_name and bio
- create seller profile
- show seller menu:
  ➕ Додати матеріал
  📦 Мої матеріали
  📩 Звернення
  💳 Підписка
```

### Prompt 6 — file upload

```text
Implement file upload for product files and preview images.

Backend:
- POST /files/upload
- validate file size
- validate extension
- upload to S3-compatible storage
- create files DB record
- return file_id

Bot:
- when user uploads a Telegram document or photo during seller flow,
  download file from Telegram and upload it to backend.

For local dev, implement LocalStorageAdapter that saves files to /tmp/teachermarket_storage.
```

### Prompt 7 — product creation via bot

```text
Implement aiogram FSM for adding a product.

Steps:
1 title
2 description
3 language
4 level
5 category
6 audience
7 price
8 product file
9 1-3 preview images
10 confirm

Backend:
- POST /products creates draft
- PATCH /products/{id}
- POST /products/{id}/submit sets status pending_moderation

After submission, notify all admins from ADMIN_TELEGRAM_IDS.
```

### Prompt 8 — admin moderation in bot

```text
Implement admin moderation.

Backend:
- GET /admin/products/pending
- POST /admin/products/{id}/approve
- POST /admin/products/{id}/reject
- POST /admin/products/{id}/request-changes
- POST /admin/products/{id}/hide

Bot:
- admins receive moderation message with product info and buttons
- approve publishes product
- reject asks admin for reason and sends it to seller
- request changes asks admin for comment and sends it to seller

Add audit_logs for all admin actions.
```

### Prompt 9 — Mini App catalog

```text
Implement Mini App catalog.

Frontend pages:
- HomePage
- CatalogPage
- ProductPage
- FavoritesPage
- SellerDashboardPage

Backend:
- GET /products with filters:
  language, level, category, audience, min_price, max_price, search, sort, page, limit
- GET /products/{id}

Only published products should be visible publicly.
Show product previews, price, seller display_name and contact action.
```

### Prompt 10 — contact requests

```text
Implement contact requests.

Backend:
- POST /products/{id}/contact creates contact_request
- validates product status = published
- stores requester Telegram info when available
- returns seller Telegram URL
- GET /seller/contact-requests returns requests for current seller

When contact request is created:
- notify seller via bot
- write audit log

Frontend:
- product page has button "Написати автору"
- clicking it calls backend, then opens seller Telegram link
```

### Prompt 11 — author subscriptions and mock payments

```text
Implement author subscription plans and mock subscription payments.

Backend:
- GET /subscription-plans
- GET /seller/subscription
- POST /seller/subscription/checkout
- DEV ONLY endpoint /subscription-payments/mock/{payment_id}/mark-paid
- activate or extend subscription when payment is paid
- enforce product limits by active subscription plan

Keep MockPaymentProvider.

Frontend:
- seller dashboard shows subscription status
- seller can choose plan and open payment_url
```

### Prompt 12 — real subscription payment provider

```text
Refactor subscription payments to use PaymentProvider interface.

Interface:
- create_payment(subscription_payment) -> payment_url, provider_payment_id
- verify_webhook(request) -> verified event
- parse_event(payload) -> payment status, subscription_payment id, amount, currency

Keep MockPaymentProvider.
Add skeleton for RealPaymentProvider with TODOs for selected provider.
Webhook must:
- verify signature
- verify amount and currency
- be idempotent
- activate subscription in a DB transaction
```

### Prompt 13 — seller dashboard

```text
Implement seller dashboard.

Backend:
- GET /seller/products
- GET /seller/contact-requests
- GET /seller/subscription

Frontend:
- show seller products
- show contact requests count/list
- show active plan and expiry date
- show button to upgrade/extend subscription
```

### Prompt 14 — security hardening pass

```text
Do a security hardening pass.

Implement:
- admin checks everywhere
- auth dependency for protected endpoints
- upload limits
- allowed extensions
- webhook idempotency
- audit logs for admin/subscription/contact/product status actions
- CORS restricted to WEBAPP_URL
- no secrets in logs
- basic rate limiting for auth, upload, contact requests and subscription checkout
- proper error responses without leaking stack traces

Add tests for:
- non-admin cannot approve product
- user cannot access another seller's contact requests
- free author cannot exceed product limit
- duplicate subscription webhook does not extend subscription twice
```

---

## 18. Minimal test plan

### 18.1. Buyer tests

- user opens Mini App;
- user sees catalog;
- filters work;
- product page opens;
- user can save product to favorites;
- user can click “Написати автору”;
- contact request is created;
- seller Telegram link opens.

### 18.2. Seller tests

- user creates seller profile;
- seller adds material;
- file upload works;
- preview upload works;
- product goes to moderation;
- seller sees status;
- seller gets notification after approval/rejection;
- seller sees contact requests;
- seller sees subscription status;
- seller cannot publish above free/pro plan limit.

### 18.3. Admin tests

- admin sees pending material;
- admin approves product;
- product becomes published;
- admin rejects product with reason;
- non-admin cannot access admin endpoints;
- admin can activate/extend seller subscription;
- audit log is created.

### 18.4. Subscription payment tests

- payment amount matches selected subscription plan;
- wrong currency fails;
- wrong signature fails;
- duplicate webhook returns OK but does not extend subscription twice;
- failed payment does not activate subscription.

### 18.5. File tests

- unsupported extension rejected;
- too large file rejected;
- non-owner cannot download product file;
- non-admin cannot open moderation file;
- previews do not expose original product file.

---

## 19. MVP design notes

### 19.1. Brand logic

ТічерМаркет должен ощущаться как отдельный продукт, но внутри одной экосистемы:

```text
Тічер Тусовка — комьюнити / главный бренд
ТічерБорд — CRM / автоматизация
ТічерМаркет — маркет материалов
```

### 19.2. Tone of voice

Украинский интерфейс:

```text
легко
дружелюбно
без перегруза
для преподавателей
```

Примеры:

```text
Продати матеріал
Збережене
Кабінет автора
Матеріал на модерації
Написати автору
Підписку активовано
```

### 19.3. Не превращать в файлопомойку

Ключевая позиция:

```text
Кураторський маркет матеріалів від реальних викладачів.
```

---

## 20. Что не делать в MVP

Не делать сразу:

- корзину;
- встроенную покупку материалов;
- автогенерацию watermark в каждом PDF;
- авто-выплаты авторам;
- сложную систему рейтинга авторов;
- реферальную систему;
- внутренний чат покупателя и продавца;
- сложный dispute center;
- отдельную большую web-admin;
- мобильное приложение;
- многоязычность интерфейса;
- AI-рекомендации.

---

## 21. Definition of Done для MVP

MVP можно считать готовым, если:

```text
1. Пользователь открывает бота.
2. Пользователь открывает Mini App.
3. Пользователь видит каталог опубликованных материалов.
4. Пользователь может открыть карточку материала.
5. Пользователь может связаться с автором через Telegram.
6. Обращение сохраняется в аналитике автора.
7. Продавец может добавить материал.
8. Материал проходит ручную модерацию.
9. Админ может одобрить/отклонить материал.
10. Продавец видит обращения и статус подписки.
11. Автор может оплатить подписку на сервис.
12. Основные файлы не лежат публично.
13. Subscription payment webhook проверяется и работает idempotently.
```

---

## 22. Самая короткая версия для разработчика

```text
Build a Telegram-first materials catalog MVP.

Interfaces:
- Telegram bot for onboarding, seller upload flow, admin moderation, notifications, author subscription status.
- Telegram Mini App for catalog, filters, product pages, favorites, contact requests, seller dashboard.

Backend:
- FastAPI, PostgreSQL, SQLAlchemy, Alembic.
- One backend for bot and Mini App.
- Private file storage.
- Subscription payment provider abstraction with mock first and real provider later.
- No material orders, no marketplace commission, no seller payouts.

Core flows:
- seller uploads product → admin moderates → product published
- buyer opens Mini App → finds product → contacts seller in Telegram
- seller sees contact requests
- seller pays subscription → webhook confirms → subscription activates

Security:
- verify Telegram initData
- verify subscription payment webhooks
- private files
- admin by Telegram ID allowlist
- idempotent subscription payment processing
- upload validation
- no public product file URLs
```

---

## 23. First practical steps

1. Создать репозиторий `teachermarket`.
2. Скопировать этот документ в `docs/mvp-spec.md`.
3. Создать `.env.example`.
4. Запустить Prompt 1 для coding agent.
5. После каждого этапа запускать проект локально.
6. Не переходить к оплатам подписки, пока не работает:
   - user auth;
   - products;
   - seller upload;
   - admin moderation;
   - catalog.
7. Сначала сделать contact requests.
8. Потом сделать mock payments для подписки.
9. Потом подключать реальный payment provider для подписки.

---

## 24. MVP risk list

### Риск 1: каталог в боте будет неудобным

Решение:

```text
Основной каталог делать в Mini App.
Бот использовать как вход, уведомления и выдачу файлов.
```

### Риск 2: продавцы зальют мусор

Решение:

```text
Ручная модерация.
Превью обязательно.
Четкие правила.
```

### Риск 3: файлы будут пересылать

Решение:

```text
Полностью не защитить.
Но можно:
- не давать публичные ссылки;
- показывать покупателю только превью;
- основной файл держать приватным для автора и модерации;
- делать watermark на превью;
- позже добавить персональный watermark в PDF.
```

### Риск 4: платежи и выплаты усложнят запуск

Решение:

```text
Не проводить сделки между преподавателями.
Не делать выплаты авторам.
Монетизация только через подписку автора на сервис.
```

### Риск 5: юридика

Решение:

```text
На MVP:
- простые правила сервиса;
- условия подписки;
- правила прямых сделок между преподавателями;
- ответственность автора за материалы;
- ручная модерация.
```

---

## 25. Финальная рекомендация по MVP

Идеальный первый запуск:

```text
@TeacherMarket_Bot
+
Telegram Mini App catalog
+
30–50 первых материалов
+
10–20 авторов
+
ручная модерация
+
оплата через payment link/webhook
+
подписка автора на сервис
+
обращения покупателей напрямую к авторам
```

Это даст нормальную проверку спроса без разработки гигантского маркетплейса.
