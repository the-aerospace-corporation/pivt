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

function help() {
	echo
	echo "Usage: $0 [OPTION]... [RELEASE_SUFFIX]"
	echo "Build a PIVT release. RELEASE_SUFFIX will be appended to the resulting release .tar.gz."
	echo
	echo "	-m, --no-md5	don't produce an md5 sum"
	echo "	-h, --help		display this help and exit"
}

md5=true

PARAMS=""

while (( "$#" )); do
	case "$1" in
		-m | --no-md5 ) md5=false; shift;;
		-h | --help ) help; exit 0;;
		-- ) shift; break;;
		-* | --*= ) echo "Error: Unsupported flag $1" >&2; help; exit 1;;
		* ) PARAMS="$PARAMS $1"; shift;;
	esac
done

eval set -- "$PARAMS"

suffix=$1

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
script_dir=${script_dir/\/cygdrive\/c\//C:\/}
script_dir=${script_dir/\/c\//C:\/}

echo "Script location: $script_dir"

splunk_app_dir=$script_dir/splunk-app

# get version from cfg/pivt.version
source $script_dir/cfg/pivt.version || exit 1

if [ -z $CURRENT ]; then
	echo "No CURRENT version found from version file ($script_dir/cfg/pivt.version)"
	cleanup3
	exit 2
fi

version=$CURRENT
echo "Version: $version"

echo "Checking for correct version in necessary files"
$script_dir/check-version.sh $version $splunk_app_dir || exit 3

whole_version="$version"
if [ ! -z $suffix ]; then
	whole_version="$whole_version-$suffix"
fi

echo "Building visualizations"
viz_dir=$splunk_app_dir/appserver/static/visualizations
visualizations=$(ls $viz_dir)
for viz_name in $visualizations
do
	$viz_dir/$viz_name/setup.sh
	$viz_dir/$viz_name/build.sh
done

splunk_app_name=pivt-splunk-app-$version.tar.gz
splunk_app=$script_dir/$splunk_app_name

cleanup1() {
	rm $splunk_app || true
}

echo "Packaging PIVT Splunk app"
python $script_dir/package_pivt_app.py --name $splunk_app $splunk_app_dir
if [ $? -ne 0 ]; then
	echo "\nPython script failed. Exiting"
	cleanup1
	exit 4
fi

# create release using package.py
echo "Building release"
release_name="aero-pivt-$whole_version.tar.gz"
release="$script_dir/$release_name"

manifest=$script_dir/manifest-$version.in
cp $script_dir/manifest.in $manifest

cleanup2() {
	rm $manifest
	cleanup1
}

sed -i -r "s/pivt-splunk-app.tar.gz/$splunk_app_name/" $manifest || { cleanup2; exit 5; }

python $script_dir/package.py $script_dir pivt-$version --out $release --manifest $manifest || { cleanup2; exit 6; }

if $md5; then
	echo "Creating md5"
	cd $script_dir
	md5sum $release_name > $release_name.md5
	echo "MD5 created: $script_dir/$release_name.md5"
else
	echo "Skipping md5 creation"
fi

echo "Cleaning up"
cleanup2

echo "Done."
