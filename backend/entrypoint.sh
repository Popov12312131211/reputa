#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! python -c "
import psycopg2
try:
    psycopg2.connect('$DATABASE_URL')
    print('PostgreSQL is ready!')
except psycopg2.OperationalError:
    exit(1)
" 2>/dev/null; do
    sleep 1
done

echo "Running migrations..."
alembic upgrade head

echo "Starting server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
