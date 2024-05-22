import jwt
from flask import Blueprint, jsonify, request

authModule = Blueprint("authModule", __name__)

USERS = [
    {"id": 1, "username": "branko", "password": "branko", "role": "manager"},
    {"id": 2, "username": "willy", "password": "willy", "role": "admin"},
    {"id": 3, "username": "mavend", "password": "mavend", "role": "client"},
]

@authModule.route("/auth", methods=["POST"])
def auth_user():
    # Get the username and password from JSON request
    username = request.json["username"]
    password = request.json["password"]

    user = validate_user(username, password)
    if user:
        token = jwt.encode({"role": user["role"]}, "secret", algorithm="HS256")
        return jsonify({"message": "success", "token": token})
    else:
        return jsonify({"message": "Invalid username or password"})

def validate_user(username, password):
    for user in USERS:
        if user["username"] == username and user["password"] == password:
            return user
    return None