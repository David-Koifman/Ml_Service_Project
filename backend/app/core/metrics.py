from prometheus_client import Counter, Histogram

predictions_total = Counter(
    "ml_predictions_total",
    "Total number of prediction tasks",
    ["status"],
)

credits_spent_total = Counter(
    "ml_credits_spent_total",
    "Total credits spent on predictions",
)

credits_added_total = Counter(
    "ml_credits_added_total",
    "Total credits added (topup + promo)",
    ["source"],
)

prediction_duration_seconds = Histogram(
    "ml_prediction_duration_seconds",
    "Time spent running ML prediction",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)
