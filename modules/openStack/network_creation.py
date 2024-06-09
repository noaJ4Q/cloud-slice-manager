import json
import logging

from .openstack_sdk import create_network
from .subnets_creation import main as subnets_creation

logger = logging.getLogger("network_creation")
logger.setLevel(logging.INFO)

# ENDPOINTS
NEUTRON_ENDPOINT = "http://127.0.0.1:9696/v2.0"
# CREDENTIALS
DOMAIN_ID = "default"


def main(token_for_project, json_data):
    logger.info("Creando red")
    network_name = json_data["deployment"]["details"]["network_name"]
    resp3 = create_network(NEUTRON_ENDPOINT, token_for_project, network_name)
    if resp3.status_code == 201:
        print("NETWORK CREATED SUCCESSFULLY")
        logger.info("NETWORK CREATED SUCCESSFULLY")
        network_created = resp3.json()
        network_id = json.dumps(network_created)["network"]["id"]
        logs = subnets_creation(
            token_for_project=token_for_project,
            network_id=network_id,
            json_data=json_data,
        )
        logger.info(logs)
    else:
        print("FAILED NETWORK CREATION")
        logger.error("FAILED NETWORK CREATION")
    log_contents = logger.getvalue()
    return log_contents
