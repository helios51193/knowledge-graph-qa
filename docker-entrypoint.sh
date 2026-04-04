#!/bin/sh
set -e

echo "Waiting for postgres..."
while ! nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
  sleep 1
done

echo "Running migrations..."
python manage.py migrate --noinput

echo "Running collecting static..."
python manage.py collectstatic --noinput

exec "$@"