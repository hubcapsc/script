#!/bin/bash

# Helper script for setting user limits on a group of IO500 instances.

UPDATE_CLIENTS=1
UPDATE_SERVERS=1

NUM_CLIENTS=4
NUM_SERVERS=4

CLIENT_PREFIX="pattern-io500-"
SERVER_PREFIX="pattern-ofs-"

set_user_limits() {
    instance_name=$1

    gcloud compute ssh $instance_name --command="sudo sh -c '
        cat >> /etc/security/limits.conf <<-EOF
        * - nproc unlimited
        * - memlock unlimited
        * - stack unlimited
        * - nofile 1048576
        * - cpu unlimited
        * - rtprio unlimited
        EOF'"
}

if [ "$UPDATE_CLIENTS" -gt "0" ]
then
    for i in `seq -w 01 $NUM_CLIENTS`
    do
        set_user_limits ${CLIENT_PREFIX}${i}
    done
fi

if [ "$UPDATE_SERVERS" -gt "0" ]
then
    for i in `seq -w 01 $NUM_SERVERS`
    do
        set_user_limits ${SERVER_PREFIX}${i}
    done
fi
