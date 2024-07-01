import io
import json
import logging
from datetime import datetime

from bson import ObjectId
from pymongo import MongoClient, collection
from pyvis.network import Network

from .instances_creation import main as instances_creation
from .openstack_sdk import (
    create_subnet,
    get_server_console,
    log_error,
    log_info,
    password_authentication_with_scoped_authorization_va,
)
from .ports_creation import main as ports_creation

log_buffer = io.StringIO()
buffer_handler = logging.StreamHandler(log_buffer)
logger = logging.getLogger("subnets_creation")
logger.addHandler(buffer_handler)
logger.setLevel(logging.INFO)

# ENDPOINTS
NEUTRON_ENDPOINT = "http://127.0.0.1:9696/v2.0"
NOVA_ENDPOINT = "http://127.0.0.1:8774/v2.1"
KEYSTONE_ENDPOINT = "http://127.0.0.1:5000/v3"
ADMIN_USER_ID = "d95ef81dc2374f939b6800c44a97743f"
ADMIN_USER_PASSWORD = "7c80c0fc17c122fa228c4d3aea5c12c0"
ADMIN_PROJECT_ID = "400106fa8b724626ace6be4ddfbc1787"


# CREDENTIALS
DOMAIN_ID = "default"
# DATA


def generate_diag(userId, topoId, json_data):
    net = Network(notebook=True)

    nodes = json_data.get("visjs", {}).get("nodes", {})
    edges = json_data.get("visjs", {}).get("edges", {})
    edge_node_mapping = json_data.get("metadata", {}).get("edge_node_mapping", {})

    for node_id, node_info in nodes.items():
        net.add_node(node_id, label=node_info["label"], shape="circle")

    for from_node, edge_ids in edge_node_mapping.items():
        for edge_id in edge_ids:
            edge_info = edges.get(edge_id, {})
            to_node = next(
                (
                    n_id
                    for n_id, e_list in edge_node_mapping.items()
                    if edge_id in e_list and n_id != from_node
                ),
                None,
            )
            if to_node:
                net.add_edge(
                    from_node,
                    to_node,
                    label=edge_info.get("label", ""),
                    color=edge_info.get("color", ""),
                )

    net.repulsion(node_distance=200)

    html_file = f"topologyGraph/{userId+topoId}.html"
    net.show(html_file)

    return f"http://10.20.12.153:8080/slices/{html_file}"


def save_draft_to_db(data, decoded_token):
    data["manager"] = decoded_token["_id"]
    data["deployment"]["details"]["status"] = "deployed"
    data["deployment"]["details"]["created"] = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    return db_crud.deployed_slices.insert_one(data)


def update_graph_to_db(id, url):
    document = db_crud.deployed_slices.find_one({"_id": ObjectId(id)})
    if document:
        document["deployment"]["details"]["graph_url"] = url
        db_crud.deployed_slices.update_one({"_id": ObjectId(id)}, {"$set": document})
        return True
    return False


def db_connection():
    try:
        client = MongoClient("localhost", 27017)
        slicemanager_db = client["slicemanager_db"]
    except Exception as e:
        print(f"Error durante la conexión: {e}")
        return None
    return slicemanager_db


db_crud = db_connection()


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
