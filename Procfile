web: gunicorn example.app:server --workers 2
workers: celery -A portal_core.app_factory:celery_app worker --loglevel DEBUG --concurrency=2
worker-beat: celery -A portal_core.app_factory:celery_app beat
