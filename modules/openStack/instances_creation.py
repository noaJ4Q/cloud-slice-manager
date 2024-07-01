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
    instance_1_name = json_data["structure"]["visjs"]["nodes"][node_id]["label"]
    instance_1_flavor_id = json_data["structure"]["metadata"]["nodes"][node_id][
        "flavor"
    ]
    instance_1_image_id = json_data["structure"]["metadata"]["nodes"][node_id]["image"]

    list_ports = []

    for edge in json_data["structure"]["metadata"]["edge_node_mapping"][node_id]:
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
        instance_id = instance_created.get("server").get("id")
        message = f"instance_id: {instance_id}"
        # save url in json_data
        log_info(logger, message)
    else:
        log_error(logger, f"FAILED INSTANCE CREATION: {resp.status_code} {resp.json()}")
    # logs_contents = log_buffer.getvalue()
    return instance_id, json.dumps(instance_created)
