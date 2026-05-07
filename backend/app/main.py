import os
from fastapi import FastAPI, Response
from prometheus_client import CollectorRegistry, multiprocess, generate_latest, CONTENT_TYPE_LATEST
from prometheus_fastapi_instrumentator import Instrumentator

from app.routers import auth, users, models, predictions, billing, promo, admin

app = FastAPI(
    title="ML Loan Service",
    description="ML-сервис для предсказания одобрения кредита",
    version="1.0.0",
)

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
