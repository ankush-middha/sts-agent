#!/bin/sh

echo "Lines that might need renaming:"

grep -r etc/dd | grep -v README | grep -v CHANGELOG | grep -ve "^[^:]*:\\s*\#.*"
grep -r datadog\\.conf . | grep -v sts-check-naming | grep -v Binary | grep -v CHANGELOG | grep -ve "^[^:]*:\\s*\#.*" | grep -v README
grep -r ddagent.py . | grep -v sts-check-naming | grep -v Binary
grep -r opt/datadog . | grep -v sts-check-naming
grep -re "echo.*DataDog" . | grep -v sts-check-naming
