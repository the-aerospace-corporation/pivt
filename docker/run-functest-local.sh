#!/bin/bash

# Copyright 2019 The Aerospace Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

pivt_containers=`docker container ls --format "{{.Names}}" | grep pivt-ft-`
num_containers=`echo $pivt_containers | wc -l`
if [ $num_containers == 1 ]; then
    pivt_container=$pivt_containers
    echo "Found pivt-ft container ($pivt_container)"
elif [ $num_containers < 1 ]; then
    echo "No pivt-ft containers running! Exiting"
    exit 1
else
    echo "Multiple pivt-ft containers! Exiting"
    exit 2
fi

pivt_networks=`docker network ls --format "{{.Name}}" | grep pivt-network-`
num_networks=`echo $pivt_networks | wc -l`
if [ $num_networks == 1 ]; then
    pivt_network=$pivt_networks
    echo "Found pivt network ($pivt_network)"
elif [ $num_networks < 1 ]; then
    echo "No pivt networks up! Exiting"
    exit 3
else
    echo "Multiple pivt networks! Exiting"
    exit 4
fi

echo "Docker environment:"
docker --version

SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SCRIPTDIR=${SCRIPTDIR/\/cygdrive\/c\//C:\/}
SCRIPTDIR=${SCRIPTDIR/\/c\//C:\/}

ROOTDIR=$SCRIPTDIR/../

echo "Script location:"
echo $SCRIPTDIR

echo "Root location:"
echo $ROOTDIR

echo "run container-ft-local"
docker run --network=$pivt_network --name "container-ft-local" -e PIVT_HOST=$pivt_container -v $ROOTDIR/functests/:/app functest-local

echo "stop container or true"
docker stop container-ft-local || true

echo "remove container or true"
docker rm -v container-ft-local || true
