import io
import logging

import requests

from .admin_token_for_project import main as admin_token_for_project
from .openstack_sdk import (
    create_project,
    log_error,
    log_info,
    password_authentication_with_scoped_authorization,
)


class FilterDebugMessages(logging.Filter):
    def filter(self, record):
        if "Debugger is active!" in record.getMessage():
            return False
        if "Debugger PIN:" in record.getMessage():
            return False
        return True


log_buffer = io.StringIO()
buffer_handler = logging.StreamHandler(log_buffer)
buffer_handler.addFilter(FilterDebugMessages())
logger = logging.getLogger()
logger.addHandler(buffer_handler)
logger.setLevel(logging.INFO)

# ENDPOINTS
KEYSTONE_ENDPOINT = "http://127.0.0.1:5000/v3"
# CREDENTIALS
ADMIN_USER_PASSWORD = "f47972ff2e17ca282c94b16ffab56767"
ADMIN_USER_USERNAME = "admin"
ADMIN_USER_DOMAIN_NAME = "Default"
DOMAIN_ID = "default"
ADMIN_PROJECT_NAME = "admin"


def main(json_data):
    log_info(logger, "Inicio de la operación de OpenStack")

    # ===================================================== PROJECT CREATION =====================================================
    log_info(logger, "Creando proyecto")
    project_name = json_data["deployment"]["details"]["project_name"]
    resp = create_project(KEYSTONE_ENDPOINT, project_name)
    if resp.status_code == 201:
        log_info(logger, "PROYECTO CREADO EXITOSAMENTE")
        # ===================================================== ASSIGN ROLE TO USER =====================================================
        log_info(logger, "Asignando rol al usuario")
        project_id = resp.json()["project"]["id"]
        headers = {
            "X-Auth-Token": resp.headers["X-Subject-Token"],
            "Content-Type": "application/json",
        }
        data = {
            "role": {
                "name": "admin",
            }
        }
        resp2 = requests.post(
            f"{KEYSTONE_ENDPOINT}/projects/{project_id}/roles",
            headers=headers,
            json=data,
        )
        if resp2.status_code == 201:
            log_info(logger, "ROL ASIGNADO EXITOSAMENTE")
            # ===================================================== TOKEN FOR ADMIN USER =====================================================
            resp1 = password_authentication_with_scoped_authorization(
                KEYSTONE_ENDPOINT,
                ADMIN_USER_DOMAIN_NAME,
                ADMIN_USER_USERNAME,
                ADMIN_USER_PASSWORD,
                DOMAIN_ID,
                ADMIN_PROJECT_NAME,
            )
            if resp1.status_code == 201:
                log_info(logger, "SUCCESSFUL ADMIN AUTHENTICATION")
                admin_token = resp1.headers["X-Subject-Token"]
                logs = admin_token_for_project(
                    admin_token=admin_token, json_data=json_data
                )
                log_info(logger, logs)
            else:
                log_error(logger, "FAILED ADMIN AUTHENTICATION")
        else:
            log_error(logger, "FALLO EN LA ASIGNACIÓN DEL ROL AL USUARIO")
    else:
        log_error(logger, "FALLO EN LA CREACIÓN DEL PROYECTO")

    log_contents = log_buffer.getvalue()
    return log_contents
