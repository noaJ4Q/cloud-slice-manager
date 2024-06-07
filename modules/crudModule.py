import jwt
import requests
from flask import Blueprint, jsonify, request, send_from_directory
from pyvis.network import Network

from .openStack.openStackModule import main as openStackModule

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
                openStackModule(data)
            else:
                # procedimiento linux
                slice = request.json["slice"]
                return jsonify({"message": "success", "slice": slice})
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
