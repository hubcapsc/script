# README

## Introduction

This repo contains two scripts:

- `script`
- `bulk_create.py`

The first, `script`, is a tool to launch a GCP environment that consists of
OrangeFS servers and clients that are pre-configured for the IO500 benchmark.
It is written in Bash. Optionally, the IO500 benchmark can be set to run automatically upon environment creation.

The second, `bulk_create.py`, is a Python script that utilizes Google's Python
bulk API to create a set of instances. It is used by the main bash script but
can also be run as a standalone tool to launch instances without configuring
them for OrangeFS or IO500.

## Assumptions

These instructions assume the following already exist:

- Google Cloud Account
- Google Cloud Project
- Google Cloud Storage Bucket

## Getting Started

1. Install Prerequisites

   ```no-highlight
   sudo dnf install -y nc perl
   ```

   **NOTE:** Most systems come with Perl pre-installed but may not have the
   modules required by the `pvfs2-genconfig` script. Installing via the command
   above installs `perl` and all of its modules/dependencies. If your system
   has a pre-installed version and you wish to install *only* the modules that
   are strictly necessary, use the following command instead:

   ```no-highlight
   sudo dnf install -y nc perl-Term-ReadLine perl-Getopt-Long perl-Math-BigInt perl-FindBin
   ```

