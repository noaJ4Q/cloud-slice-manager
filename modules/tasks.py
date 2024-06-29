from modules.celery_app import app
from modules.openStack.openStackModule import main as openStackModule


@app.task
def deploy_openstack(data):
    return openStackModule(data)


@app.task
def deploy_linux_cluster(data):
    # Aquí iría la lógica para el despliegue en un clúster de Linux
    return "LinuxCluster deployment processed"
