from celery import Celery

from modules.openStack.openStackModule import main as openStackModule

app = Celery("tasks", broker="redis://:headnode@0.0.0.0")


@app.task
def deploy_openstack(data):
    return openStackModule(data)


@app.task
def deploy_linux_cluster(data):
    # Aquí iría la lógica para el despliegue en un clúster de Linux
    return "LinuxCluster deployment processed"