2. Install `pvfs2-genconfig`

   **NOTE:** If you are on a system that has OrangeFS installed, you can skip
   this step as long as the `pvfs2-genconfig` script is located in `/usr/bin/`.
   If you wish to install OrangeFS, follow the instructions in the
   [OrangeFS documentation](http://docs.orangefs.com/quickstart/quickstart-package/) and then skip to Step 3.

   If you are not running on a system with OrangeFS installed, use the
   following commands to download and install the `pvfs2-genconfig` script:

   ```
   curl -O https://raw.githubusercontent.com/waltligon/orangefs/master/src/apps/admin/pvfs2-genconfig
   sudo mv pvfs2-genconfig /usr/bin/
   chmod 755 /usr/bin/pvfs2-genconfig
   ```

3. Install Required Python Packages

   **NOTE:** It is recommended (though not required) to do this inside a
   Python virtual environment (see <https://docs.python.org/3/tutorial/venv.html#creating-virtual-environments>).

   ```no-highlight
   python -m pip install -r requirements.txt
   ```

4. [Install Google Cloud SDK and `gcloud`](https://cloud.google.com/sdk/docs/install)

5. Set Application Default Credentials

   **NOTE**: This step can be skipped if either of the following is true:
   - You are running the script from a Google Compute Engine virtual machine.
   - You have disabled the bulk-create feature in `script` and do not plan to
     use `bulk_create.py` as a standalone script.

   Run the following command and follow the instructions:

   ```no-highlight
   gcloud auth application-default login
   ```

   You will be asked to log into your Google Cloud account and copy a
   verification code. This sets up the credentials needed to authenticate
   Google client API calls.

6. Setup SSH Keys

   The instances launched by the script use metadata-based SSH keys, so in
   order to communicate with them, the machine running the script needs to have
   the private key corresponding to a public key that has been added to your
   Google Cloud project. You can create a new key pair or use an existing one
   for this purpose. Follow Google's instructions to learn how to
   [Add SSH Keys to Project Metadata](https://cloud.google.com/compute/docs/connect/add-ssh-keys#add_ssh_keys_to_project_metadata).

   Depending on your environment and the name of your key pair, you may need to
   ensure the ssh-agent is running and the corresponding identity has been
   added to it. To start the agent and add an identity, use the following
   commands:

   ```no-highlight
   eval `ssh-agent -s`
   ssh-add ~/.ssh/<KEY_FILE>
   ```

   ... where `<KEY_FILE>` is the name of the private key corresponding to the
   public key you added to your project metadata.

7. Set Config Options

   There are several options in the script that can be changed to configure
   your Google Cloud settings and customize your environment and how IO500 is
   run. See [Configurable Script Options](#configurable-script-options) below
   for more details.

8. Run `script`

   ```no-highlight
   ./script
   ```

   **NOTE:** This will create instances and a resource policy (if enabled) in your Google Cloud project. Be sure to delete these when you are done with
   them to avoid unnecessary charges to your account. See
   [Cleaning Up](#cleaning-up).

## Results and IO500

When the script is finished, your instances will be running in your Google
Cloud project. You should be able to connect to them using the SSH key you
added to your project metadata. Assuming your account has the necessary access
for the resources you requested, you should have the specified number of server
and client instances, with an OrangeFS filesystem distributed across the
servers and each client instance running as an OrangeFS client.

### IO500 Clients

Each client has three distinct `io500` directories corresponding to each flavor
of MPI:

- `/home/io500_vanilla/io500`
- `/home/io500_openmpi/io500`
- `/home/io500_intel/io500`

Within each is an `io500` executable that has been compiled for that version of
MPI. If you configured the script to automatically run IO500 by setting
`OB_RUN_IO500`, this is also where you will find the IO500 `results` directory.

**NOTE:** You may notice a file `io500.sh` is also in this directory. However,
that is the default script from the IO500 repo, NOT the script you may have
customized and uploaded to the bucket specified by the `OB_BUCKET` option. By
default, your custom script and .ini configuration file are located here:

- `/var/tmp/io500.sh`
- `/var/tmp/config-custom.ini`

See [`OB_BUCKET`](#ob_bucket) below for more information about these files.

### Running IO500 Manually

If you did not set `OB_RUN_IO500`, you can run it manually after the instances
have been launched. However, before doing so you will need to configure the
environment for your desired flavor of MPI by running a setup script. As a
reminder, the following commands should be run on the first IO500 client
instance.

For vanilla MPI (a.k.a. MPICH), run:
```no-highlight
. /home/io500_vanilla/setvars_vanilla.sh
```

For OpenMPI, run:
```no-highlight
. /home/io500_openmpi/setvars_openmpi.sh
```

For Intel MPI, run:
```no-highlight
. /opt/intel/oneapi/setvars.sh
```

Once you have run the setup script, you can then run IO500 using the following
commands:

```no-highlight
cd /home/io500_<MPI_TYPE>/io500
chmod u+x /var/tmp/io500.sh
/var/tmp/io500.sh /var/tmp/config-custom.ini
```

... where `<MPI_TYPE>` is either `vanilla`, `openmpi`, or `intel`.

## Cleaning Up

The script will create a number of server and client instances in your Google
Cloud project. If the configuration option `OB_USE_PLACEMENT_GROUP` is set, a
resource policy will also be created. To avoid incurring unwanted charges to
your Google Cloud account or cluttering up your project with unused policies,
be sure to delete these resources when you are finished with them.

### Deleting Instances

Google Compute Engine instances can be deleted through the
[Google Cloud Console](https://console.cloud.google.com/compute/instances).
If you prefer the command line, it can be done using the gcloud CLI as follows:

```no-highlight
gcloud compute instances delete <INSTANCE_NAME>
```

You can specify multiple instance names, separated by spaces, to delete more
than one at a time.

### Deleting Resource Policies

Unlike instances, resource policies cannot be deleted from the Google Cloud
Console, so the gcloud CLI must be used.

You can list the resource policies in your project with the following command:

```no-highlight
gcloud compute resource-policies list
```

To delete a policy, copy the policy name from the output of the above command,
then use the `delete` command:

```no-highlight
gcloud compute resource-policies delete <POLICY_NAME>
```

## Configurable Script Options

| Option Name | Description |
| ----------- | ----------- |
| `OB_REGION` | Name of GCP region to launch instances in |
| `OB_ZONE` | Name of GCP zone to launch instances in |
| `OB_PROJECT` | GCP project ID |
| `OB_MPI_TYPE` | Version of MPI to use ("intel", "openmpi", or "vanilla") |
| `OB_SLOTS` | Number of slots (processors) per MPI host |
| `OB_RUN_IO500` | Set to 1 to run IO500 upon environment creation |
| `OB_BUCKET` | Google Cloud Storage bucket containing config files (see [below](#ob_bucket)) |
| `OB_OFS_NAME` | String to begin all server names with |
| `OB_IO500_NAME` | String to begin all client names with |
| `OB_OFS_SERVERS` | Number of OrangeFS server instances to launch |
| `OB_IO500_CLIENTS` | Number of IO500 client instances to launch |
| `OB_OFS_MACHINE` | GCP machine type to use for servers |
| `OB_IO500_MACHINE` | GCP machine type to use for clients |
| `OB_SSD_NUM` | Number of local NVMe drives to attach to each server instance |
| `OB_USE_PLACEMENT_GROUP`| Set to 1 to launch instances with a compact placement policy |
| `OB_POLICY_PREFIX` | String to begin the resource policy name with |
| `OB_SUBNET` | Name of subnetwork to launch instances in |
| `OB_NIC_TYPE` | Set to "GVNIC" if Tier 1 network performance is desired |
| `OB_USE_TIER1_NET` | Set to 1 if Tier 1 network performance is desired |
| `OB_STARTUP_SCRIPT` | Local path to a script to run on each instance upon launch |

This is not an exhaustive list of available options, but these are the most likely options a new user will first want to change. There are more options
that can be used to customize the behavior and performance of the OrangeFS
filesystem.

### `OB_BUCKET`

The `OB_BUCKET` option should be set to the gsutil URI of a Google Cloud
Storage bucket containing at least the following three files:

- `io500.sh`: a valid IO500 script
- `config-custom.ini`: a valid IO500 configuration file
- `openmpivars`: see the [next section](#openmpivars-file)

See <https://github.com/IO500/io500> for more information on the IO500 script
and .ini configuration file.

#### `openmpivars` File

**NOTE:** If you never plan to use OpenMPI, this file can be excluded.

This file must contain the appropriate `PATH` and `LD_LIBRARY_PATH` for the
OpenMPI installation on the image used to create your instances. For the
default `OB_IMAGE`, the `openmpivars` file looks like this (a standard OpenMPI
installation):

```no-highlight
PATH="/opt/openmpi-4.1.1/bin:$PATH"
LD_LIBRARY_PATH="/opt/openmpi-4.1.1/lib:$LD_LIBRARY_PATH"
```
