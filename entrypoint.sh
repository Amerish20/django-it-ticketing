#!/bin/sh

# wait for db
echo "Waiting for PostgreSQL..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done
echo "PostgreSQL started"

# run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# start server
echo "Starting server..."
gunicorn it_ticketing.wsgi:application --bind 0.0.0.0:8000
