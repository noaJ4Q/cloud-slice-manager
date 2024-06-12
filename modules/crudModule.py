import logging

import jwt
import requests
from flask import Blueprint, jsonify, request, send_from_directory
from pymongo import collection
from pyvis.network import Network
from pymongo import MongoClient

from .openStack.openStackModule import main as openStackModule

logger = logging.getLogger("crudModule")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

crudModule = Blueprint("crudModule", __name__)

SLICES = [
    {
        "id": 1,
        "name": "Slice 1",
        "user": 3,
        "topology": "Malla",
        "vms": 2,
        "zone": "Zona 1",
        "created": "2021-06-01 10:00:00",
        "status": "active",
    },
    {
        "id": 2,
        "name": "Slice 2",
        "user": 3,
        "topology": "Anillo",
        "vms": 3,
        "zone": "Zona 2",
        "created": "2021-06-01 10:00:00",
        "status": "active",
    },
]


@crudModule.route("/slices", methods=["GET"])
def list_slices():
    token = request.headers.get("Authorization")
    try:
        decoded = jwt.decode(token, "secret", algorithms=["HS256"])
        if decoded["role"] == "manager":
            return jsonify({"message": "success", "slices": SLICES})
        else:
            return jsonify({"message": "Unauthorized access"}), 401
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 401


@crudModule.route("/slices", methods=["POST"])
def create_slice():
    token = request.headers.get("Authorization")
    try:
        decoded = jwt.decode(token, "secret", algorithms=["HS256"])
        if decoded["role"] == "manager":
            data = request.get_json()
            if not data:
                return jsonify({"message": "Missing JSON from topology"}), 400

            if request.json["deployment"]["platform"] == "OpenStack":
                logs = openStackModule(data)
                return jsonify(
                    {"message": "OpenStack deployment processed", "logs": logs}
                )
            else:
                # procedimiento linux
                return jsonify({"message": "LinuxCluster deployment processed"})
        else:
            return jsonify({"message": "Unauthorized access"}), 401
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 401


@crudModule.route("/slices/diag", methods=["POST"])
def gen_diag():
    token = request.headers.get("Authorization")
    try:
        decoded = jwt.decode(token, "secret", algorithms=["HS256"])
        data = request.get_json()
        if not data:
            return jsonify({"message": "Missing JSON from topology"}), 400

        url = generate_diag(decoded["_id"], data)

        return jsonify(
            {
                "message": "success",
                "url": url,
                "tip": "We recommend to open url in private mode to avoid loading cache.",
            }
        )
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 401


@crudModule.route("/slices/topologyGraph/<path:filename>")
def serve_graph(filename):
    return send_from_directory("topologyGraph", filename)


def generate_diag(userId, json_data):
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

    html_file = f"topologyGraph/{userId}.html"
    net.show(html_file)

    return f"http://10.20.12.148:8080/slices/{html_file}"


def db_connection_monitoreo():
    try:
        client = MongoClient("localhost", 27017)
        monitoreo_db = client["monitoreo"]
    except Exception as e:
        print(f"Error durante la conexión: {e}")
        return None
    return monitoreo_db


db = db_connection_monitoreo()
collection1 = db["worker1"] if db else None
collection2 = db["worker2"] if db else None
collection3 = db["worker3"] if db else None


@crudModule.route("/monitoreo/worker1", methods=["GET"])
def get_latest_metric_w1():
    token = request.headers.get("Authorization")
    try:
        decoded = jwt.decode(token, "secret", algorithms=["HS256"])

        if not collection:
            return jsonify({"message": "Database connection error"}), 500

        latest_metrics = list(collection1.find().sort("time", 1).limit(1))
        if not latest_metrics:
            return jsonify({"message": "No data available"}), 404

        latest_metric = latest_metrics[0]
        del latest_metric["_id"]

        return jsonify({"message": "success", "data": latest_metric}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 401
    except Exception as e:
        return jsonify({"message": f"An error occurred: {e}"}), 500


@crudModule.route("/monitoreo/worker2", methods=["GET"])
def get_latest_metric_w2():
    token = request.headers.get("Authorization")
    try:
        decoded = jwt.decode(token, "secret", algorithms=["HS256"])

        if not collection:
            return jsonify({"message": "Database connection error"}), 500

        latest_metrics = list(collection2.find().sort("time", 1).limit(1))
        if not latest_metrics:
            return jsonify({"message": "No data available"}), 404

        latest_metric = latest_metrics[0]
        del latest_metric["_id"]

        return jsonify({"message": "success", "data": latest_metric}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 401
    except Exception as e:
        return jsonify({"message": f"An error occurred: {e}"}), 500


@crudModule.route("/monitoreo/worker3", methods=["GET"])
def get_latest_metric_w3():
    token = request.headers.get("Authorization")
    try:
        decoded = jwt.decode(token, "secret", algorithms=["HS256"])

        if not collection:
            return jsonify({"message": "Database connection error"}), 500

        # Obtener el documento más reciente
        latest_metric = collection3.find_one({}, sort=[('_id', -1)])
        if not latest_metric:
            return jsonify({"message": "No data available"}), 404

        # Eliminar el campo "_id" del resultado final
        del latest_metric["_id"]

        return jsonify({"message": "success", "data": latest_metric}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 401
    except Exception as e:
        return jsonify({"message": f"An error occurred: {e}"}), 500