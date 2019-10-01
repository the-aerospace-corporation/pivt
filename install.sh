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

exe() {
	cmd=$1
	exe_always=$2

	if $verbose; then
		echo "$cmd"
	fi

	if ! $dry_run || $exe_always; then
		eval "$cmd"
	fi
}

dry_run=false
verbose=false
prod=true
docker=false

# Get options
OPTS=`getopt -o dvaf --long dry,verbose,not-prod,docker -n 'parse-options' -- "$@"`
if [ $? != 0 ] ; then
	echo "Incorrect options provided"
	exit 1
fi

eval set -- "$OPTS"

while true; do
	case "$1" in
		-d | --dry ) dry_run=true; verbose=true; shift;;
		-v | --verbose ) verbose=true; shift;;
		-a | --not-prod ) prod=false; shift;;
		-f | --docker ) prod=false; docker=true; shift;;
		-- ) shift; break;;
		* ) break;;
	esac
done

if $dry_run; then
	echo 'Dry Run mode, none of the following actions will be executed, this is for preview purposes'
	echo 'Run this script again without the -d option to have the install commands executed'
fi

install_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

exe "source $install_dir/config.out" true

if [ -z $TARGET ]; then
	echo 'No TARGET found in config.out; exiting. Make sure to run ./configure.sh to generate config.out before running this script'
	exit 2
fi

if [ -z $PIVTHOME ]; then
	echo "No PIVTHOME found in config.out; exiting. Make sure to run ./configure.sh to generate config.out before running this script"
	exit 2
fi

if [ -z $BACKUPDIR ]; then
	echo 'No BACKUPDIR found in config.out; exiting. Make sure to run ./configure.sh to generate config.out before running this script'
	exit 2
fi

if [ -z $SPLUNKHOME ]; then
	echo 'No SPLUNKHOME found in config.out; exiting. Make sure to run ./configure.sh to generate config.out before running this script'
	exit 2
fi

echo "Installing PIVT backend"

PIVT_HOME="$TARGET/pivt"

echo "Install target: $TARGET"

exe "source $install_dir/dist/etc/pivt.version" true

version=$CURRENT

new_pivt_dir_w_version="$TARGET/pivt-$version"

if $verbose; then
	echo "Version: $version"
fi

##### Copy new PIVT delivery to target directory as pivt-$version #####

date_now="$(date +%FT%H-%M-%S%Z)"

if [ -d $new_pivt_dir_w_version ]; then
	if $prod; then
		echo "ERROR: directory with desired name already exists: $new_pivt_dir_w_version. Exiting"
		exit 3
	fi

	pivt_backup_dir="$new_pivt_dir_w_version-BACKUP-$date_now"

	exe "mv $new_pivt_dir_w_version $pivt_backup_dir" false

	old_pivt_dir=$pivt_backup_dir
fi

if $verbose; then
	echo "New PIVT dir: $new_pivt_dir_w_version"
fi

exe "cp -a $install_dir/dist $new_pivt_dir_w_version" false

##### Remove existing 'pivt' symlink #####

if [ -L $PIVT_HOME ]; then
	if [ -z $old_pivt_dir ]; then
		old_pivt_dir=$(readlink $PIVT_HOME)
	fi
	exe "rm $PIVT_HOME" false
elif [ -e $PIVT_HOME ]; then
	echo "ERROR: Trying to remove symlink but found something that isn't a symlink: $PIVT_HOME. Exiting"
	exit 4
fi

echo "Old PIVT dir: $old_pivt_dir"

##### Add new 'pivt' symlink to point to new installation #####

exe "ln -s $new_pivt_dir_w_version $PIVT_HOME" false

echo "PIVT_HOME: $PIVT_HOME"

##### Set permissions on all PIVT shell scripts

exe "chmod 755 $PIVT_HOME/bin/*.sh"

##### Handle data #####

if [ -d $PIVT_HOME/var/data ]; then
	# new delivery comes with data; must recreate indexes
	# exe "$PIVT_HOME/bin/recreate_indexes.sh"
	echo "Index recreation feature not implemented yet. You must recreate the indexes through Splunk manually and restart Splunk."
elif [ ! -z $old_pivt_dir ]; then
	exe "mv $old_pivt_dir/var $PIVT_HOME" false
fi

