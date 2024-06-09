import json
import logging

from .instances_creation import main as instances_creation
from .openstack_sdk import create_subnet
from .ports_creation import main as ports_creation

logger = logging.getLogger("subnets_creation")
logger.setLevel(logging.INFO)

# ENDPOINTS
NEUTRON_ENDPOINT = "http://127.0.0.1:9696/v2.0"
# CREDENTIALS
DOMAIN_ID = "default"
# DATA


def main(token_for_project, network_id, json_data):
    logger.info("Creando subred")
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
        print("SUBNET CREATED SUCCESSFULLY")
        logger.info("SUBNET CREATED SUCCESSFULLY")
        subnet_created = resp.json()

        project_id = json.dumps(subnet_created)["subnet"]["project_id"]

        ports = {}
        for edge_id, edge_info in json_data["visjs"]["edges"].items():
            logs = ports_creation(
                token_for_project=token_for_project,
                network_id=network_id,
                project_id=project_id,
                port_name=edge_info["label"],
                ports=ports,
                edge_id=edge_id,
            )
            logger.info(logs)
        for node_id in json_data["metadata"]["nodes"].items():
            logs1 = instances_creation(
                token_for_project=token_for_project,
                node_id=node_id,
                ports=ports,
                json_data=json_data,
            )
            logger.info(logs1)

    else:
        print("FAILED SUBNET CREATION")
        logger.error("FAILED SUBNET CREATION")
    log_contents = logger.getvalue()
    return log_contents
