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

help() {
	echo
	echo "Usage: $0 [OPTION]... SERVER RELEASE"
	echo "Deploy RELEASE to SERVER"
	echo
	echo "	-y, --yes		answer yes"
	echo "	-h, --help		display this help and exit"
}

YES=false

PARAMS=""

while (( "$#" )); do
	case "$1" in
		-y | --yes ) YES=true; shift;;
		-h | --help ) help; exit 0;;
		-- ) shift; break;;
		-* | --*= ) echo "Error: Unsupported flag $1" >&2; help; exit 1;;
		* ) PARAMS="$PARAMS $1"; shift;;
	esac
done

eval set -- "$PARAMS"

if [ -z "$1" ] ; then
	echo "ERROR: No SERVER argument"
	help
	exit 1
fi

if [ -z "$2" ] ; then
	echo "ERROR: No RELEASE argument"
	help
	exit 1
fi

SERVER=$1
RELEASE=$2

if ! $YES; then
	read -p "Deploy $RELEASE to $SERVER? [y/n] " -n 1 -r
	echo    # (optional) move to a new line
	if [[ $REPLY =~ ^[Yy]$ ]]; then
	    YES=true
	fi
fi

if ! $YES; then
	exit 0
fi

# DEPLOY

ssh splunk@$SERVER rm -r /opt/pivt/staging/*

scp $RELEASE splunk@$SERVER:/opt/pivt/staging

if [ $? -ne 0 ]; then
	exit 2
fi

RELEASE_BASENAME=${RELEASE##*/}

ssh splunk@$SERVER /bin/bash << EOF
	tar -xzvf /opt/pivt/staging/$RELEASE_BASENAME -C /opt/pivt/staging
	cd /opt/pivt/staging/pivt-*
	chmod +x *.sh
	chmod -R g+w .

	export PIVT_HOME=/opt/pivt/pivt

	./configure.sh /opt/pivt \$PIVT_HOME /opt/pivt
	./install.sh -va

	cd \$PIVT_HOME/bin
	python3.5 -c 'from pivt.util import util; util.setup(); util.update_dashboards("/opt/splunk", None, get_new_date=False)'
	/opt/splunk/bin/splunk restart
EOF
