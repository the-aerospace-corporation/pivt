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

environment="dev"
network=""
container="pivt"
port="8000"
image="pivt"
keep_running=false

opts=`getopt -o e:n:c:p:i:r --long environment:,network:,container:,port:,image:,keep-running -n 'parse-options' -- "$@"`
if [ $? != 0 ] ; then
    echo "Incorrect options provided"
    exit 1
fi

eval set -- "$opts"

while true; do
	case "$1" in
		-e | --environment ) environment="$2"; shift 2;;
		-n | --network ) network="--network=$2"; shift 2;;
		-c | --container ) container="$2"; shift 2;;
		-p | --port ) port="$2"; shift 2;;
		-i | --image ) image="$2"; shift 2;;
		-r | --keep-running ) keep_running=true; shift;;
		-- ) shift; break;;
		* ) break;;
	esac
done

if [ $environment != "prod" ] && [ $environment != "dev" ] && [ $environment != "ft" ]; then
	echo "environment must be 'prod', 'dev', or 'ft', not $environment"
	exit 2
fi

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
script_dir=${script_dir/\/cygdrive\/c\//C:\/}
script_dir=${script_dir/\/c\//C:\/}

root_dir=$script_dir/..

splunk_start_args="--accept-license --answer-yes"
pivt_home="//app/pivt"
tz="America/Los_Angeles"

general_cmd=""
if [ $environment == "ft" ]; then
	general_cmd="cd bin && python3 -m pivt.process && chown -R \`stat -c \"%u:%g\" $pivt_home/var/data\` $pivt_home/var/data && echo 'run functests now!'"
fi

volumes=""

if [ $environment == "dev" ] ; then
	volumes="$volumes -v $root_dir/data:$pivt_home/var/data -v $root_dir/pivt:$pivt_home/bin -v $root_dir/splunk-app:/opt/splunk/etc/apps/pivt -v $root_dir/cfg/default:$pivt_home/etc/default -v $root_dir/cfg/pivt.version:$pivt_home/etc/pivt.version"
elif [ $environment == "ft" ] ; then
	volumes="$volumes -v $root_dir/functests/ft-data:$pivt_home/var/data"
fi

if [ $environment == "ft" ] && ! $keep_running; then
	ports=""
else
	ports="-p $port:8000 -p 8089:8089"
fi

docker run -d --name $container -e "SPLUNK_START_ARGS=$splunk_start_args" -e "PIVT_HOME=$pivt_home" -e "TZ=$tz" -e "GENERAL_CMD=$general_cmd" $ports $network $volumes $image
