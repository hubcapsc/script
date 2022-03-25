import sys
import json

import googleapiclient.discovery
import googleapiclient.errors
import google.auth.exceptions

def build_discovery_service_object(service, version):
    try:
        obj = googleapiclient.discovery.build(service, version)
    except google.auth.exceptions.DefaultCredentialsError:
        print(
            "No Google application credentials.\n"
            "Please do one of the following before re-running the script:\n"
            "1) Run `gcloud auth application-default login`\n"
            "OR\n"
            "2) Set the GOOGLE_APPLICATION_CREDENTIALS environment variable\n"
        )
        sys.exit(1)

    return obj

def verify_project(project_id):
    resource_manager = build_discovery_service_object(
        "cloudresourcemanager", "v3")
    project_name = f"projects/{project_id}"

    try:
        resource_manager.projects().get(name=project_name).execute()
    except googleapiclient.errors.HttpError as e:
        if e.resp.status == 403:
            print(f"Error: Permission denied on project \"{project_id}\" (or it may not exist).")
            # error_msg = json.loads(e.content).get("error").get("message")
            # print(f"Error: {error_msg}")
        else:
            raise
        return False
    else:
        return True

def verify_region(project_id, region):
    compute = build_discovery_service_object("compute", "v1")

    try:
        compute.regions().get(project=project_id, region=region).execute()
    except googleapiclient.errors.HttpError as e:
        error_msg = json.loads(e.content).get("error").get("message")
        print(f"Error: {error_msg}")
        return False
    else:
        return True

def verify_zone(project_id, region, zone):
    compute = build_discovery_service_object("compute", "v1")

    if not zone.startswith(region):
        print(f"Error: Zone \"{zone}\" does not exist in \"{region}\" region.")
        return False

    try:
        compute.zones().get(project=project_id, zone=zone).execute()
    except googleapiclient.errors.HttpError as e:
        error_msg = json.loads(e.content).get("error").get("message")
        print(f"Error: {error_msg}")
        return False
    else:
        return True

def verify_image(project_id, image_name):
    compute = build_discovery_service_object("compute", "v1")
    try:
        compute.images().get(project=project_id, image=image_name).execute()
    except googleapiclient.errors.HttpError as e:
        error_msg = json.loads(e.content).get("error").get("message")
        print(f"Error: {error_msg}")
        return False
    else:
        return True

def verify_subnet(project_id, region, subnet):
    compute = build_discovery_service_object("compute", "v1")

    try:
        compute.subnetworks().get(
            project=project_id,
            region=region,
            subnetwork=subnet).execute()
    except googleapiclient.errors.HttpError as e:
        error_msg = json.loads(e.content).get("error").get("message")
        print(f"Error: {error_msg}")
        return False
    else:
        return True

def verify_policy(project_id, region, policy):
    compute = build_discovery_service_object("compute", "v1")

    try:
        compute.resourcePolicies().get(
            project=project_id,
            region=region,
            resourcePolicy=policy).execute()
    except googleapiclient.errors.HttpError as e:
        message = json.loads(e.content).get("error").get("message")
        print(f"Error: {message}")
        return False
    else:
        return True

def verify_machine_type(project_id, zone, machine_type):
    compute = build_discovery_service_object("compute", "v1")

    try:
        compute.machineTypes().get(
            project=project_id,
            zone=zone,
            machineType=machine_type).execute()
    except googleapiclient.errors.HttpError as e:
        message = json.loads(e.content).get("error").get("message")
        print(f"Error: {message}")
        return False
    else:
        return True
