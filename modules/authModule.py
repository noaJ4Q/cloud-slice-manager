import datetime
import hashlib

import jwt

# from entities.user import User
from flask import Blueprint, jsonify, request
from pymongo import MongoClient

authModule = Blueprint("authModule", __name__)


def db_connection():
    try:
        client = MongoClient("localhost", 27017)
        slicemanager_db = client["slicemanager_db"]
    except Exception as e:
        print(f"Error durante la conexión: {e}")
        return None
    return slicemanager_db


db = db_connection()


@authModule.route("/auth", methods=["POST"])
def auth_user():

    if not db:
        return jsonify({"message": "Database connection error"}), 500

    data = request.get_json()
    if not data or not "username" in data or not "password" in data:
        return jsonify({"message": "Missing username or password"}), 400

    username = data["username"]
    password = hashlib.sha256(data["password"].encode("utf-8")).hexdigest()

    user = validate_user(username, password)

    if user:
        expired_time = datetime.datetime.now() + datetime.timedelta(hours=1)

        token = jwt.encode(
            {"_id": str(user["_id"]), "role": user["role"], "expired": expired_time},
            "secret",
            algorithm="HS256",
        )
        return jsonify({"message": "success", "token": token}), 200
    else:
        return jsonify({"message": "Invalid username or password"}), 401


def validate_user(username, password):
    user = db.users.find_one({"username": username, "password": password})
    if user:
        return user
    return None
