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

if [ -z $1 ]; then
    echo "No ARTIFACTORY_API_KEY argument. Exiting"
    exit 1
fi

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
script_dir=${script_dir/\/cygdrive\/c\//C:\/}
script_dir=${script_dir/\/c\//C:\/}

lookups_url=http://devops:8081/artifactory/generic-local/pivt/pivt-lookups

files=$(curl -su pivt-puller:$1 "http://devops:8081/artifactory/api/storage/generic-local/pivt/pivt-lookups/" | grep -oE '"uri" : ".*\.csv"' | sed -r 's/"uri" : "(.*\.csv)"/\1/')

mkdir -p $script_dir/splunk-app/lookups

for file in $files; do
    curl -su pivt-puller:$1 "$lookups_url/$file" --output $script_dir/splunk-app/lookups/$file
done