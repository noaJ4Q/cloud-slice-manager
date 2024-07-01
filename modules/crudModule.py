import logging
import os
from datetime import datetime

import jwt
from bson import ObjectId
from flask import Blueprint, jsonify, request, send_from_directory
from pymongo import MongoClient, collection
from pyvis.network import Network

from .tasks import delete_openstack, deploy_linux_cluster, deploy_openstack

logger = logging.getLogger("crudModule")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

crudModule = Blueprint("crudModule", __name__)


# DB CONNECTIONS
def db_connection():
    try:
        client = MongoClient("localhost", 27017)
        slicemanager_db = client["slicemanager_db"]
    except Exception as e:
        print(f"Error durante la conexión: {e}")
        return None
    return slicemanager_db


def db_connection_monitoreo():
    try:
        client = MongoClient("localhost", 27017)
        monitoreo_db = client["monitoreo"]
    except Exception as e:
        print(f"Error durante la conexión: {e}")
        return None
    return monitoreo_db


db_crud = db_connection()
db = db_connection_monitoreo()


# ONLY FOR CLIENT REQUESTS
@crudModule.route("/slices/client", methods=["GET"])
def list_client_slices():
    token = request.headers.get("Authorization")
    validation = validate_token(token, "client")
    if not isinstance(validation, dict):
        return validation

    try:
        decoded = validation
        slices = (
            list(db_crud.deployed_slices.find({"client": decoded["_id"]}))
            if db_crud
            else []
        )
        for slice in slices:
            slice["_id"] = str(slice["_id"])
        return jsonify({"message": "success", "slices": slices}), 200

    except Exception as e:
        return jsonify({"message": f"An error occurred: {e}"}), 500


@crudModule.route("/users", methods=["GET"], defaults={"role": None})
@crudModule.route("/users/<role>")
def list_users(role):
    token = request.headers.get("Authorization")
    validation = validate_token(token, "manager")
    if not isinstance(validation, dict):
        return validation

    print(role)
    try:
        if role is None:
            users = list(db_crud.users.find()) if db_crud else []
        else:
            users = list(db_crud.users.find({"role": role})) if db_crud else []
        for user in users:
            user["_id"] = str(user["_id"])
        return jsonify({"message": "success", "users": users}), 200

    except Exception as e:
        return jsonify({"message": f"An error occurred: {e}"}), 500


@crudModule.route("/slices", methods=["GET"])
@crudModule.route("/slices/client", methods=["GET"])
def list_slices():

    token = request.headers.get("Authorization")
    validation = validate_token(token, "manager")
    if not isinstance(validation, dict):
        return validation

    try:

        slices = list(db_crud.deployed_slices.find()) if db_crud else []  # FIND SLICES
        for slice in slices:
            slice["_id"] = str(slice["_id"])
        return jsonify({"message": "success", "slices": slices}), 200

    except Exception as e:
        return jsonify({"message": f"An errorr occurred: {e}"}), 500


@crudModule.route("/slices", methods=["POST"])
def create_slice():

    token = request.headers.get("Authorization")
    validation = validate_token(token, "manager")
    if not isinstance(validation, dict):
        return validation

    decoded = validation

    data = request.get_json()
    if not data:
        return jsonify({"message": "Missing JSON from topology"}), 400

    if request.json["deployment"]["platform"] == "OpenStack":
        task = deploy_openstack.delay(data, decoded)
        return jsonify({"message": "OpenStack deployment processed"})
    else:
        # procedimiento linux
        return jsonify({"message": "LinuxCluster deployment processed"})


@crudModule.route("/slices/delete/<slice_id>", methods=["POST"])
def delete_slice(slice_id):

    token = request.headers.get("Authorization")
    validation = validate_token(token, "manager")
    if not isinstance(validation, dict):
        return validation

    # buscar ID en la base de datos
    collection = db_crud.deployed_slices if db_crud else None
    if not collection:
        return jsonify({"message": "Database connection error"}), 500

    slice = collection.find_one({"_id": ObjectId(slice_id)})

    if not slice:
        return jsonify({"message": "Slice not found"}), 404

    # eliminar slice usando task de celery
    task = delete_openstack.delay(slice_id)
    return jsonify({"message": "Slice deletion processed"})


@crudModule.route("/slices/draft", methods=["GET"], defaults={"slice_id": None})
@crudModule.route("/slices/draft/<slice_id>")
def list_draft_slices(slice_id):

    token = request.headers.get("Authorization")
    validation = validate_token(token, "manager")
    if not isinstance(validation, dict):
        return validation

    try:
        if slice_id is None:
            slices = list(db_crud.slices_draft.find()) if db_crud else []
            for slice in slices:
                slice["_id"] = str(slice["_id"])
            return jsonify({"message": "success", "slices": slices}), 200
        else:
            slice = (
                db_crud.slices_draft.find_one({"_id": ObjectId(slice_id)})
                if db_crud
                else {}
            )
            slice["_id"] = str(slice["_id"])
            return jsonify({"message": "success", "slice": slice}), 200

    except Exception as e:
        return jsonify({"message": f"An error occurred: {e}"}), 500


