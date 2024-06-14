import io
import json
import logging

from .openstack_sdk import create_instance, log_error, log_info

log_buffer = io.StringIO()
buffer_handler = logging.StreamHandler(log_buffer)
logger = logging.getLogger("instances_creation")
logger.addHandler(buffer_handler)
logger.setLevel(logging.INFO)

# ENDPOINTS
NOVA_ENDPOINT = "http://127.0.0.1:8774/v2.1"
# CREDENTIALS
DOMAIN_ID = "default"


def main(token_for_project, node_id, ports, json_data):

    log_info(logger, "Creando instancias")

    # INSTANCE DATA
    instance_1_name = json_data["visjs"]["nodes"][node_id]["label"]
    instance_1_flavor_id = json_data["metadata"]["nodes"][node_id]["flavor"]
    instance_1_image_id = json_data["metadata"]["nodes"][node_id]["image"]

    list_ports = []

    for edge in json_data["metadata"]["edge_node_mapping"][node_id]:
        add_port = {"port": ports[edge][0]}
        list_ports.append(add_port)
        del ports[edge][0]

    instance_1_networks = list_ports

    resp = create_instance(
        NOVA_ENDPOINT,
        token_for_project,
        instance_1_name,
        instance_1_flavor_id,
        instance_1_image_id,
        instance_1_networks,
    )
    print(resp.status_code)
    if resp.status_code == 202:
        log_info(logger, "INSTANCE CREATED SUCCESSFULLY")
        instance_created = resp.json()
        print(json.dumps(instance_created))
        # TODO 1: Save instance_created["server"]["id"] in database
        # TODO 2: Get instance_created["server"]["addresses"] and update controller with 10.20.12.148
        # TODO 3: Save TODO 2 in database
    else:
        log_error(logger, "FAILED INSTANCE CREATION")
    logs_contents = log_buffer.getvalue()
    return logs_contents
