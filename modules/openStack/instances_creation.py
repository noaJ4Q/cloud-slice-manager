import json

from openstack_sdk import create_instance

# ENDPOINTS
NOVA_ENDPOINT = "http://127.0.0.1:8774/v2.1"
# CREDENTIALS
DOMAIN_ID = "default"


def main(token_for_project, node_id, ports, json_data):

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
        print("INSTANCE CREATED SUCCESSFULLY")
        instance_created = resp.json()
        print(json.dumps(instance_created))
    else:
        print("FAILED INSTANCE CREATION")
        return
