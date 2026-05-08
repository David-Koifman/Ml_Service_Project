# ML Loan Service

Масштабируемый ML-сервис для предсказания одобрения кредита с биллинговой системой на основе кредитов.

> Точность модели: **93%** (GradientBoostingClassifier) · Покрытие тестами: **92%**

## Требования

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (единственная зависимость)

## Быстрый старт

```bash
# 1. Клонировать и перейти в папку
git clone <repo>
cd MLServiceProject

# 2. Создать .env файл
cp .env.example .env

# 3. Запустить все сервисы
docker compose up -d
```

> Первый запуск скачивает Docker-образы (~2-3 ГБ), занимает 3-5 минут.
> Миграции БД и создание admin-аккаунта происходят **автоматически**.

```bash
# 4. Открыть в браузере
open http://localhost:8501        # Landing page / Dashboard
open http://localhost:8000/docs   # Swagger API документация
open http://localhost:3000        # Grafana (admin/admin)
```

## Сервисы

| Сервис | URL | Описание |
|---|---|---|
| API (Swagger) | http://localhost:8000/docs | REST API документация |
| Dashboard | http://localhost:8501 | Streamlit аналитика |
| Grafana | http://localhost:3000 | Мониторинг метрик (admin/admin) |
| Prometheus | http://localhost:9090 | Сбор метрик |

## Архитектура

```
Client → FastAPI → PostgreSQL
              ↓
           Redis → Celery Worker → ML Model (.joblib)
                                       ↓
                               Списание кредитов
```

## API Эндпоинты

### Auth
| Метод | URL | Описание |
|---|---|---|
| POST | `/auth/register` | Регистрация |
| POST | `/auth/login` | Логин → JWT токен |
| GET | `/users/me` | Личный кабинет |

### ML Модели
| Метод | URL | Описание |
|---|---|---|
| POST | `/models/upload` | Загрузить .joblib модель |
| GET | `/models/` | Список моделей |
| DELETE | `/models/{id}` | Удалить модель |

### Предсказания
| Метод | URL | Описание |
|---|---|---|
| POST | `/predictions/` | Создать задачу (async) |
| GET | `/predictions/{id}` | Статус и результат |
| GET | `/predictions/` | История предсказаний |

### Биллинг
| Метод | URL | Описание |
|---|---|---|
| GET | `/billing/balance` | Текущий баланс |
| POST | `/billing/topup` | Пополнить баланс |
| GET | `/billing/transactions` | История транзакций |
| POST | `/promo/activate` | Активировать промокод |

### Admin
| Метод | URL | Описание |
|---|---|---|
| POST | `/admin/promo` | Создать промокод |
| GET | `/admin/promo` | Список промокодов |
| DELETE | `/admin/promo/{id}` | Деактивировать промокод |

## Как работает биллинг

1. При регистрации пользователь получает **100 кредитов**
2. Каждое успешное предсказание стоит **10 кредитов**
3. Списание происходит **атомарно** (единая транзакция) только при успешном выполнении
4. Если worker упал — кредиты **не списываются**
5. Пополнение через `POST /billing/topup` (mock платёжного шлюза)
6. Промокоды дают бонусные кредиты (создаёт admin)

## Роли пользователей

| Роль | Возможности |
|---|---|
| `user` | Регистрация → 100 кредитов, предсказания, биллинг, промокоды |
| `admin` | Всё выше + загрузка/удаление моделей, управление промокодами, аналитика всех пользователей |

Сделать пользователя админом:
```bash
docker compose exec postgres psql -U mluser -d mlservice -c "UPDATE users SET role='admin' WHERE email='your@email.com';"
```

## Тестовые аккаунты

Admin создаётся **автоматически** при первом запуске:

| Роль | Email | Пароль |
|---|---|---|
| `admin` | admin@example.com | admin123 |

Обычный пользователь — зарегистрируйся через Dashboard (http://localhost:8501).

> Сменить email/пароль админа можно в `.env` через переменные `ADMIN_EMAIL` и `ADMIN_PASSWORD`.

## Пользовательский путь

```
Landing page (localhost:8501)
    ↓ Регистрация (+100 кредитов)
    ↓ Форма заёмщика (13 полей, доля займа считается автоматически)
    ↓ Celery обрабатывает асинхронно (~1-2 сек)
    ↓ Результат: Одобрено / Отказано + вероятность
    ↓ Списание 10 кредитов (только при успехе)
```

## Маркетинговые механики (Вариант А — Промокоды)

- Промокод даёт фиксированные кредиты или % скидку на пополнение
- Ограничение активаций + срок действия
- Защита от повторной активации одним пользователем
- Управление через Admin панель

## Загрузка ML модели

Загрузка моделей доступна только администраторам. Сервис принимает любую Scikit-learn модель в формате `.joblib`.

Пример обучения и загрузки демо-модели:

```bash
# Обучить модель
python ml/train_model.py

# Загрузить через API (после запуска)
curl -X POST http://localhost:8000/models/upload \
  -H "Authorization: Bearer <token>" \
  -F "name=Кредитный скоринг v1" \
  -F "file=@backend/ml_models/loan_model.joblib"
```

Формат запроса предсказания:

```json
{
  "person_age": 25,
  "person_gender": "male",
  "person_education": "Bachelor",
  "person_income": 50000,
  "person_emp_exp": 2,
  "person_home_ownership": "RENT",
  "loan_amnt": 10000,
  "loan_intent": "PERSONAL",
  "loan_int_rate": 12.5,
  "loan_percent_income": 0.2,
  "cb_person_cred_hist_length": 3,
  "credit_score": 650,
  "previous_loan_defaults_on_file": "No"
}
```

## Тесты

```bash
cd backend
pytest tests/ -v --cov=app --cov-report=term-missing
```

Покрытие: **92%**

## Переменные окружения

| Переменная | Описание |
|---|---|
| `DATABASE_URL` | PostgreSQL строка подключения |
| `REDIS_URL` | Redis URL |
| `SECRET_KEY` | Секретный ключ JWT |
| `PREDICTION_COST` | Стоимость предсказания в кредитах (default: 10) |
| `INITIAL_CREDITS` | Начальный баланс при регистрации (default: 100) |
| `GRAFANA_PASSWORD` | Пароль Grafana (default: admin) |
| `ADMIN_EMAIL` | Email admin-аккаунта (default: admin@example.com) |
| `ADMIN_PASSWORD` | Пароль admin-аккаунта (default: admin123) |
