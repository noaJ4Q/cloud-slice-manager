import logging
import jwt
from flask import Blueprint, jsonify, request, send_from_directory
from pymongo import collection
from pyvis.network import Network
from pymongo import MongoClient
from datetime import datetime


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
]

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

@crudModule.route("/slices", methods=["GET"])
def list_slices():
    token = request.headers.get("Authorization")

    decoded = None
    validate_token(token, decoded)
    # find all slices in db, in case there are none, return an empty list
    slices = list(db_crud.slices.find()) if db_crud else []
    for slice in slices:
        slice["_id"] = str(slice["_id"])
    return jsonify({"message": "success", "slices": slices})

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

@crudModule.route("/slice", methods=["POST"])
def save_slice():
    token = request.headers.get("Authorization")
    try:
        decoded = jwt.decode(token, "secret", algorithms=["HS256"])
        if decoded["role"] == "manager": # AUTHORIZATION
            data = request.get_json()
            if not data:
                return jsonify({"message": "Missing JSON from topology"}), 400

            id = save_structure_to_db(data)

            return jsonify({"message": "success", "sliceId": str(id.inserted_id)})
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


def save_structure_to_db(data):
    data["deployment"]["details"]["created"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return db_crud.slices.insert_one(data)

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

@crudModule.route("/monitoreo/<worker>", methods=["GET"])
def get_latest_metric(worker):
    collection = db[worker] if db else None
    token = request.headers.get("Authorization")

    valid_token(token)

    try:
        decoded = jwt.decode(token, "secret", algorithms=["HS256"])

        if not collection:
            return jsonify({"message": "Database connection error"}), 500

        latest_metrics = list(collection.find().sort("time", -1).limit(1))
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

def fecha_ya_vencio(fecha_definida):
    fecha_definida_dt = datetime.strptime(fecha_definida, '%Y-%m-%d %H:%M:%S')
    fecha_actual_dt = datetime.now()
    
    return fecha_actual_dt > fecha_definida_dt

def validate_token(token, decoded):
    try:
        decoded = jwt.decode(token, "secret", algorithms=["HS256"])
        if fecha_ya_vencio(decoded["expired"]):
            return jsonify({"message", "Token expired"}), 411
        if decoded["role"] == "manager":
           ...
        else:
            return jsonify({"message": "Unauthorized access"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 401
    except Exception as e:
        return jsonify({"message": f"An error occurred: {e}"}), 500

