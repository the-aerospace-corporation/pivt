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

NORELEASE=false
KEEPRUNNING=false
port="3000"

OPTS=`getopt -o tr --long no-release,keep-running -n 'parse-options' -- "$@"`
if [ $? != 0 ] ; then
    echo "Incorrect options provided"
    exit 1
fi

eval set -- "$OPTS"

while true; do
	case "$1" in
		-t | --no-release ) NORELEASE=true; shift;;
		-r | --keep-running) KEEPRUNNING=true; shift;;
		-- ) shift; break;;
		* ) break;;
	esac
done

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

### PREPARE FT DATA

echo "Create ft-data/collected and copy resources into collected"
mkdir -p $ROOTDIR/functests/ft-data || exit 3

function cleanup1() {
	echo "Remove ft-data"
	rm -r $ROOTDIR/functests/ft-data
}

cp -r $ROOTDIR/functests/resources/* $ROOTDIR/functests/ft-data/ || { cleanup1; exit 4; }

### BUILD FT IMAGE

image_ft=pivt-ft-$(uuidgen) || { cleanup1; exit 5; }

echo "Building $image_ft"
args="-e ft -n $image_ft"
if $NORELEASE; then
	args="$args --no-release"
fi

$SCRIPTDIR/build.sh $args || { cleanup1; exit 6; }

function cleanup2() {
	echo "Remove $image_ft"
	docker image rm $image_ft

	cleanup1
}

### START FT CONTAINER

container_ft=pivt-ft-$(uuidgen) || { cleanup2; exit 7; }

echo "Start pivt container - $container_ft"
args="-e ft -c $container_ft -i $image_ft"
if $KEEPRUNNING; then
	args="$args -p $port -r"
fi
$SCRIPTDIR/start.sh $args || { cleanup2; exit 8; }

function cleanup3() {
	echo "$container_ft logs:"
	docker logs $container_ft

	echo "Stop and remove $container_ft"
	$SCRIPTDIR/stop.sh -c $container_ft

	cleanup2
}

### CREATE NETWORK

network=pivt-network-$(uuidgen) || { cleanup3; exit 9; }

echo "Creating $network"
docker network create -d bridge $network || { cleanup3; exit 10; }

function cleanup4() {
	cleanup3

	echo "Remove Network - $network"
	docker network rm $network
}

### ATTACH CONTAINER_FT TO NETWORK

echo "Attaching pivt container to network"
docker network connect $network $container_ft || { cleanup4; exit 11; }

### GET FUNCTESTS

echo "Copying functests into docker directory"
cp -r $ROOTDIR/functests/ $SCRIPTDIR/ || { cleanup4; exit 12; }

function cleanup5() {
	echo "Remove temp functests directory"
	rm -r $SCRIPTDIR/functests

	cleanup4
}

### BUILD FUNCTEST IMAGE

image_functest=pivt-functest-$(uuidgen) || { cleanup5; exit 13; }

echo "Building $image_functest"
docker build -t $image_functest -f $SCRIPTDIR/Dockerfile.functest $SCRIPTDIR/ || { cleanup5; exit 14; }

function cleanup6() {
	echo "Remove $image_functest"
	docker image rm $image_functest

	cleanup5
}

### WAIT FOR FT CONTAINER TO START

echo "Read $container_ft logs and run $image_functest when splunk is done starting"

declare -i i=0

while true; do
	docker logs 2>&1 $container_ft | grep "run functests now!"
	if [ $? -ne 0 ]; then
		sleep 10
		((i++))
	else
		break
	fi

	if [ $i -gt 10 ]; then
		echo "ERROR! TERMINATING! - Splunk took over 100 seconds to start in $container_ft."
		cleanup6
		exit 15
	fi
done

echo "pivt container started. Wating 20 seconds for data ingest..."

sleep 20

### START FUNCTEST CONTAINER

container_functest=pivt-functest-$(uuidgen) || { cleanup6; exit 16; }

echo "Start $container_functest"
docker run --network="$network" --name $container_functest -e PIVT_HOST=$container_ft -v $ROOTDIR/functests/ft-data:/app/ft-data/ $image_functest || { cleanup6; exit 17; }

function cleanup7() {
	echo "Stop and remove $container_functest"
	$SCRIPTDIR/stop.sh -c $container_functest

	cleanup6
}

### EXTRACT REPORT FILES

echo "Extracting report files"
docker cp $container_functest:/data/ft_report.json $SCRIPTDIR/ || { cleanup7; exit 18; }

function keep_running {
	read -n 1 -p "Type 'x' to terminate program: " userinput
	if [ "$userinput" = "x" ]; then
		echo ""
		cleanup7
	else
		echo " Invalid command"
		keep_running
	fi
}

### KEEP RUNNING OR CLEANUP AND EXIT

if $KEEPRUNNING; then
	echo "Continuing to run for functional testing"
	echo "Container: $container_ft"
	echo "Network: $network"

	keep_running
else
	cleanup7
fi

echo "Done functional testing."
