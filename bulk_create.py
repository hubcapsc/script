import argparse
import sys
from enum import Enum

import googleapiclient.discovery
import google.auth.exceptions

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

        self.policy = args.policy
        self.nic_type = args.nic_type
        self.enable_tier1_networking = args.enable_tier1_networking

        self.server = {
            "count": args.num_servers,
            "type": args.server_type,
            "prefix": args.server_prefix,
            "num_ssd_per": args.num_ssd_per_server
        }

        self.client = {
            "count": args.num_clients,
            "type": args.client_type,
            "prefix": args.client_prefix
        }



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
            "--policy",
            default=None,
            help="name of resource policy to apply to instances")
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
            "--num-ssd-per-server",
            type=int,
            default=0,
            help="number of local SSDs to attach to each server instance")

    return parser

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
    else:
        instance_properties["machineType"] = opts.client["type"]

    if opts.policy:
        instance_properties["resourcePolicies"] = [opts.policy]
        instance_properties["scheduling"] = {
            "onHostMaintenance": "TERMINATE",
            "automaticRestart": "false"
        }

    # TODO: check that nic-type is set to "GVNIC"
    if opts.enable_tier1_networking:
        instance_properties["networkPerformanceConfig"] = {
            "totalEgressBandwidthTier": "TIER_1"
        }

    return instance_properties

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

    compute.instances().bulkInsert(
            project=opts.project,
            zone=opts.zone,
            body=body).execute()

if __name__ == "__main__":
    parser = initialize_parser()
    args = parser.parse_args()
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

    network_interface = setup_network_interface(ob_opts)
    create_instances(compute, ob_opts, network_interface, OBInstType.SERVER)
    create_instances(compute, ob_opts, network_interface, OBInstType.CLIENT)
