#!/bin/sh

if [ "$COMPOSE_PROFILES" = "prod" ]; then
  echo "Running in production mode..."
  python manage.py migrate && \
  python manage.py init_admins && \
  gunicorn django_stickers_bot.wsgi:application --workers $(nproc) --bind 0.0.0.0:8000
else
  echo "Running in development mode..."
  python manage.py migrate && \
  python manage.py init_admins && \
  python manage.py runserver 0.0.0.0:8000
fi