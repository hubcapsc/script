from enum import Enum

import googleapiclient.discovery

class OBInstType(Enum):
    SERVER = 1
    CLIENT = 2

class OBOptions:
    project = "orangefsdev"
    region = "us-central1"
    zone = "us-central1-a"

    image_name = "hubcap-io500-oiv1"
    image_path = f"global/images/{image_name}"
    scopes = "https://www.googleapis.com/auth/cloud-platform"
    subnet_name = "io500-central1-sn"
    subnet_path = f"regions/{region}/subnetworks/{subnet_name}"
    policy_name = "python-io500-2-pg"

    nic_type = "GVNIC"
    use_tier1_networking = True

    server_count = 1
    client_count = 1
    server_machine_type = "c2-standard-30"
    client_machine_type = "c2-standard-30"
    server_name_prefix = "python-ofs-"
    client_name_prefix = "python-io500-"

    num_ssds_per_instance = 4


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

    if opts.subnet_name and opts.region:
        subnet_path = f"regions/{opts.region}/subnetworks/{opts.subnet_name}"
        network_interface["subnetwork"] = subnet_path

    if opts.nic_type:
        network_interface["nicType"] = opts.nic_type

    return network_interface

def setup_disks(opts, is_server):
    boot_disk = {
        "type": "PERSISTENT",
        "boot": "true",
        "initializeParams": {
            "sourceImage": opts.image_path
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

    if is_server and opts.num_ssds_per_instance > 0:
        local_disk = {
            "type": "SCRATCH",
            "initializeParams": {
                "diskType": "local-ssd"
            },
            "autoDelete": "true",
            "interface": "NVME"
        }
        local_disks = [local_disk] * opts.num_ssds_per_instance
        disks += local_disks

    return disks

def setup_instance_properties(opts, is_server, net_int, disks):
    instance_properties = {
        "networkInterfaces": [net_int],
        "disks": disks,
        "serviceAccounts": [
            {
                "scopes": [opts.scopes]
            }
        ]
    }

    if is_server:
        instance_properties["machineType"] = opts.server_machine_type
    else:
        instance_properties["machineType"] = opts.client_machine_type

    if opts.policy_name:
        instance_properties["resourcePolicies"] = [opts.policy_name]
        instance_properties["scheduling"] = {
            "onHostMaintenance": "TERMINATE",
            "automaticRestart": "false"
        }

    if opts.use_tier1_networking:
        instance_properties["networkPerformanceConfig"] = {
            "totalEgressBandwidthTier": "TIER_1"
        }

    return instance_properties

def create_instances(compute, opts, network_interface, inst_type):
    if inst_type == OBInstType.SERVER:
        is_server = True
        name_pattern = f"{opts.server_name_prefix}#"
    else:
        is_server = False
        name_pattern = f"{opts.client_name_prefix}#"

    disks = setup_disks(opts, is_server)
    instance_properties = setup_instance_properties(
            opts, is_server, network_interface, disks)
    body = {
        "count": opts.client_count,
        "namePattern": name_pattern,
        "instanceProperties": instance_properties
    }

    compute.instances().bulkInsert(
            project=opts.project,
            zone=opts.zone,
            body=body).execute()


if __name__ == "__main__":
    ob_opts = OBOptions()

    compute = googleapiclient.discovery.build('compute', 'v1')

    network_interface = setup_network_interface(ob_opts)
    create_instances(compute, ob_opts, network_interface, OBInstType.SERVER)
    create_instances(compute, ob_opts, network_interface, OBInstType.CLIENT)
