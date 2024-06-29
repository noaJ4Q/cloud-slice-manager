from celery import Celery

import modules.tasks

app = Celery("cloud_slice_manager", broker="redis://:headnode@localhost:6379/0")