@crudModule.route("/slices/draft", methods=["POST"])
def save_draft_slice():

    token = request.headers.get("Authorization")
    validation = validate_token(token, "manager")
    if not isinstance(validation, dict):
        return validation

    data = request.get_json()
    if not data:
        return jsonify({"message": "Missing JSON from topology"}), 400

    decoded = validation

    if "_id" in data:
        id = data["_id"]
        update_draft_to_db(data) 
        url = generate_diag(decoded["_id"], id, data["structure"])
        if update_graph_to_db(id, url):
            return jsonify({"message": "success", "sliceId": id})
        else:
            return jsonify(
                {
                    "message": "success",
                    "sliceId": id,
                    "graph_url": "Server error",
                }
            )
    else:
        id = save_draft_to_db(data, decoded)
        url = generate_diag(decoded["_id"], str(id.inserted_id), data["structure"])
        if update_graph_to_db(str(id.inserted_id), url):
            return jsonify({"message": "success", "sliceId": str(id.inserted_id)})
        else:
            return jsonify(
                {
                    "message": "success",
                    "sliceId": str(id.inserted_id),
                    "graph_url": "Server error",
                }
            )


def update_draft_to_db(data):
    document = db_crud.slices_draft.find_one({"_id": ObjectId(data["_id"])})
    if document:
        db_crud.slices_draft.update_one({"_id": ObjectId(data["_id"])}, {"$set": data})
        return True
    return False

@crudModule.route("/slices/diag", methods=["POST"])
def gen_diag():

    token = request.headers.get("Authorization")
    validation = validate_token(token, "manager")
    if not isinstance(validation, dict):
        return validation

    data = request.get_json()
    if not data:
        return jsonify({"message": "Missing JSON from topology"}), 400

    decoded = validation
    url = generate_diag(decoded["_id"], "", data)

    return jsonify(
        {
            "message": "success",
            "url": url,
            "tip": "We recommend to open url in private mode to avoid loading cache.",
        }
    )


@crudModule.route("/slices/topologyGraph/<path:filename>")
def serve_graph(filename):
    return send_from_directory("topologyGraph", filename)


def save_draft_to_db(data, decoded_token):
    data["manager"] = decoded_token["_id"]
    data["deployment"]["details"]["created"] = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    return db_crud.slices_draft.insert_one(data)


def update_graph_to_db(id, url):
    document = db_crud.slices_draft.find_one({"_id": ObjectId(id)})
    if document:
        document["deployment"]["details"]["graph_url"] = url
        db_crud.slices_draft.update_one({"_id": ObjectId(id)}, {"$set": document})
        return True
    return False


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


@crudModule.route("/monitoreo/<worker>", methods=["GET"])
def get_latest_metric(worker):
    collection = db[worker] if db else None

    token = request.headers.get("Authorization")
    validation = validate_token(token, "manager")
    if not isinstance(validation, dict):
        return validation

    if not collection:
        return jsonify({"message": "Database connection error"}), 500

    latest_metrics = list(collection.find().sort("time", -1).limit(1))
    if not latest_metrics:
        return jsonify({"message": "No data available"}), 404

    latest_metric = latest_metrics[0]
    del latest_metric["_id"]

    return jsonify({"message": "success", "data": latest_metric}), 200


def fecha_ya_vencio(fecha_definida):
    fecha_definida_dt = datetime.strptime(fecha_definida, "%Y-%m-%d %H:%M:%S")
    fecha_actual_dt = datetime.now()
    return fecha_actual_dt > fecha_definida_dt


def validate_token(token, role):
    if not token:
        return jsonify({"message": "Missing token"}), 401
    try:
        decoded = jwt.decode(token, "secret", algorithms=["HS256"])
        if fecha_ya_vencio(decoded["expired"]):
            return jsonify({"message": "Token expired"}), 411
        if decoded["role"] != role:
            return jsonify({"message": "Unauthorized access"}), 401
        return decoded
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 401
    except Exception as e:
        return jsonify({"message": f"An error occurred: {e}"}), 500


@crudModule.route("/logs", methods=["GET"])
def get_logs():
    log_file_path = "/root/Proyecto/cloud-slice-manager/app.log"

    if not os.path.exists(log_file_path):
        return jsonify({"message": "Log file not found"}), 404

    try:
        with open(log_file_path, "r") as log_file:
            logs_content = log_file.read()

        return jsonify({"message": "success", "data": logs_content}), 200

    except Exception as e:
        return jsonify({"message": f"Error reading log file: {str(e)}"}), 500
