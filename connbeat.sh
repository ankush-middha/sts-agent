#!/bin/bash

export STSURL="`grep -m 1 '^dd_url: ' /etc/sts-agent/stackstate.conf | sed 's/^dd_url: //'`"
export APIKEY="`grep -m 1 '^api_key: ' /etc/sts-agent/stackstate.conf | sed 's/^api_key: //'`"

exec /opt/stackstate-agent/bin/connbeat -c /etc/sts-agent/connbeat.yml -path.logs /var/log/stackstate -path.data /var/lib/stackstate/connbeat
