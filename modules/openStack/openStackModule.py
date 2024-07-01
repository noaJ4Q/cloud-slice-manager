import io
import logging

import requests
from dotenv import load_dotenv

from .admin_token_for_project import main as admin_token_for_project
from .openstack_sdk import (
    assign_role_to_user,
    create_project,
    delete_network,
    delete_port,
    delete_project,
    delete_server,
    delete_subnet,
    execute_bash_command,
    list_instances,
    list_networks,
    list_ports,
    list_subnets,
    log_error,
    log_info,
    password_authentication_with_scoped_authorization,
    password_authentication_with_scoped_authorization_va,
    token_authentication_with_scoped_authorization,
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
NOVA_ENDPOINT = "http://127.0.0.1:8774/v2.1"
NEUTRON_ENDPOINT = "http://127.0.0.1:9696"
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
    r = password_authentication_with_scoped_authorization_va(
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


def get_token_for_admin_in_project(project_id):
    admin_token = get_token_for_admin()
    resp = token_authentication_with_scoped_authorization(
        KEYSTONE_ENDPOINT, admin_token, DOMAIN_ID, project_id
    )
    # print('token project')
    # print(resp.status_code)
    if resp.status_code == 201:
        token_for_project = resp.headers["X-Subject-Token"]
        return token_for_project
    else:
        return None


def main(json_data, decoded):
    log_info(logger, "Inicio de la operación de OpenStack")
    # ===================================================== INITIALIZATION =====================================================
    success, output = execute_bash_command(". ~/env-scripts/admin-openrc")
    if success:
        log_info(logger, "GOOD INIT" + output)
        # ===================================================== PROJECT CREATION =====================================================
        admin_token = get_token_for_admin()
        log_info(logger, "ADMIN TOKEN: " + admin_token)

        resp0 = create_project(
            KEYSTONE_ENDPOINT,
            admin_token,
            DOMAIN_ID,
            json_data["deployment"]["details"]["project_name"],
            "Proyecto creado para "
            + json_data["deployment"]["details"]["project_name"],
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
                        admin_token=admin_token, json_data=json_data, decoded=decoded
                    )
                    log_info(logger, logs)
                else:
                    log_error(logger, "FAILED ADMIN AUTHENTICATION " + output)
            else:
                log_error(logger, "FAILED ROLE ADDITION " + output)
        else:

            log_error(logger, f"FAILED PROJECT CREATION: {resp0.status_code}")
    else:
        log_error(logger, "FAILED INITIALIZATION")
    log_contents = log_buffer.getvalue()
    return log_contents


def eliminate_topology(project_id):
    log_info(logger, "Inicio de la eliminación de OpenStack")
    token_for_project = get_token_for_admin_in_project(project_id)

    log_info(logger, "Buscando instancias")
    r1 = list_instances(NOVA_ENDPOINT, token_for_project, project_id)
    if r1.status_code == 200:
        instances = r1.json()["servers"]
    else:
        log_error(logger, "Error buscando instancias")
        return None
    for ins in instances:
        ins_id = ins["id"]

        r11 = delete_server(NOVA_ENDPOINT, token_for_project, ins_id)
        if r11.status_code == 204:
            log_info(logger, f"INSTANCIA BORRADA CORRECTAMENTE: {ins_id}")
        # print(ins_id)

    r2 = list_ports(NEUTRON_ENDPOINT, token_for_project, project_id)
    if r2.status_code != 200:
        log_error(logger, "Error buscando puertos")
    ports = r2.json()["ports"]
    for port in ports:
        port_id = port["id"]
        r21 = delete_port(NEUTRON_ENDPOINT, token_for_project, port_id)
        if r21.status_code == 204:
            log_info(logger, f"PUEERTO BORRADO CORRECTAMENTE: {port_id}")
        # print(port_id)

    r3 = list_subnets(NEUTRON_ENDPOINT, token_for_project, project_id)
    if r3.status_code != 200:
        return None
    subnets = r3.json()["subnets"]
    for sn in subnets:
        sn_id = sn["id"]
        r31 = delete_subnet(NEUTRON_ENDPOINT, token_for_project, sn_id)
        if r31.status_code == 204:
            log_info(logger, f"SUBRED BORRADA CORRECTAMENTE: {sn_id}")

    r4 = list_networks(NEUTRON_ENDPOINT, token_for_project, project_id)
    if r4.status_code != 200:
        return None
    nets = r4.json()["networks"]
    for net in nets:
        net_id = net["id"]
        r41 = delete_network(NEUTRON_ENDPOINT, token_for_project, net_id)
        if r41.status_code == 204:
            log_info(logger, f"RED BORRADA CORRECTAMENTE: {net_id}")

    r5 = delete_project(KEYSTONE_ENDPOINT, token_for_project, project_id)
    if r5.status_code == 204:
        log_info(logger, "TOPOLOGIA BORRADA CORRECTAMENTE")
    else:
        log_error(logger, "Error borrando proyecto")
    log_contents = log_buffer.getvalue()
    return log_contents
