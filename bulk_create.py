import argparse
import sys
import json
import socket
from enum import Enum

import googleapiclient.discovery
import google.auth.exceptions

import utils

class OBInstType(Enum):
    SERVER = 1
    CLIENT = 2

class OBOptions:
    def __init__(self, args):
        self.project = args.project
        self.region = args.region
        self.zone = args.zone
        self.image = f"global/images/{args.image}"

        self.scopes = []
        for item in args.scopes:
            self.scopes.append(f"https://www.googleapis.com/auth/{item}")

        if args.subnet:
            self.subnet = f"regions/{args.region}/subnetworks/{args.subnet}"
        else:
            self.subnet = None

        if args.enable_tier1_networking and args.nic_type != "GVNIC":
            print("Warning: Setting nic-type to \"GVNIC\" for Tier 1 networking.")
            self.nic_type = "GVNIC"
        else:
            self.nic_type = args.nic_type
        self.enable_tier1_networking = args.enable_tier1_networking

        self.threads_per_core = args.threads_per_core

        self.server = {
            "count": args.num_servers,
            "type": args.server_type,
            "prefix": args.server_prefix,
            "num_ssd_per": args.num_ssd_per_server
        }
        if args.server_metadata:
            self.server["metadata"] = parse_metadata_str(args.server_metadata)
        if args.server_policy:
            self.server["policy"] = args.server_policy

        self.client = {
            "count": args.num_clients,
            "type": args.client_type,
            "prefix": args.client_prefix
        }
        if args.client_metadata:
            self.client["metadata"] = parse_metadata_str(args.client_metadata)
        if args.client_policy:
            self.client["policy"] = args.client_policy

        if args.startup_script:
            self.startup_script = stringify_startup_script(args.startup_script)
        else:
            self.startup_script = None

def initialize_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "-p", "--project",
            required=True,
            help="GCP project id")
    parser.add_argument(
            "-r", "--region",
            required=True,
            help="GCP region to launch instances in")
    parser.add_argument(
            "-z", "--zone",
            required=True,
            help="GCP zone to launch instances in")
    parser.add_argument(
            "-i", "--image",
            required=True,
            help="name of source image to create instances from")
    # TODO: should "scopes" be required?
    parser.add_argument(
            "--scopes",
            required=True,
            action="append",
            metavar="SCOPE",
            help="GCP access scope to be applied to instances")
    parser.add_argument(
            "-s", "--subnet",
            default=None,
            help="subnetwork to create instances in")
    parser.add_argument(
            "--server-policy",
            default=None,
            help="name of resource policy to apply to server instances")
    parser.add_argument(
            "--client-policy",
            default=None,
            help="name of resource policy to apply to client instances")
    parser.add_argument(
            "--nic-type",
            default=None,
            choices=["", "GVNIC"],
            help="type of GCP vNIC to be used on generated network interface")
    parser.add_argument(
            "--enable-tier1-networking",
            action="store_true",
            help="enable TIER_1 networking on instances")
    parser.add_argument(
            "--num-servers",
            required=True,
            type=int,
            help="number of servers to create")
    parser.add_argument(
            "--num-clients",
            required=True,
            type=int,
            help="number of clients to create")
    parser.add_argument(
            "--server-type",
            required=True,
            help="machine type to use for server instances")
    parser.add_argument(
            "--client-type",
            required=True,
            help="machine type to use for client instances")
    parser.add_argument(
            "--server-prefix",
            required=True,
            help="string to begin all server names with")
    parser.add_argument(
            "--client-prefix",
            required=True,
            help="string to begin all client names with")
    parser.add_argument(
            "--server-metadata",
            default=None,
            help="comma-separated list of custom metadata key=value pairs")
    parser.add_argument(
            "--client-metadata",
            default=None,
            help="comma-separated list of custom metadata key=value pairs")
    parser.add_argument(
            "--num-ssd-per-server",
            type=int,
            default=0,
            help="number of local SSDs to attach to each server instance")
    parser.add_argument(
            "--threads-per-core",
            type=int,
            default=2,
            choices=[1, 2],
            help="number of threads per physical core on launched instances")
    parser.add_argument(
            "--startup-script",
            default=None,
            help="path to local startup script to run on launched instances")

    return parser

# Take a string of comma-separated key/value pairs of the form
# "key1=val1,key2=val2" and return a dictionary in the metadata format
# expected by the Google Python Client API, i.e.:
# {
#     "items": [
#         {
#             "key": "key1",
#             "value": "val1"
#         },
#         {
#             "key": "key2",
#             "value": "val2"
#         }
#     ]
# }
def parse_metadata_str(md_str):
    metadata = {}
    metadata["items"] = []

    kv_str_list = md_str.split(',')
    for kv_str in kv_str_list:
        kv_pair = kv_str.split('=', maxsplit=1)
        try:
            new_entry = {
                "key": kv_pair[0],
                "value": kv_pair[1]
            }
        except IndexError:
            # Google allows a key with no value, so we will too
            new_entry = {
                "key": kv_pair[0]
            }
        metadata["items"].append(new_entry)
    return metadata

# Read the contents of the startup script into a string
#
# With the Google Python Client API, a startup script must be specified
# through custom instance metadata, as a key/value pair where the value
# is a string containing the contents of the script.
def stringify_startup_script(filename):
    try:
        with open(filename, 'r') as f:
            script_text = f.read()
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)
    return script_text

