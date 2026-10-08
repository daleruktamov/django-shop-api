# Shop API — backend интернет-магазина

REST API интернет-магазина на Django REST Framework: регистрация и JWT-авторизация,
каталог товаров с поиском и фильтрами, корзина, оформление заказов и отзывы с оценками.

Фронтенда нет и не предполагается — сервис отдаёт только JSON, поэтому им может
пользоваться сайт, мобильное приложение или бот.

## Стек

| Слой | Технология |
| --- | --- |
| Язык | Python 3.11+ |
| Фреймворк | Django 5.2 + Django REST Framework |
| База данных | PostgreSQL (локально можно на SQLite) |
| Авторизация | JWT (`djangorestframework-simplejwt`) |
| Документация | Swagger / OpenAPI (`drf-spectacular`) |
| Деплой | Render + Gunicorn + WhiteNoise |

## Ссылки

- **Рабочий API:** https://django-shop-api-pmxr.onrender.com/
- **Swagger:** https://django-shop-api-pmxr.onrender.com/api/docs/
- ReDoc: https://django-shop-api-pmxr.onrender.com/api/redoc/
- Схема OpenAPI: https://django-shop-api-pmxr.onrender.com/api/schema/
- Админка: https://django-shop-api-pmxr.onrender.com/admin/
- Презентация к защите: [docs/Shop_API_presentation.pptx](docs/Shop_API_presentation.pptx)

> Сервис развёрнут на бесплатном тарифе Render и засыпает без запросов —
> первый запрос после простоя открывается до минуты.

## Что умеет

**Пользователи и доступ**

- Регистрация по username + email + паролю, сразу выдаётся пара JWT-токенов.
- Вход по username **или** email, обновление access-токена по refresh-токену, выход
  с отзывом токена (blacklist).
- Просмотр и редактирование профиля, смена пароля.
- Три роли: **гость** (только просмотр каталога), **покупатель**, **администратор**.

**Каталог**

- Публичный список товаров с пагинацией (12 на страницу, `?page_size=` до 100).
- Поиск по названию и описанию: `?search=`.
- Фильтры: `?category=`, `?category_slug=`, `?min_price=`, `?max_price=`, `?in_stock=`.
- Сортировка: `?ordering=price | -price | -created_at | -sold_count | -rating`.
- Категории и товары создаёт, меняет и удаляет только администратор.
- Скрытые товары (`is_active=false`) видны только администратору.

**Корзина**

- У каждого покупателя одна корзина, она создаётся при первом обращении.
- Добавление товара, изменение количества, удаление позиции, полная очистка.
- Повторное добавление того же товара увеличивает количество, а не перезаписывает его.
- Нельзя положить больше, чем есть на складе. Чужую корзину тронуть нельзя.

**Заказы**

- Заказ собирается из корзины одной транзакцией: цены фиксируются, остатки
  списываются со склада, корзина очищается.
- Если товара не хватило — заказ не создаётся целиком, склад не меняется.
- Адрес и телефон подставляются из профиля, если не переданы явно.
- Статусы: `new` → `processing` → `shipped` → `delivered` (плюс `cancelled`).
  Менять статус может только администратор.
- Покупатель видит только свои заказы и может отменить заказ в статусе
  «новый» или «в обработке» — товары возвращаются на склад.

**Отзывы**

- Отзыв (текст + оценка 1–5) может оставить только тот, кто купил товар.
- Один отзыв на товар от одного пользователя.
- Средний рейтинг и количество отзывов считаются автоматически и приходят
  в карточке товара.
- Редактировать и удалять отзыв может автор или администратор.

## Быстрый старт

```bash
git clone https://github.com/RealHelloWorld1/django-shop-api.git
cd django-shop-api

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env

python manage.py migrate
python manage.py seed_demo       # демо-каталог и тестовые пользователи
python manage.py runserver
```

Дальше:

- API — <http://127.0.0.1:8000/>
- Swagger — <http://127.0.0.1:8000/api/docs/>
- Админка — <http://127.0.0.1:8000/admin/>

Команда `seed_demo` создаёт 4 категории, 12 товаров и двух пользователей:

| Логин | Пароль | Роль |
| --- | --- | --- |
| `admin` | `admin12345` | администратор |
| `customer` | `customer12345` | покупатель |

Свой суперпользователь: `python manage.py createsuperuser`.

### Переменные окружения

Все настройки читаются из `.env` (шаблон — `.env.example`):

| Переменная | Назначение | По умолчанию |
| --- | --- | --- |
| `SECRET_KEY` | секретный ключ Django | ключ для разработки |
| `DEBUG` | режим отладки | `True` |
| `ALLOWED_HOSTS` | разрешённые хосты через запятую | `localhost,127.0.0.1` |
| `DATABASE_URL` | строка подключения к PostgreSQL | локальный SQLite |
| `ACCESS_TOKEN_MINUTES` | время жизни access-токена | `60` |
| `REFRESH_TOKEN_DAYS` | время жизни refresh-токена | `7` |

Если `DATABASE_URL` не задан, проект поднимается на SQLite — так его можно
запустить сразу после клонирования. На Render используется PostgreSQL.

## Основные эндпоинты

Полный список — в Swagger (`/api/docs/`).

### Авторизация

| Метод | Адрес | Описание | Доступ |
| --- | --- | --- | --- |
| POST | `/api/auth/register/` | Регистрация | все |
| POST | `/api/auth/login/` | Вход, получение JWT | все |
| POST | `/api/auth/refresh/` | Новый access-токен | все |
| POST | `/api/auth/logout/` | Выход, отзыв refresh-токена | покупатель |
| GET / PATCH | `/api/auth/me/` | Профиль | покупатель |
| POST | `/api/auth/me/password/` | Смена пароля | покупатель |
| GET | `/api/auth/users/` | Список пользователей | администратор |

