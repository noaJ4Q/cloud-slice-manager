import io
import json
import logging

from .openstack_sdk import (
    create_instance,
    get_server_console,
    log_error,
    log_info,
    password_authentication_with_scoped_authorization_va,
)

log_buffer = io.StringIO()
buffer_handler = logging.StreamHandler(log_buffer)
logger = logging.getLogger("instances_creation")
logger.addHandler(buffer_handler)
logger.setLevel(logging.INFO)

# ENDPOINTS
NOVA_ENDPOINT = "http://127.0.0.1:8774/v2.1"
KEYSTONE_ENDPOINT = "http://127.0.0.1:5000/v3"
ADMIN_USER_ID = "d95ef81dc2374f939b6800c44a97743f"
ADMIN_USER_PASSWORD = "7c80c0fc17c122fa228c4d3aea5c12c0"
DOMAIN_ID = "default"
ADMIN_PROJECT_ID = "400106fa8b724626ace6be4ddfbc1787"
# CREDENTIALS
DOMAIN_ID = "default"


def get_token_for_admin():
    r = password_authentication_with_scoped_authorization_va(
        KEYSTONE_ENDPOINT,
        ADMIN_USER_ID,
        ADMIN_USER_PASSWORD,
        DOMAIN_ID,
        ADMIN_PROJECT_ID,
    )
    if r.status_code == 201:
        return r.headers["X-Subject-Token"]
    else:
        return None


def get_console_url_per_instance(instance_id):
    admin_token = get_token_for_admin()
    r = get_server_console(admin_token, instance_id)
    if r.status_code == 200:
        remote_url = r.json()["remote_console"]["url"]
        # REPLACE
        remote_url = remote_url.replace("controller:6080", "10.20.12.153:6080")
        print(r.json())
        return remote_url
    else:
        return None


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
        # url = get_console_url_per_instance(instance_id)
        # json_data["structure"]["metadata"]["nodes"][node_id]["console_url"] = url
        # save url in json_data
        log_info(logger, message)
    else:
        log_error(logger, f"FAILED INSTANCE CREATION: {resp.status_code} {resp.json()}")
    logs_contents = log_buffer.getvalue()
    return logs_contents
