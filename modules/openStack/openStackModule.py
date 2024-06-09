import logging
from io import StringIO

from .admin_token_for_project import main as admin_token_for_project
from .openstack_sdk import password_authentication_with_scoped_authorization

log_stream = StringIO()
logging.basicConfig(level=logging.INFO, stream=log_stream)

# ENDPOINTS
KEYSTONE_ENDPOINT = "http://127.0.0.1:5000/v3"
# CREDENTIALS
ADMIN_USER_PASSWORD = "f47972ff2e17ca282c94b16ffab56767"
ADMIN_USER_USERNAME = "admin"
ADMIN_USER_DOMAIN_NAME = "Default"
DOMAIN_ID = "default"
ADMIN_PROJECT_NAME = "admin"


def main(json_data):
    # ===================================================== TOKEN FOR ADMIN USER =====================================================
    resp1 = password_authentication_with_scoped_authorization(
        KEYSTONE_ENDPOINT,
        ADMIN_USER_DOMAIN_NAME,
        ADMIN_USER_USERNAME,
        ADMIN_USER_PASSWORD,
        DOMAIN_ID,
        ADMIN_PROJECT_NAME,
    )
    log_contents = log_stream.getvalue()
    if resp1.status_code == 201:
        print("SUCCESSFUL ADMIN AUTHENTICATION")
        admin_token = resp1.headers["X-Subject-Token"]
        admin_token_for_project(admin_token=admin_token, json_data=json_data)
    else:
        print("FAILED ADMIN AUTHENTICATION")
    return log_contents
