#!/bin/bash

# This script is meant to be passed to GCP instances at creation as a
# startup script to set various OS-level tuning parameters for optimal
# IO500 benchmark performance.

# used to prevent re-running this script on reboots
FLAG_FILE="/var/tmp/.setup_done"

# server and client options
TUNE_TCP_MEM=1
ENABLE_BUSY_POLL=1

# client-only options
ENABLE_HUGE_PAGES=1

# use instance metadata to determine if client or server
INST_TYPE=$(curl http://metadata.google.internal/computeMetadata/v1/instance/attributes/type -H "Metadata-Flavor: Google")

# only run at instance creation/first boot
if [ -e "$FLAG_FILE" ]
then
    exit
fi

# Client and Server Settings

# update tcp_*mem settings
if [ "$TUNE_TCP_MEM" -gt "0" ]
then
    rmem="net.ipv4.tcp_rmem = 4096 131072 16777216"
    wmem="net.ipv4.tcp_wmem = 4096 16384 16777216"
    echo "${rmem}" >> /etc/sysctl.conf
    echo "${wmem}" >> /etc/sysctl.conf
    sysctl -p
fi

# enable busy polling
if [ "$ENABLE_BUSY_POLL" -gt "0" ]
then
    busy_poll="net.core.busy_poll = 50"
    busy_read="net.core.busy_read = 50"
    echo "${busy_poll}" >> /etc/sysctl.conf
    echo "${busy_read}" >> /etc/sysctl.conf
    sysctl -p
fi

# Client-only Settings

if [ "$INST_TYPE" == "client" ]
then
    if [ "$ENABLE_HUGE_PAGES" -gt "0" ]
    then
        # enable transparent huge pages
        echo 'always' > /sys/kernel/mm/transparent_hugepage/enabled
        echo 'always' > /sys/kernel/mm/transparent_hugepage/defrag
    fi
fi

# create flag file to indidcate this script has already run
touch "$FLAG_FILE"
