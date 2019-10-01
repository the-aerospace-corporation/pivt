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

get_python_version() {
    py_exe=$1
    echo "$($py_exe -V 2>&1 | grep -Po '(?<=Python )(.+)')"
}

check_python_version() {
    version=$1
    if echo $version | sed 's/.* //;q' | awk -F. '{ if ($1 >= 3 && ( $2 >= 5 || ($2 == 4 && $3 >= 2) )) { exit 0 } else {exit 1} }' ; then
        true
    else
        false
    fi
}

help() {
	echo
	echo "Usage: $0 [OPTION]... TARGET PIVTHOME BACKUPDIR"
	echo "Prepare for PIVT Splunk app install. Old PIVT Splunk app (if it exists) will be backed up to BACKUPDIR."
	echo
    echo "  -p, --py        path to Python executable"
	echo "  -h, --help		display this help and exit"
}

PYEXE=""

PARAMS=""

while (( "$#" )); do
	case "$1" in
		-p | --py ) PYEXE="$2"; shift 2;;
		-h | --help ) help; exit 0;;
		-- ) shift; break;;
		-* | --*= ) echo "Error: Unsupported flag $1" >&2; help; exit 1;;
		* ) PARAMS="$PARAMS $1"; shift;;
	esac
done

eval set -- "$PARAMS"

if [ -z $1 ]; then
    echo "No TARGET argument"
    help
    exit 1
fi

if [ -z $2 ]; then
    echo "No PIVTHOME argument"
    help
    exit 1
fi

if [ -z $3 ] ; then
	echo "No BACKUPDIR argument"
	help
	exit 1
fi

target=$1
pivt_home=$2
backup_dir=$3

if [ ! -d $target ]; then
    echo "Path does not exist: $target. Exiting"
    exit 2
fi

if [ ! -d $backup_dir ]; then
    echo "Path does not exist: $backup_dir. Exiting"
    exit 2
fi

install_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Import config.in
source $install_dir/config.in

# BACKEND

if [ -z "$PYEXE" ]; then
    # Look for Python executable
    export py_exe="python3.5"
    export version=$(get_python_version $py_exe)

    if [ -z "$version" ]; then
        export py_exe="python3"
        export version=$(get_python_version $py_exe)
    fi

    if [ -z "$version" ]; then
        export py_exe="python"
        export version=$(get_python_version $py_exe)
    fi

    # Check for correct Python version (3.5.2 or greater)
    if check_python_version $version; then
        echo "Python executable: $py_exe"
        echo "Python version: $version"
    else
        echo "Invalid python version, must be at least 3.5.2"

        read -p "Enter path to valid Python executable: " py_exe
        version=$(get_python_version $py_exe)

        if check_python_version $version; then
            echo "Python executable: $py_exe"
            echo "Python version: $version"
        else
            echo "Invalid python version, must be at least 3.5.2"
            exit 3
        fi
    fi
else
    export py_exe=$PYEXE
    version=$(get_python_version $py_exe)

    if check_python_version $version; then
        echo "Python executable: $py_exe"
        echo "Python version: $version"
    else
        echo "Invalid python version, must be at least 3.5.2"
        exit 4
    fi
fi

# Check if Python requests module exists
if $py_exe -c "import requests" &> /dev/null; then
    echo 'requests python module found'
else
    echo 'requests python module not found, use `pip install requests` to install this module'
    exit 5
fi

echo "TARGET=$target" >> $install_dir/config.out

# FRONTEND

# Look for SPLUNKHOME path in environment
if [ ! -d $SPLUNKHOME ]; then
    echo "Default Splunk install location not found: $SPLUNKHOME"
    # Prompt user for SPLUNKHOME path if default does not exist
	read -p "Enter valid install location: " SPLUNKHOME
    if [ ! -d "$SPLUNKHOME" ]; then
        echo "Splunk installation not found, exiting"
	    exit 3
    fi
fi

# Check if Splunk executable exists in SPLUNKHOME path
if [ ! -f "$SPLUNKHOME/bin/splunk" ]; then
	echo "$SPLUNKHOME doesn't look like a valid Splunk installation. Exiting."
	exit 4
fi

echo "Splunk home: $SPLUNKHOME"

# Check if Splunk version is valid (7.0 or greater)

splunk_version=$(ls /opt/splunk | sed -n 's/splunk-//gp' | sed -n -r 's/-.+-manifest//gp')

echo "Splunk Version:" $splunk_version
if echo $splunk_version | sed 's/.* //;q' | awk -F. '{ if ($1 >= 7) { exit 0 } else {exit 1} }' ; then
    echo "Version is 7.0 or later"
else
    echo "Version is too old."
    exit 5
fi

echo "PIVTHOME=$pivt_home" >> $install_dir/config.out
echo "BACKUPDIR=$backup_dir" >> $install_dir/config.out
echo "SPLUNKHOME=$SPLUNKHOME" >> $install_dir/config.out
