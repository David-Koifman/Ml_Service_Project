#!/bin/sh
mkdir -p /tmp/prometheus_multiproc
alembic upgrade head
python -m app.seed
exec "$@"
