import io
import json
import logging

from .crudModule import generate_diag, save_draft_to_db, update_graph_to_db
from .instances_creation import main as instances_creation
from .openstack_sdk import create_subnet, log_error, log_info
from .ports_creation import main as ports_creation

log_buffer = io.StringIO()
buffer_handler = logging.StreamHandler(log_buffer)
logger = logging.getLogger("subnets_creation")
logger.addHandler(buffer_handler)
logger.setLevel(logging.INFO)

# ENDPOINTS
NEUTRON_ENDPOINT = "http://127.0.0.1:9696/v2.0"
# CREDENTIALS
DOMAIN_ID = "default"
# DATA


def main(token_for_project, network_id, json_data, decoded):
    log_info(logger, "Creando subred")
    details = json_data["deployment"]["details"]
    resp = create_subnet(
        NEUTRON_ENDPOINT,
        token_for_project,
        network_id,
        details["subnet_name"],
        details["ip_version"],
        details["cidr"],
    )
    if resp.status_code == 201:
        log_info(logger, "SUBNET CREATED SUCCESSFULLY")
        subnet_created = resp.json()

        project_id = subnet_created["subnet"]["project_id"]

        ports = {}
        for edge_id, edge_info in json_data["structure"]["visjs"]["edges"].items():
            logs = ports_creation(
                token_for_project=token_for_project,
                network_id=network_id,
                project_id=project_id,
                port_name=edge_info["label"],
                ports=ports,
                edge_id=edge_id,
            )
            log_info(logger, logs)
        for node_id, node_info in json_data["structure"]["metadata"]["nodes"].items():
            logs1 = instances_creation(
                token_for_project=token_for_project,
                node_id=node_id,
                ports=ports,
                json_data=json_data,
            )
            log_info(logger, logs1)

        id = save_draft_to_db(json_data, decoded)
        url = generate_diag(decoded["_id"], str(id.inserted_id), json_data["structure"])
        if update_graph_to_db(str(id.inserted_id), url):
            log_info(logger, "DATA SAVED IN DB")
        else:
            log_error(logger, "SERVER ERROR SAVING DATA IN DB")

    else:
        log_error(logger, "FAILED SUBNET CREATION")
    log_contents = log_buffer.getvalue()
    return log_contents