### Каталог

| Метод | Адрес | Описание | Доступ |
| --- | --- | --- | --- |
| GET | `/api/categories/` | Список категорий | все |
| POST / PATCH / DELETE | `/api/categories/{id}/` | Управление категориями | администратор |
| GET | `/api/products/` | Список товаров | все |
| GET | `/api/products/{id}/` | Карточка товара | все |
| POST / PATCH / DELETE | `/api/products/{id}/` | Управление товарами | администратор |

### Корзина

| Метод | Адрес | Описание | Доступ |
| --- | --- | --- | --- |
| GET | `/api/cart/` | Содержимое корзины и сумма | покупатель |
| POST | `/api/cart/items/` | Добавить товар | покупатель |
| PATCH | `/api/cart/items/{id}/` | Изменить количество | покупатель |
| DELETE | `/api/cart/items/{id}/` | Удалить позицию | покупатель |
| DELETE | `/api/cart/clear/` | Очистить корзину | покупатель |

### Заказы

| Метод | Адрес | Описание | Доступ |
| --- | --- | --- | --- |
| POST | `/api/orders/` | Оформить заказ из корзины | покупатель |
| GET | `/api/orders/` | Свои заказы (все — для админа) | покупатель |
| GET | `/api/orders/{id}/` | Детали заказа | владелец / админ |
| POST | `/api/orders/{id}/cancel/` | Отменить заказ | владелец / админ |
| PATCH | `/api/orders/{id}/status/` | Сменить статус | администратор |

### Отзывы

| Метод | Адрес | Описание | Доступ |
| --- | --- | --- | --- |
| GET | `/api/products/{id}/reviews/` | Отзывы о товаре | все |
| POST | `/api/products/{id}/reviews/` | Оставить отзыв | купивший товар |
| PATCH / DELETE | `/api/products/{id}/reviews/{review_id}/` | Изменить или удалить | автор / админ |

## Пример работы с API

```bash
# 1. Регистрация
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"ivan","email":"ivan@example.com","password":"Sup3rSecret!42","password2":"Sup3rSecret!42"}'

# 2. Вход — можно по username или по email
curl -X POST http://127.0.0.1:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"login":"ivan","password":"Sup3rSecret!42"}'

# 3. Каталог: поиск, фильтр по цене и сортировка
curl "http://127.0.0.1:8000/api/products/?search=ноутбук&max_price=6000000&ordering=price"

# 4. Добавить товар в корзину (нужен access-токен)
curl -X POST http://127.0.0.1:8000/api/cart/items/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"product":1,"quantity":2}'

# 5. Оформить заказ
curl -X POST http://127.0.0.1:8000/api/orders/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"phone":"+998901112233","address":"Ташкент, Чиланзар 5"}'
```

В Swagger токен вставляется кнопкой **Authorize** в формате `Bearer <ACCESS_TOKEN>`.

## Тесты

```bash
python manage.py test
```

54 теста покрывают регистрацию и вход, права гостя / покупателя / администратора,
поиск и фильтры каталога, работу корзины, оформление и отмену заказа, фиксацию
цены на момент покупки и правила отзывов.

## Деплой на Render

Есть файл `render.yaml` — Render может создать веб-сервис и базу одной кнопкой
(Blueprint). Вручную порядок такой:

1. **New → Postgres**, план **Free**. Запомнить регион. После создания скопировать
   **Internal Database URL**.
2. **New → Web Service**, подключить этот репозиторий, регион — **тот же, что у базы**.
3. Build Command: `./build.sh`
4. Start Command: `gunicorn config.wsgi:application`
5. Environment Variables:

   | Переменная | Значение |
   | --- | --- |
   | `DATABASE_URL` | Internal Database URL из шага 1 |
   | `SECRET_KEY` | длинная случайная строка |
   | `DEBUG` | `False` |
   | `SEED_DEMO` | `true` — заполнить базу демо-данными при сборке |
   | `ADMIN_PASSWORD` | пароль администратора `admin` |

`build.sh` сам ставит зависимости, собирает статику, накатывает миграции и —
если задан `SEED_DEMO=true` — создаёт демо-каталог и администратора. Это нужно
потому, что на бесплатном тарифе Render нет доступа к Shell. На платном тарифе
переменную можно не задавать, а выполнить `python manage.py createsuperuser`
в Shell.

Версия Python берётся из файла `.python-version`. `ALLOWED_HOSTS` на Render
заполняется автоматически из `RENDER_EXTERNAL_HOSTNAME`.

> Бесплатная база на Render живёт ограниченное время, а бесплатный веб-сервис
> засыпает без запросов — первый запрос после простоя открывается около минуты.

## Структура проекта

```
shop-api/
├── config/          настройки Django, корневые URL
├── core/            общие permissions, пагинация, корневой эндпоинт
├── users/           модель User, регистрация, JWT, профиль, роли
├── catalog/         категории и товары, фильтры, команда seed_demo
├── cart/            корзина и позиции корзины
├── orders/          заказы, позиции заказа, статусы
├── reviews/         отзывы и оценки
├── build.sh         скрипт сборки для Render
├── render.yaml      описание сервисов Render
└── requirements.txt зависимости
```

### Модели

| Модель | Назначение |
| --- | --- |
| `User` | аккаунт, роль, телефон и адрес доставки |
| `Category` | категория товаров |
| `Product` | товар: цена, остаток, изображение, счётчик продаж |
| `Cart` / `CartItem` | корзина пользователя и товары в ней |
| `Order` / `OrderItem` | заказ и его позиции со снимком цены |
| `Review` | отзыв: оценка 1–5 и текст |
