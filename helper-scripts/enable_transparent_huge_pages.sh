#!/bin/bash

# Helper script for enabling transparent huge pages on a group of
# IO500 client instances.

# NOTE:
# At this point in time, enabling on the servers may cause issues with
# the pvfs2-server process. More investigation is needed.

UPDATE_CLIENTS=1
UPDATE_SERVERS=0

NUM_CLIENTS=4
NUM_SERVERS=4

CLIENT_PREFIX="pattern-io500-"
SERVER_PREFIX="pattern-ofs-"

enable_transparent_huge_pages() {
    instance_name=$1

    cmd1="echo 'always' > /sys/kernel/mm/transparent_hugepage/enabled"
    cmd2="echo 'always' > /sys/kernel/mm/transparent_hugepage/defrag"
    gcloud compute ssh $instance_name --command="sudo sh -c '${cmd1}; ${cmd2}'"
}

if [ "$UPDATE_CLIENTS" -gt "0" ]
then
    for i in `seq -w 01 $NUM_CLIENTS`
    do
        enable_transparent_huge_pages ${CLIENT_PREFIX}${i}
    done
fi

if [ "$UPDATE_SERVERS" -gt "0" ]
then
    for i in `seq -w 01 $NUM_SERVERS`
    do
        enable_transparent_huge_pages ${SERVER_PREFIX}${i}
    done
fi
