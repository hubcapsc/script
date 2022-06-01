#!/bin/bash

# Helper script for restarting and remounting the OrangeFS client on
# a group of IO500 client instances.

NUM_CLIENTS=10
CLIENT_PREFIX="pattern-io500-"
SERVER_ADDR="pattern-ofs-01"
PORT="3334"
MNTDIR="/pvfsmnt"

for i in `seq -w 01 $NUM_CLIENTS`
do
    gcloud compute ssh ${CLIENT_PREFIX}${i} --command="\
        sudo modprobe orangefs; \
        sudo pvfs2-client -p /usr/sbin/pvfs2-client-core; \
        sudo mount -t pvfs2 tcp://${SERVER_ADDR}:${PORT}/orangefs ${MNTDIR}"
done
