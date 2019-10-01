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

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
script_dir=${script_dir/\/cygdrive\/c\//C:\/}
script_dir=${script_dir/\/c\//C:\/}

root_dir="$(cd $script_dir/.. && pwd)"

echo "Script location:"
echo $script_dir

echo "Root location:"
echo $root_dir

mkdir $script_dir/pivt
cp -r $root_dir/pivt $root_dir/unittests $root_dir/.coveragerc $script_dir/pivt

cleanup1() {
    rm -r $script_dir/pivt
}

image=pivt-unittest-$(uuidgen) || { cleanup1; exit 2; }

echo "Building $image"
docker build -t $image -f $script_dir/Dockerfile.unittest $script_dir/ || { cleanup1; exit 3; }

container=pivt-unittest-$(uuidgen) || { cleanup1; exit 4; }

echo "Running $container"
docker run --name $container $image || { cleanup1; exit 5; }

mkdir -p $script_dir/ut_data/

echo "Extracting report files"
docker cp $container:/data/ut_report.xml $script_dir/ut_data/
docker cp $container:/data/coverage.xml $script_dir/ut_data/
docker cp $container:/data/pylint.out $script_dir/ut_data/

echo "Removing $container"
docker rm -v $container

echo "Removing $image"
docker image rm $image

cleanup1
