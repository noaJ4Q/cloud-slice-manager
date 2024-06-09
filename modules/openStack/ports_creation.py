import json

from .openstack_sdk import create_port

# ENDPOINTS
NEUTRON_ENDPOINT = "http://127.0.0.1:9696/v2.0"


def main(token_for_project, network_id, project_id, port_name, edge_id, ports):
    resp1 = create_port(
        NEUTRON_ENDPOINT, token_for_project, port_name, network_id, project_id
    )
    if resp1.status_code == 201:
        print("PORT CREATED SUCCESSFULLY")
        port_created = resp1.json()
        ports[edge_id].append(port_created["port"]["id"])
    else:
        print("FAILED PORT CREATION")
        return

    resp2 = create_port(
        NEUTRON_ENDPOINT, token_for_project, port_name, network_id, project_id
    )
    if resp2.status_code == 201:
        print("PORT CREATED SUCCESSFULLY")
        port_created = resp2.json()
        ports[edge_id].append(port_created["port"]["id"])
    else:
        print("FAILED PORT CREATION")
        return
