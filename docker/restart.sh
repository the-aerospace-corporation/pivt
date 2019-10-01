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

ENVIRONMENT="dev"

OPTS=`getopt -o e: --long environment: -n 'parse-options' -- "$@"`
if [ $? != 0 ] ; then
    echo "Incorrect options provided"
    exit 1
fi

eval set -- "$OPTS"

while true; do
	case "$1" in
		-e | --environment ) ENVIRONMENT="$2"; shift 2;;
		-- ) shift; break;;
		* ) break;;
	esac
done

if [ $ENVIRONMENT != "prod" ] && [ $ENVIRONMENT != "dev" ] && [ $ENVIRONMENT != "ft" ] ; then
	echo "environment must be 'prod', 'aero-prod', 'aero-dev', or 'aero-ft', not $ENVIRONMENT"
	exit 2
fi

SCRIPTDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SCRIPTDIR=${SCRIPTDIR/\/cygdrive\/c\//C:\/}
SCRIPTDIR=${SCRIPTDIR/\/c\//C:\/}

$SCRIPTDIR/stop.sh
$SCRIPTDIR/start.sh -e $ENVIRONMENT
