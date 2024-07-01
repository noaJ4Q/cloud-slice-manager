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
        expired_time = datetime.datetime.now() + datetime.timedelta(hours=1)
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

@authModule.route("/users", methods=["POST"])
def create_user():
    data = request.get_json()
    username = data.get("username")
    password_hash = data.get("password")
    role = data.get("role")

    # Verificar si faltan datos obligatorios
    if not (username and password_hash and role):
        return jsonify({"error": "Faltan datos obligatorios"}), 400

    # Verificar la autorización (simulado con un token en la cabecera)
    token = request.headers.get("Authorization")
    if not token or not validate_token(token, "admin"):
        return jsonify({"error": "Acceso no autorizado"}), 401

    # Guardar el usuario en la base de datos
    collection = db["users"]  # Colección 'users' en la base de datos
    user_data = {
        "username": username,
        "password": password_hash,
        "role": role
    }

    print(user_data)

    try:
        result = collection.insert_one(user_data)
        return jsonify({"message": "Usuario creado exitosamente", "user_id": str(result.inserted_id)})
    except Exception as e:
        return jsonify({"error": f"No se pudo crear el usuario: {str(e)}"}), 500


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
