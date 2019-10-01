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

usage() {
    echo "Usage: $0 VERSION APPDIR"
}

version=$1
app_dir=$2

if [ -z $version ]; then
    echo "No VERSION"
    usage
    exit 1
fi

if [ -z $app_dir ]; then
    echo "No APPDIR"
    usage
    exit 1
fi

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
script_dir=${script_dir/\/cygdrive\/c\//C:\/}
script_dir=${script_dir/\/c\//C:\/}

notfound=false

find_version() {
    file=$1
    line_num=$2

    lines=`grep -on "$version" $file`

    match="*$line_num:$version*"

    if [[ $lines != $match ]]; then
        echo "Version ($version) not found in $file at line $line_num"
        notfound=true
    fi
}

find_version $script_dir/CHANGELOG 4
find_version $script_dir/README 1
find_version $script_dir/LICENSE 15

cfg_path="$app_dir/default"
if [ ! -d $cfg_path ]; then
    cfg_path="$app_dir/local"
fi

dashboards_path="$cfg_path/data/ui/views"

for file in `ls $dashboards_path`
do
    grep "<description>PIVT Version: $version --- Last pull date: None</description>" $dashboards_path/$file > /dev/null 2>&1
    if [ $? != 0 ]; then
        echo "Dashboard $file does not have correct version"
        notfound=true
    fi
done

grep "version = $version" $cfg_path/app.conf > /dev/null 2>&1
if [ $? != 0 ]; then
    echo "app.conf does not have correct version"
    notfound=true
fi

if $notfound; then
    exit 1
fi
