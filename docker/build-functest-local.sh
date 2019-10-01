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

echo "Copying functests into docker directory"
cp -r $ROOTDIR/functests/ $SCRIPTDIR/ || exit 4

function cleanup1() {
	echo "Remove temp functests directory"
	rm -r $SCRIPTDIR/functests
}

echo "Building functest-local"
docker build -t functest-local -f $SCRIPTDIR/Dockerfile.functest $SCRIPTDIR/ || { cleanup1; exit 1; }

cleanup1
