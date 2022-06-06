#!/bin/bash

# Helper script for enabling zone reclaim mode on a group of IO500
# instances.

# NOTE:
# At this point in time, enabling on the servers may cause issues with
# the pvfs2-server process. More investigation is needed.

UPDATE_CLIENTS=1
UPDATE_SERVERS=0

NUM_CLIENTS=4
NUM_SERVERS=4

CLIENT_PREFIX="pattern-io500-"
SERVER_PREFIX="pattern-ofs-"

ZONE_RECLAIM_MODE=1

set_zone_reclaim_mode() {
    instance_name=$1
    mode=$2

    cmd="sudo sysctl vm.zone_reclaim_mode=${mode}"
    gcloud compute ssh $instance_name --command="${cmd}"
}

if [ "$UPDATE_CLIENTS" -gt "0" ]
then
    for i in `seq -w 01 $NUM_CLIENTS`
    do
        set_zone_reclaim_mode ${CLIENT_PREFIX}${i} $ZONE_RECLAIM_MODE
    done
fi

if [ "$UPDATE_SERVERS" -gt "0" ]
then
    for i in `seq -w 01 $NUM_SERVERS`
    do
        set_zone_reclaim_mode ${SERVER_PREFIX}${i} $ZONE_RECLAIM_MODE
    done
fi
