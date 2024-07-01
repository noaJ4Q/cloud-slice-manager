from celery import Celery

from modules.openStack.openStackModule import eliminate_topology as deleteSliceOS
from modules.openStack.openStackModule import main as openStackModule

app = Celery("tasks", broker="redis://:headnode@0.0.0.0")


@app.task
def deploy_openstack(data, decoded):
    return openStackModule(data, decoded)


@app.task
def delete_openstack(project_id):
    return deleteSliceOS(project_id)


@app.task
def deploy_linux_cluster(data):
    # Aquí iría la lógica para el despliegue en un clúster de Linux
    return "LinuxCluster deployment processed"
