import io
import logging

import requests

from .admin_token_for_project import main as admin_token_for_project
from .openstack_sdk import (
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


def main(json_data):
    log_info(logger, "Inicio de la operación de OpenStack")
    # ===================================================== INITIALIZATION =====================================================
    success, output = execute_bash_command(". ~/env-scripts/admin-openrc")
    if success:
        log_info(logger, "GOOD INIT" + output)
        # ===================================================== PROJECT CREATION =====================================================
        command = (
            "openstack project create "
            + json_data["deployment"]["details"]["project_name"]
        )

        success, output = execute_bash_command(command)
        if success:
            log_info(logger, "PROJECT CREATED SUCCESSFULLY")
            command2 = (
                "openstack role add admin --project "
                + json_data["deployment"]["details"]["project_name"]
                + " --user admin"
            )
            success, output = execute_bash_command(command2)
            if success:
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
