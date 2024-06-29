from celery import Celery

app = Celery("cloud_slice_manager", broker="redis://localhost:6379/0")
