#!/bin/bash

set -ae

AWS_DEFAULT_REGION=${AWS_REGION:-us-east-1}
: ${ECS_CLUSTER_NAME:=default}
: ${RESOURCE_CHECK_INTERVAL:=60}

SCRIPT_DIR=$( cd ${0%/*} && pwd -P )
"$SCRIPT_DIR/ecspander.py" --cluster $ECS_CLUSTER_NAME
