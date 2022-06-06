#!/bin/bash

# Helper script for setting TCP memory limits on a group of IO500
# instances.

UPDATE_CLIENTS=1
UPDATE_SERVERS=1

NUM_CLIENTS=4
NUM_SERVERS=4

CLIENT_PREFIX="pattern-io500-"
SERVER_PREFIX="pattern-ofs-"

update_tcp_mem() {
    instance_name=$1

    rmem="net.ipv4.tcp_rmem = 4096 131072 16777216"
    wmem="net.ipv4.tcp_wmem = 4096 16384 16777216"
    rmem_cmd="echo ${rmem} >> /etc/sysctl.conf"
    wmem_cmd="echo ${wmem} >> /etc/sysctl.conf"
    load_cmd="sysctl -p"
    ssh_cmd="sudo sh -c '${rmem_cmd}; ${wmem_cmd}; ${load_cmd}'"
    gcloud compute ssh $instance_name --command="${ssh_cmd}"
}

if [ "$UPDATE_CLIENTS" -gt "0" ]
then
    for i in `seq -w 01 $NUM_CLIENTS`
    do
        update_tcp_mem ${CLIENT_PREFIX}${i}
    done
fi

if [ "$UPDATE_SERVERS" -gt "0" ]
then
    for i in `seq -w 01 $NUM_SERVERS`
    do
        update_tcp_mem ${SERVER_PREFIX}${i}
    done
fi
