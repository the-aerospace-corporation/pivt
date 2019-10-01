#/bin/bash

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

if [ $# -ne 2 ]; then
	echo "Illegal number of parameters"
	echo "Usage: $0 devops-server-username archive-path"
	exit 1
fi

username=$1
archive=$2

echo "file: $archive"
chmod 660 $archive
scp $archive $username@devops:/var/lib/jenkins/pivt-data
