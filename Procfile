web: gunicorn example.app:server --workers 2
workers: celery -A app:celery_app worker --loglevel DEBUG --concurrency=2
worker-beat: celery -A app:celery_app beat