# Verify user-specified Google Cloud resources
def verify_inputs(args):
    # required inputs
    if (not utils.verify_project(args.project)
            or not utils.verify_region(args.project, args.region)
            or not utils.verify_zone(args.project, args.region, args.zone)
            or not utils.verify_image(args.project, args.image)):
        return False

    if (not utils.verify_machine_type(
            args.project, args.zone, args.server_type)):
        return False

    if (not utils.verify_machine_type(
            args.project, args.zone, args.client_type)):
        return False

    # optional inputs
    if (args.subnet
            and not utils.verify_subnet(args.project, args.region, args.subnet)):
        return False

    if (args.server_policy
            and not utils.verify_policy(
                args.project, args.region, args.server_policy)):
        return False
    if (args.client_policy
            and not utils.verify_policy(
                args.project, args.region, args.client_policy)):
        return False

    return True

def setup_network_interface(opts):
    network_interface = {
        "accessConfigs": [
            {
                "type": "ONE_TO_ONE_NAT",
                "name": "External NAT",
                "networkTier": "PREMIUM"
            }
        ]
    }

    if opts.subnet:
        network_interface["subnetwork"] = opts.subnet

    if opts.nic_type:
        network_interface["nicType"] = opts.nic_type

    return network_interface

def setup_disks(opts, is_server):
    boot_disk = {
        "type": "PERSISTENT",
        "boot": "true",
        "initializeParams": {
            "sourceImage": opts.image
        },
        "autoDelete": "true"
    }

    if opts.nic_type == "GVNIC":
        boot_disk["guestOsFeatures"] = [
            {
                "type": "GVNIC"
            }
        ]

    disks = [boot_disk]

    if is_server and opts.server["num_ssd_per"] > 0:
        local_disk = {
            "type": "SCRATCH",
            "initializeParams": {
                "diskType": "local-ssd"
            },
            "autoDelete": "true",
            "interface": "NVME"
        }
        local_disks = [local_disk] * opts.server["num_ssd_per"]
        disks += local_disks

    return disks

def setup_instance_properties(opts, is_server, net_int, disks):
    instance_properties = {
        "advancedMachineFeatures": {
            "threadsPerCore": opts.threads_per_core
        },
        "networkInterfaces": [net_int],
        "disks": disks,
        "serviceAccounts": [
            {
                "scopes": opts.scopes
            }
        ]
    }

    if is_server:
        instance_properties["machineType"] = opts.server["type"]
        if "metadata" in opts.server:
            instance_properties["metadata"] = opts.server["metadata"]
        if "policy" in opts.server:
            instance_properties["resourcePolicies"] = [opts.server["policy"]]
    else:
        instance_properties["machineType"] = opts.client["type"]
        if "metadata" in opts.client:
            instance_properties["metadata"] = opts.client["metadata"]
        if "policy" in opts.client:
            instance_properties["resourcePolicies"] = [opts.client["policy"]]

    if "resourcePolicies" in instance_properties:
        instance_properties["scheduling"] = {
            "onHostMaintenance": "TERMINATE",
            "automaticRestart": "false"
        }

    if opts.startup_script:
        startup_metadata = {
            "key": "startup-script",
            "value": opts.startup_script
        }

        if "metadata" in instance_properties:
            instance_properties["metadata"]["items"].append(startup_metadata)
        else:
            instance_properties["metadata"] = {
                "items": [startup_metadata]
            }

    if opts.enable_tier1_networking:
        instance_properties["networkPerformanceConfig"] = {
            "totalEgressBandwidthTier": "TIER_1"
        }

    return instance_properties

def wait_for_operation(compute, operation, opts):
    print(f"Waiting for {operation['operationType']} operation to finish...",
          end=" ", flush=True)
    while True:
        try:
            result = compute.zoneOperations().wait(
                project=opts.project,
                zone=opts.zone,
                operation=operation['name']).execute()
        except (TimeoutError, socket.timeout):
            print("\b.", end=" ", flush=True)
            continue

        if result['status'] == 'DONE':
            print("done.")
            if 'error' in result:
                print(result['error'])
                raise Exception(result['error'])
            return result

def create_instances(compute, opts, network_interface, inst_type):
    if inst_type == OBInstType.SERVER:
        is_server = True
        count = opts.server["count"]
        name_pattern = f'{opts.server["prefix"]}##'
    else:
        is_server = False
        count = opts.client["count"]
        name_pattern = f'{opts.client["prefix"]}##'

    disks = setup_disks(opts, is_server)
    instance_properties = setup_instance_properties(
            opts, is_server, network_interface, disks)
    body = {
        "count": count,
        "namePattern": name_pattern,
        "instanceProperties": instance_properties
    }

    try:
        operation = compute.instances().bulkInsert(
            project=opts.project,
            zone=opts.zone,
            body=body).execute()
    except googleapiclient.errors.HttpError as e:
        error_msg = json.loads(e.content).get("error").get("message")
        print(f"Error: {error_msg}")
        sys.exit(1)

    wait_for_operation(compute, operation, opts)

if __name__ == "__main__":
    parser = initialize_parser()
    args = parser.parse_args()

    if args.num_servers + args.num_clients < 1:
        print("Error: Must specify at least one server or client.")
        sys.exit(1)

    if not verify_inputs(args):
        sys.exit(1)
    ob_opts = OBOptions(args)

    try:
        compute = googleapiclient.discovery.build('compute', 'v1')
    except google.auth.exceptions.DefaultCredentialsError:
        print(
            "No Google application credentials.\n"
            "Please do one of the following before re-running the script:\n"
            "1) Run `gcloud auth application-default login`\n"
            "OR\n"
            "2) Set the GOOGLE_APPLICATION_CREDENTIALS environment variable\n"
        )
        sys.exit(1)

    net_int = setup_network_interface(ob_opts)

    if args.num_servers > 0:
        create_instances(compute, ob_opts, net_int, OBInstType.SERVER)
    if args.num_clients > 0:
        create_instances(compute, ob_opts, net_int, OBInstType.CLIENT)
