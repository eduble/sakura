#!/bin/bash

daemon_index="$1"
shift

cd $(dirname $0)/..
TMPDIR=$(mktemp -d /tmp/daemon$daemon_index.XXXXXXXX)
export PYTHONUNBUFFERED=1

on_exit()
{
    rm -rf $TMPDIR
}

# whatever happens, call at_exit() at the end.
trap on_exit EXIT

CUSTOM_DATASTORES_CONF="$PWD/test/daemon${daemon_index}-datastores.conf"
if [ -f "$CUSTOM_DATASTORES_CONF" ]
then
    DATASTORES_CONF="$(cat "$CUSTOM_DATASTORES_CONF")"
else
    DATASTORES_CONF="[ ]"
fi

cat > $TMPDIR/daemon.conf << EOF
{
    "hub-host": "localhost",
    "hub-port": 10432,
    "daemon-desc": "daemon $daemon_index",
    "work-dir": "$HOME/.sakura/daemon$daemon_index",
    "data-stores": $DATASTORES_CONF
}
EOF
# Sample data-store configuration:
#   [...]
#   "data-stores": [
#       {
#           "host": "<dbms-ip-or-hostname>",
#           "datastore-admin": {
#               "user":             "<dbms-admin-user>",
#               "encoded-password": "<dbms-admin-encoded-password>"
#           },
#           "sakura-admin": "<sakura-username>",
#           "access-scope": "<public|restricted|private>",
#           "driver": "postgresql"
#       }
#   ]
#   [...]
#
# Use sakura-encode-password to encode your passwords.

PYTHONPATH="$PWD" sakura/daemon/daemon.py -f $TMPDIR/daemon.conf
