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

CONTAINER="pivt"

OPTS=`getopt -o c: --long container: -n 'parse-options' -- "$@"`
if [ $? != 0 ] ; then
    echo "Incorrect options provided"
    exit 1
fi

eval set -- "$OPTS"

while true; do
	case "$1" in
		-c | --container ) CONTAINER="$2"; shift 2;;
		-- ) shift; break;;
		* ) break;;
	esac
done

# we use '... || true' to handle non-zero error codes.
# both commands below return a non-zero code when the
# container doesn't exist
docker stop $CONTAINER || true
docker rm -v $CONTAINER || true
