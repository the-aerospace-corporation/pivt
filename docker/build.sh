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
NORELEASE=false
NAME="pivt"

OPTS=`getopt -o e:tn:b:f: --long environment:,no-release,name: -n 'parse-options' -- "$@"`
if [ $? != 0 ] ; then
    echo "Incorrect options provided"
    exit 1
fi

eval set -- "$OPTS"

while true; do
	case "$1" in
		-e | --environment ) ENVIRONMENT="$2"; shift 2;;
		-t | --no-release ) NORELEASE=true; shift;;
		-n | --name ) NAME="$2"; shift 2;;
		-- ) shift; break;;
		* ) break;;
	esac
done

if [ $ENVIRONMENT != "prod" ] && [ $ENVIRONMENT != "dev" ] && [ $ENVIRONMENT != "ft" ]; then
	echo "environment must be 'prod', 'dev', or 'ft', not $ENVIRONMENT"
	exit 2
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

license=$SCRIPTDIR/Splunk.License.lic
if [ ! -f $license ]; then
	echo "No Splunk license in $SCRIPTDIR! ($license)"
	exit 3
fi

if [ $ENVIRONMENT != "dev" ]; then
	if ! $NORELEASE; then
		source $ROOTDIR/release.sh --no-md5 version || exit 4
		mv $release $SCRIPTDIR || { rm $release; exit 5; }
		release=$SCRIPTDIR/${release##*/}
	else
		release=$(find $SCRIPTDIR -name aero-pivt*.tar.gz)

		if [ $(echo $release | wc -w) -gt 1 ]; then
			echo "More than one release in $SCRIPTDIR directory! Exiting."
			exit 6
		fi

		echo "Release: $release"
	fi

	release_basename=${release##*/}
fi

function cleanup1() {
	if [ $ENVIRONMENT != "dev" ] && ! $NORELEASE; then
		rm $release
	fi
}

echo "Copying splunk_etc"
if [ $ENVIRONMENT == "ft" ]; then
	etc_dir="$SCRIPTDIR/splunk_etc_ft"
else
	etc_dir="$SCRIPTDIR/splunk_etc_default"
fi

cp -r $etc_dir $SCRIPTDIR/splunk_etc || { cleanup1; exit 7; }

function cleanup2() {
	rm -r $SCRIPTDIR/splunk_etc
	cleanup1
}

etc_license_dir=$SCRIPTDIR/splunk_etc/licenses/enterprise
mkdir -p $etc_license_dir || { cleanup2; exit 8; }
cp $license $etc_license_dir || { cleanup2; exit 9; }

echo "Building $NAME docker image"
if [ $ENVIRONMENT != "dev" ]; then
	dockerfile="$SCRIPTDIR/Dockerfile.prod"
else
	dockerfile="$SCRIPTDIR/Dockerfile"
fi

docker build -t $NAME -f $dockerfile --build-arg release=$release_basename $SCRIPTDIR || { cleanup2; exit 10; }

echo "Cleaning up"
cleanup2

echo "Done"
