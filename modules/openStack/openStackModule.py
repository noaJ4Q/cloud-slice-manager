import io
import logging

import requests
from dotenv import load_dotenv

from .admin_token_for_project import main as admin_token_for_project
from .openstack_sdk import (
    assign_role_to_user,
    create_project,
    execute_bash_command,
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


ADMIN_USER_ID = "8ea65183fdfb491684cbf7b6235cda3a"
ADMIN_PROJECT_ID = "4883bf19fa1f4522a66b888187c16a70"
ADMIN_ROLE_ID = "4b72a39d87794c82bdf15597bce0265d"
EXTERNAL_NETWORK_ID = "22d83117-7126-41d4-acaf-e7e815d04bfd"


def get_token_for_admin():
    r = password_authentication_with_scoped_authorization(
        KEYSTONE_ENDPOINT,
        ADMIN_USER_ID,
        ADMIN_USER_PASSWORD,
        DOMAIN_ID,
        ADMIN_PROJECT_ID,
    )
    if r.status_code == 201:
        return r.headers["X-Subject-Token"]
    else:
        return None


def main(json_data):
    log_info(logger, "Inicio de la operación de OpenStack")
    # ===================================================== INITIALIZATION =====================================================
    success, output = execute_bash_command(". ~/env-scripts/admin-openrc")
    if success:
        # ===================================================== PROJECT CREATION =====================================================
        command = (
            "openstack project create "
            + json_data["deployment"]["details"]["project_name"]
        )
        admin_token = get_token_for_admin()

        resp0 = create_project(
            KEYSTONE_ENDPOINT,
            admin_token,
            DOMAIN_ID,
            json_data["deployment"]["details"]["project_name"],
            json_data["deployment"]["details"]["project_desc"],
        )

        if resp0.status_code == 201:
            log_info(logger, "PROJECT CREATED SUCCESSFULLY")

            p = resp0.json()["project"]
            project_id = p["id"]

            resp1 = assign_role_to_user(
                KEYSTONE_ENDPOINT, admin_token, project_id, ADMIN_USER_ID, ADMIN_ROLE_ID
            )
            if resp1.status_code == 204:
                log_info(logger, "ROLE ADDED SUCCESSFULLY")
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
                    log_error(logger, "FAILED ADMIN AUTHENTICATION " + output)
            else:
                log_error(logger, "FAILED ROLE ADDITION " + output)
        else:
            log_error(logger, "FAILED PROJECT CREATION " + output)
    else:
        log_error(logger, "FAILED INITIALIZATION")
    log_contents = log_buffer.getvalue()
    return log_contents
