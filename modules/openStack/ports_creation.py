import io
import json
import logging

from .openstack_sdk import create_port

log_buffer = io.StringIO()
buffer_handler = logging.StreamHandler(log_buffer)
logger = logging.getLogger("ports_creation")
logger.addHandler(buffer_handler)
logger.setLevel(logging.INFO)

# ENDPOINTS
NEUTRON_ENDPOINT = "http://127.0.0.1:9696/v2.0"


def main(token_for_project, network_id, project_id, port_name, edge_id, ports):
    logger.info("Creando puertos")
    resp1 = create_port(
        NEUTRON_ENDPOINT, token_for_project, port_name, network_id, project_id
    )
    if resp1.status_code == 201:
        print("PORT CREATED SUCCESSFULLY")
        logger.info("PORT CREATED SUCCESSFULLY")
        port_created = resp1.json()
        ports[edge_id].append(port_created["port"]["id"])
    else:
        print("FAILED PORT CREATION")
        logger.error("FAILED PORT CREATION")

    resp2 = create_port(
        NEUTRON_ENDPOINT, token_for_project, port_name, network_id, project_id
    )
    if resp2.status_code == 201:
        print("PORT CREATED SUCCESSFULLY")
        logger.info("PORT CREATED SUCCESSFULLY")
        port_created = resp2.json()
        ports[edge_id].append(port_created["port"]["id"])
    else:
        print("FAILED PORT CREATION")
        logger.error("FAILED PORT CREATION")
    log_contents = log_buffer.getvalue()
    return log_contents
