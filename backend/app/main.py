import os
from fastapi import FastAPI, Response, Request
from fastapi.responses import JSONResponse
from prometheus_client import CollectorRegistry, multiprocess, generate_latest, CONTENT_TYPE_LATEST
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.routers import auth, users, models, predictions, billing, promo, admin

limiter = Limiter(key_func=get_remote_address, default_limits=["60/minute"])

app = FastAPI(
    title="ML Loan Service",
    description="""
## ML-сервис для скоринга кредитных заявок

Платформа предоставляет REST API для автоматической оценки кредитоспособности заёмщиков
на основе ML-модели (GradientBoosting, точность 93%).

### Как начать работу
1. **Регистрация** — `POST /auth/register` (новый аккаунт получает 100 кредитов)
2. **Логин** — `POST /auth/login` → получить JWT токен
3. **Предсказание** — `POST /predictions/` с данными заёмщика (стоимость: 10 кредитов)
4. **Результат** — `GET /predictions/{id}` → решение + вероятность

### Роли
- **user** — регистрация, предсказания, пополнение баланса, промокоды
- **admin** — всё выше + загрузка/удаление моделей, управление промокодами, аналитика

### Биллинг
Система внутренних кредитов. Списание происходит атомарно только при успешном выполнении.
    """,
    version="1.0.0",
    contact={"name": "ML Loan Service", "email": "admin@mlservice.ru"},
    license_info={"name": "MIT"},
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

Instrumentator().instrument(app).expose(app)


@app.get("/metrics/combined", include_in_schema=False)
def metrics_combined():
    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)
    return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(models.router, prefix="/models", tags=["ML Models"])
app.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])
app.include_router(billing.router, prefix="/billing", tags=["Billing"])
app.include_router(promo.router, prefix="/promo", tags=["Promo"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
