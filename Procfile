web: gunicorn app:server --workers 4
workers: celery -A app:celery_app worker --loglevel DEBUG --concurrency=4
worker-beat: celery -A app:celery_app beat