##### Copy non-dist files from install dir to new installation #####

read -r -d '' copy_old_to_new_cmd <<- EOF
	cd $install_dir
	tar -c --exclude dist --exclude config.in --exclude config.out --exclude configure*.sh --exclude install*.sh --exclude MANIFEST . | tar -x -C $PIVT_HOME
	mkdir $PIVT_HOME/install
	cp -a config.in config.out configure*.sh install*.sh $PIVT_HOME/install
EOF

exe "$copy_old_to_new_cmd" false

##### Copy important files from old install to new #####

if [ ! -z $old_pivt_dir ]; then
	exe "cp -ar $old_pivt_dir/etc/local $old_pivt_dir/etc/unpulled.json $old_pivt_dir/etc/job_pull_times.ini $PIVT_HOME/etc" false
fi

echo "Installing PIVT frontend"

echo "Splunk home: $SPLUNKHOME"

##### Backup old PIVT Splunk app #####

if $docker; then
	splunk_apps_dir="/var/opt/splunk/etc/apps"
else
	splunk_apps_dir="$SPLUNKHOME/etc/apps"
fi

splunk_pivt_app_dir="$splunk_apps_dir/pivt"

date_now="$(date +%FT%H-%M-%S%Z)"

if [ -d $splunk_pivt_app_dir ]; then
	app_backup_dir="$BACKUPDIR/.pivt-app_BACKUP_$date_now"

	exe "mv $splunk_pivt_app_dir $app_backup_dir" false
fi

##### Install PIVT Splunk app #####

pivt_app=$(find $install_dir/dist -name pivt-splunk-app*.tar.gz)

echo "PIVT app archive: $pivt_app"

echo "Installing PIVT Splunk app..."

# Set install command
install_cmd="tar -xzf $pivt_app -C $splunk_apps_dir"
if [ ! -z $app_backup_dir ]; then
	install_cmd="$install_cmd && cp $app_backup_dir/lookups/pivt_jenkins_ttr.csv $splunk_pivt_app_dir/lookups"
fi
install_cmd="$install_cmd && chmod -R g+w $splunk_pivt_app_dir"

if $verbose; then
	echo "$install_cmd"
fi

if ! $dry_run; then
	eval "$install_cmd"
	if [ ! $? -eq 0 ]; then
		echo 'App install failed. Exiting'
		exit 3
	fi

	# Verify installation of the pivt-app
	if [ ! -d "$splunk_pivt_app_dir" ]; then
		echo "PIVT app not found ($splunk_pivt_app_dir). Exiting"
		exit 4
	fi
	echo "PIVT app location: $splunk_pivt_app_dir"
fi

# Define sed expression to localize paths to data inputs
pivt_inputs=$splunk_pivt_app_dir/default/inputs.conf
pivt_backup=$splunk_pivt_app_dir/default/inputs.conf.bkup
sed_cmd="sed -i -r 's|^\[monitor:///app/pivt/(.+)\]|[monitor://$PIVTHOME/\1]|' $pivt_inputs"

# Replace stanzas in inputs.conf
echo "Updating data inputs"
if $verbose; then
	echo "cp $pivt_inputs $pivt_backup"
	echo $sed_cmd
	echo "rm $pivt_backup"
fi

if ! $dry_run; then
	# Make a backup of inputs.conf in case something goes wrong
	cp $pivt_inputs $pivt_backup

	# Count how many stanzas appear originally (used in error detection on line 219)
	stanza_count="$(grep -o -E "^\[monitor:///app/pivt/.+\]" $pivt_inputs | wc -l)"

	eval $sed_cmd

	# Check for errors. Revert input.conf if an error is found.
	error_status=$?
	new_stanza_count="$(grep -o -E "^\[monitor://$PIVTHOME/.+\]" $pivt_inputs | wc -l)"

	if [[ ! $error_status -eq 0 || $stanza_count -ne $new_stanza_count ]]; then
		# Reverting to backup
		echo "Data input update failed. Reverting $pivt_inputs and exiting."
		mv -f $pivt_backup $pivt_inputs
		exit 5
	fi

	rm $pivt_backup
fi

##### Restart Splunk #####

if $prod; then
	echo "Restarting Splunk"
	exe "$SPLUNKHOME/bin/splunk restart" false
fi

echo "Done!"
