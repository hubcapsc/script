#!/bin/bash

# Helper script to enable busy polling on a group of IO500 instances.

UPDATE_CLIENTS=1
UPDATE_SERVERS=1

NUM_CLIENTS=4
NUM_SERVERS=4

CLIENT_PREFIX="pattern-io500-"
SERVER_PREFIX="pattern-ofs-"

enable_busy_polling() {
    instance_name=$1

    busy_poll="net.core.busy_poll = 50"
    busy_read="net.core.busy_read = 50"
    bp_cmd="echo ${busy_poll} >> /etc/sysctl.conf"
    br_cmd="echo ${busy_read} >> /etc/sysctl.conf"
    load_cmd="sysctl -p"
    ssh_cmd="sudo sh -c '${bp_cmd}; ${br_cmd}; ${load_cmd}'"
    gcloud compute ssh $instance_name --command="${ssh_cmd}"
}

if [ "$UPDATE_CLIENTS" -gt "0" ]
then
    for i in `seq -w 01 $NUM_CLIENTS`
    do
        enable_busy_polling ${CLIENT_PREFIX}${i}
    done
fi

if [ "$UPDATE_SERVERS" -gt "0" ]
then
    for i in `seq -w 01 $NUM_SERVERS`
    do
        enable_busy_polling ${SERVER_PREFIX}${i}
    done
fi
