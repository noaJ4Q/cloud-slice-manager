import datetime
import hashlib
import logging

import jwt
from flask import Blueprint, jsonify, request
from pymongo import MongoClient

# Configurar el logger para incluir el nombre del módulo
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - [authModule] - %(name)s - %(levelname)s - %(message)s',
                    filename='app.log')
logger = logging.getLogger(__name__)

authModule = Blueprint("authModule", __name__)

def db_connection():
    try:
        client = MongoClient("localhost", 27017)
        slicemanager_db = client["slicemanager_db"]
        logger.info("Conexión a la base de datos establecida")
    except Exception as e:
        logger.error(f"Error durante la conexión: {e}")
        return None
    return slicemanager_db

db = db_connection()

@authModule.route("/auth", methods=["POST"])
def auth_user():
    if not db:
        logger.error("Error de conexión a la base de datos")
        return jsonify({"message": "Database connection error"}), 500

    data = request.get_json()
    if not data or not "username" in data or not "password" in data:
        logger.warning("Faltan el nombre de usuario o la contraseña en la solicitud")
        return jsonify({"message": "Missing username or password"}), 400

    username = data["username"]
    password = hashlib.sha256(data["password"].encode("utf-8")).hexdigest()
    logger.info(f"Intento de autenticación para el usuario: {username}")

    user = validate_user(username, password)

    if user:
        expired_time = datetime.datetime.now() + datetime.timedelta(seconds=15)
        token = jwt.encode(
            {
                "_id": str(user["_id"]),
                "role": user["role"],
                "expired": expired_time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            "secret",
            algorithm="HS256",
        )
        logger.info(f"Autenticación exitosa para el usuario: {username}")
        return jsonify({"message": "success", "token": token}), 200
    else:
        logger.warning(f"Nombre de usuario o contraseña inválidos para el usuario: {username}")
        return jsonify({"message": "Invalid username or password"}), 401

def validate_user(username, password):
    try:
        user = db.users.find_one({"username": username, "password": password})
        if user:
            logger.info(f"Usuario {username} encontrado en la base de datos")
            return user
        else:
            logger.info(f"Usuario {username} no encontrado en la base de datos")
    except Exception as e:
        logger.error(f"Error al buscar el usuario en la base de datos: {e}")
    return None
