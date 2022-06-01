#!/bin/bash

# Helper script for restarting the OrangeFS server on a group of OFS
# server instances.

NUM_SERVERS=16
SERVER_PREFIX="pattern-ofs-"
OFS_CONFIG_FILE_NAME="orangefs.conf"
PORT="3334"

for i in `seq -w 01 $NUM_SERVERS`
do
    instance_name="${SERVER_PREFIX}${i}"
    server_alias="${instance_name}_tcp${PORT}"
    cmd="sudo pvfs2-server ${OFS_CONFIG_FILE_NAME} -a ${server_alias}"
    gcloud compute ssh ${SERVER_PREFIX}${i} --command="${cmd}"
done
