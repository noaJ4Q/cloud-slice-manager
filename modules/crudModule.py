import jwt
from flask import Blueprint, jsonify, request

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
            slice = request.json["slice"]
            return jsonify({"message": "success", "slice": slice})
        else:
            return jsonify({"message": "Unauthorized access"}), 401
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 401