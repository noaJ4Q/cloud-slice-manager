import datetime
import json
import logging
import subprocess

import requests


def log_info(logger, message):
    logger.info(
        json.dumps(
            {"timestamp": datetime.datetime.now().isoformat(), "message": message}
        )
    )


def log_error(logger, message):
    logger.error(
        json.dumps(
            {"timestamp": datetime.datetime.now().isoformat(), "message": message}
        )
    )


# INIT OPENSTACK
def execute_bash_command(command):
    try:
        response = subprocess.run(
            command,
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        return True, response.stdout
    except subprocess.CalledProcessError as e:
        return False, e.stderr


# KEYSTONE API
def password_authentication_with_scoped_authorization(
    auth_endpoint, user_domain_name, username, password, project_domain_id, project_name
):
    url = auth_endpoint + "/auth/tokens"

    data = {
        "auth": {
            "identity": {
                "methods": ["password"],
                "password": {
                    "user": {
                        "name": username,
                        "domain": {"name": user_domain_name},
                        "password": password,
                    }
                },
            },
            "scope": {
                "project": {"domain": {"id": project_domain_id}, "name": project_name}
            },
        }
    }

    r = requests.post(url=url, data=json.dumps(data))
    # status_code success = 201
    return r


def password_authentication_with_scoped_authorization_va(
    auth_endpoint, user_id, password, domain_id, project_id
):
    url = auth_endpoint + "/auth/tokens"

    data = {
        "auth": {
            "identity": {
                "methods": ["password"],
                "password": {
                    "user": {
                        "id": user_id,
                        "domain": {"id": domain_id},
                        "password": password,
                    }
                },
            },
            "scope": {"project": {"domain": {"id": domain_id}, "id": project_id}},
        }
    }

    r = requests.post(url=url, data=json.dumps(data))
    # status_code success = 201
    return r


def get_server_console(token, server_id):
    url = "http://10.20.12.153:8774" + "/servers/" + server_id + "/remote-consoles"
    headers = {
        "Content-type": "application/json",
        "X-Auth-Token": token,
        "OpenStack-API-Version": "compute v2.1",
    }

    data = {"remote_console": {"protocol": "vnc", "type": "novnc"}}

    r = requests.post(url=url, headers=headers, data=json.dumps(data))
    # status_code success = 200
    return r


def assign_role_to_user(auth_endpoint, token, project_id, user_id, role_id):
    url = (
        auth_endpoint
        + "/projects/"
        + project_id
        + "/users/"
        + user_id
        + "/roles/"
        + role_id
    )

    headers = {"Content-type": "application/json", "X-Auth-Token": token}

    r = requests.put(url=url, headers=headers)
    # status_code success = 204
    return r


def token_authentication_with_scoped_authorization(
    auth_endpoint, token, project_domain_id, project_name
):
    url = auth_endpoint + "/auth/tokens"

    data = {
        "auth": {
            "identity": {"methods": ["token"], "token": {"id": token}},
            "scope": {
                "project": {"domain": {"id": project_domain_id}, "name": project_name}
            },
        }
    }

    r = requests.post(url=url, data=json.dumps(data))
    # status_code success = 201
    return r


def create_project(auth_endpoint, token, domain_id, project_name, project_description):

    url = auth_endpoint + "/projects"
    headers = {"Content-type": "application/json", "X-Auth-Token": token}

    data = {
        "project": {
            "name": project_name,
            "description": project_description,
            "domain_id": domain_id,
        }
    }

    r = requests.post(url=url, headers=headers, data=json.dumps(data))
    # status_code success = 201
    return r


# NEUTRON API
# def create_network(auth_endpoint, token, name, network_type=None, segmentation_id=None):
def create_network(auth_endpoint, token, name):
    url = auth_endpoint + "/networks"
    data = {
        "network": {
            "name": name,
            "port_security_enabled": "false",
        }
    }

    """
    if network_type is not None:
        data['network']["provider:network_type"] = network_type

    if segmentation_id is not None:
        data["network"]["provider:segment"] = segmentation_id
    """

    headers = {"Content-type": "application/json", "X-Auth-Token": token}
    r = requests.post(url=url, headers=headers, data=json.dumps(data))
    # status_code success = 201
    return r


def create_subnet(auth_endpoint, token, network_id, name, ip_version, cidr):

    url = auth_endpoint + "/subnets"
    data = {
        "subnet": {
            "network_id": network_id,
            "name": name,
            "enable_dhcp": False,
            "gateway_ip": None,
            "ip_version": ip_version,
            "cidr": cidr,
        }
    }

    data = data = json.dumps(data)

    headers = {"Content-type": "application/json", "X-Auth-Token": token}
    r = requests.post(url=url, headers=headers, data=data)
    # status_code success = 201
    return r


def create_port(auth_endpoint, token, name, network_id, project_id):

    url = auth_endpoint + "/ports"
    headers = {"Content-type": "application/json", "X-Auth-Token": token}

    data = {
        "port": {
            "name": name,
            "tenant_id": project_id,
            "network_id": network_id,
            "port_security_enabled": "false",
        }
    }

    r = requests.post(url=url, headers=headers, data=json.dumps(data))
    # status_code success = 201
    return r


# NOVA API
# def create_instance(auth_endpoint, token, name, flavorRef, imageRef=None, availability_zone=None, network_list=None, compute_version=None):
def create_instance(auth_endpoint, token, name, flavorRef, imageRef, network_list):
    url = auth_endpoint + "/servers"
    headers = {
        "Content-type": "application/json",
        "X-Auth-Token": token,
    }
    """
    if compute_version is not None:
        headers['OpenStack-API-Version'] = 'compute ' + compute_version
    """

    data = {
        "server": {
            "name": name,
            "flavorRef": flavorRef,
            "imageRef": imageRef,
            #'availability_zone': availability_zone,
            "networks": network_list,
        }
    }

    """
    if imageRef is not None:
        data['server']['imageRef'] = imageRef

    if availability_zone is not None:
        data['server']['availability_zone'] = availability_zone

    if network_list is not None:
        data['server']['networks'] = network_list

    if volume_list is not None:
        data['server']['block_device_mapping'] = volume_list
    """

    r = requests.post(url=url, headers=headers, data=json.dumps(data))
    # status_code success = 202
    return r


def list_instances(nova_endpoint, token, project_id=None):
    # url = nova_endpoint + '/servers'
    url = nova_endpoint + "/servers/detail"
    headers = {"Content-type": "application/json", "X-Auth-Token": token}

    params = {"all_tenants": True}
    if project_id:
        params = {"all_tenants": True, "project_id": project_id}

    r = requests.get(url=url, headers=headers, params=params)
    return r


def delete_server(auth_endpoint, token, server_id):
    url = auth_endpoint + "/servers/" + server_id
    headers = {"Content-type": "application/json", "X-Auth-Token": token}

    r = requests.delete(url=url, headers=headers)
    # status_code success = 204
    return r


def list_ports(auth_endpoint, token, project_id=None):
    url = auth_endpoint + "/ports"
    headers = {"Content-type": "application/json", "X-Auth-Token": token}

    params = {}
    if project_id:
        params["project_id"] = project_id

    try:
        r = requests.get(url=url, headers=headers, params=params)
        r.raise_for_status()  # Raise an exception for HTTP errors
    except requests.exceptions.RequestException as e:
        print("Error en la solicitud: ", e)
        r = None
    return r


def delete_port(auth_endpoint, token, port_id):
    url = auth_endpoint + "/ports/" + port_id
    headers = {"Content-type": "application/json", "X-Auth-Token": token}

    r = requests.delete(url=url, headers=headers)
    # status_code success = 204
    return r


def delete_subnet(auth_endpoint, token, subnet_id):
    url = auth_endpoint + "/subnets/" + subnet_id
    headers = {"Content-type": "application/json", "X-Auth-Token": token}

    r = requests.delete(url=url, headers=headers)
    # status_code success = 204
    return r


def list_subnets(auth_endpoint, token, project_id=None):
    url = auth_endpoint + "/subnets"
    headers = {"Content-type": "application/json", "X-Auth-Token": token}

    params = {}
    if project_id:
        params["project_id"] = project_id

    try:
        r = requests.get(url=url, headers=headers, params=params)
        r.raise_for_status()  # Raise an exception for HTTP errors
    except requests.exceptions.RequestException as e:
        print("Error en la solicitud: ", e)
        r = None
    return r


def list_networks(auth_endpoint, token, project_id=None):
    url = auth_endpoint + "/networks"
    headers = {"Content-type": "application/json", "X-Auth-Token": token}

    params = {}
    if project_id:
        params["project_id"] = project_id

    try:
        r = requests.get(url=url, headers=headers, params=params)
        r.raise_for_status()  # Raise an exception for HTTP errors
    except requests.exceptions.RequestException as e:
        print("Error en la solicitud: ", e)
        r = None
    return r


def delete_network(auth_endpoint, token, network_id):
    url = auth_endpoint + "/networks/" + network_id
    headers = {"Content-type": "application/json", "X-Auth-Token": token}

    r = requests.delete(url=url, headers=headers)
    # status_code success = 204
    return r


def delete_project(auth_endpoint, token, project_id):
    url = auth_endpoint + "/projects/" + project_id
    headers = {"Content-type": "application/json", "X-Auth-Token": token}

    r = requests.delete(url=url, headers=headers)
    # status_code success = 204
    return r
