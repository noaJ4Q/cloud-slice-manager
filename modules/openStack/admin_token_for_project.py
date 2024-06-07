from network_creation import main as network_creation
from openstack_sdk import token_authentication_with_scoped_authorization

# ENDPOINTS
KEYSTONE_ENDPOINT = "http://127.0.0.1:5000/v3"
# CREDENTIALS
DOMAIN_ID = "default"


def main(admin_token, json_data):
    project_name = json_data["deployment"]["details"]["project_name"]
    # ===================================================== TOKEN FOR PROJECT =====================================================
    resp = token_authentication_with_scoped_authorization(
        KEYSTONE_ENDPOINT, admin_token, DOMAIN_ID, project_name
    )
    if resp.status_code == 201:
        print("SUCCESSFUL AUTHENTICATION FOR PROJECT " + project_name)
        token_for_project = resp.headers["X-Subject-Token"]
        network_creation(token_for_project=token_for_project, json_data=json_data)
    else:
        print("FAILED AUTHENTICATION FOR PROJECT " + project_name)
        return
