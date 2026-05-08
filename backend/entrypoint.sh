#!/bin/sh
alembic upgrade head
python -m app.seed
exec "$@"
