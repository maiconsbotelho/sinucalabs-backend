web: python manage.py migrate && python manage.py collectstatic --noinput && gunicorn config.wsgi:application
worker: celery -A config worker --loglevel=info