#!/bin/bash

# Helper script for disabling Meltdown and Spectre mitigations on a
# group of IO500 instances. This can improve performance, but at the
# cost of potentially higher security risks.

# CAUTION: RUN THIS SCRIPT AT YOUR OWN RISK! This will disable
# protections for known security vulnerabilities, so only do this after
# carefully considering your specific environment and the implications
# of removing these protections. It is highly recommended that this is
# only run on development/testing systems with limited-access that you
# control and trust and NEVER on production systems and/or machines
# with public access. For more information, see the following link:
# https://cloud.google.com/architecture/best-practices-for-using-mpi-on-compute-engine#turn_off_meltdown_and_spectre_mitigation

UPDATE_CLIENTS=1
UPDATE_SERVERS=1

NUM_CLIENTS=4
NUM_SERVERS=4

CLIENT_PREFIX="pattern-io500-"
SERVER_PREFIX="pattern-ofs-"

# TODO: how can I reboot over ssh without getting the connection error?
disable_mitigations() {
    instance_name=$1

    cmd1="sudo sed -i 's/^GRUB_CMDLINE_LINUX=\"\(.*\)\"/GRUB_CMDLINE_LINUX=\"\1 mitigations=off\"/' /etc/default/grub"
    cmd2="sudo grub2-mkconfig -o /etc/grub2.cfg"
    cmd3="sudo shutdown -r now"
    ssh_cmd="${cmd1}; ${cmd2}; ${cmd3}"
    gcloud compute ssh $instance_name --command="${ssh_cmd}"
}

if [ "$UPDATE_CLIENTS" -gt "0" ]
then
    for i in `seq -w 01 $NUM_CLIENTS`
    do
        disable_mitigations ${CLIENT_PREFIX}${i}
    done
    echo "Mitigations disabled on all clients."
    echo "Remember to restart the OFS clients."
fi

if [ "$UPDATE_SERVERS" -gt "0" ]
then
    for i in `seq -w 01 $NUM_SERVERS`
    do
        disable_mitigations ${SERVER_PREFIX}${i}
    done
    echo "Mitigations disabled on all servers."
    echo "Remmber to restart the OFS servers."
fi
