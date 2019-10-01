# -*- coding: utf-8 -*-

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

"""
Script to change the Pivt application directory local to default
and local.meta to default.meta, then compress the Pivt application
"""

import os
import glob
import tarfile
import shutil
import sys
import logging
import argparse

# Logging
LOGGER = logging.getLogger('release_version_update')
LOGGER.setLevel(logging.INFO)

CH = logging.StreamHandler()
CH.setLevel(logging.INFO)

FORMATTER = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

CH.setFormatter(FORMATTER)
LOGGER.addHandler(CH)


def main(args):
    """
    We pass in the command line argument and cast it as a variable called app_path that we
    pass to all the other functions being called in main.

    :param args: The path the user gave on the command line to the Pivt app directory
    :return: None
    """
    args = parse_args(args)
    app_path = args.root
    file_name = args.name

    find_directories(app_path)
    copy_rename_clean(app_path)
    zip_up(file_name, 'temp')
    shutil.rmtree('temp')


def parse_args(args):
    """
    We want the user to tell us where exactly the pivt app is located in their unique file system.
    So we get one agrument from them that is the path to the pivt app.

    :param args: The path the user gave on the command line to the Pivt app directory
    :return: Array with path to pivt app
            example: args = ['C:/Users/alfano/pivt/app']
    """
    parser = argparse.ArgumentParser(description='Update and Compress Pivt app for release')
    parser.add_argument('root', help='path to PIVT Splunk app directory')
    parser.add_argument('--name', default="pivt-splunk-app.tar.gz", help='name of the .tar.gz file')
    return parser.parse_args(args)


def find_directories(app_path):
    """
     Make sure that the application has the correct directories we want to rename and package.

    :param app_path: The path the user gave on the command line to the Pivt app directory
    :return: True
    """
    local = app_path + '/local'
    default = app_path + '/default'
    metadata = app_path + '/metadata'
    metadata_local = metadata + '/local.meta'
    metadata_default = metadata + '/default.meta'

    if not os.path.isdir(app_path):
        LOGGER.error('Not a valid path')
        sys.exit(1)

    my_dirs = os.listdir(app_path)

    if not my_dirs:
        LOGGER.error('Directory Empty')
        sys.exit(2)

    if os.path.isdir(local) and os.path.isdir(default):
        LOGGER.error('Both local and default exist. Merge them yourself first.')
        sys.exit(3)
    elif os.path.isdir(local):
        print('local found')
        if not os.path.exists(local + '/indexes.conf'):
            LOGGER.error('No indexes.conf')
            sys.exit(4)
    elif os.path.isdir(default):
        print('default found')
        if not os.path.exists(default + '/indexes.conf'):
            LOGGER.error('No indexes.conf')
            sys.exit(5)
    else:
        LOGGER.error('local and default not found')
        sys.exit(6)

    if os.path.isdir(metadata):
        print('metadata found')
        if os.path.exists(metadata_local) and os.path.exists(metadata_default):
            LOGGER.error('Both local.meta and default.meta exist. Merge them yourself first.')
            sys.exit(7)
        elif os.path.exists(metadata_local):
            print('local.meta found')
        elif os.path.exists(metadata_default):
            print('default.meta found')
        else:
            LOGGER.error('local.meta and default.meta not found')
            sys.exit(8)
    else:
        LOGGER.error('metadata not found')
        sys.exit(9)

    return True


def copy(source, dest):
    if os.path.isfile(source):
        shutil.copy(source, dest)
    elif os.path.isdir(source):
        basename = os.path.basename(source)
        shutil.copytree(source, os.path.join(dest, basename))
    else:
        raise Exception('Unkown file type. File: ' + source)



def copy_rename_clean(app_path):
    """
    Copy the directories local and metadata to a temp directory.
    Create folder called default that is a copy of local.
    Copy the file 'indexes.conf' from default to local and delete 'indexes.conf' from default.
    Remove the '.git' folder if found.

    :param app_path: The path the user gave on the command line to the Pivt app directory
    :return: True
    """
    temp_dir = 'temp/pivt'

    for item in glob.glob(app_path + '/*'):
        if 'appserver' in item:
            temp_appserver = temp_dir + '/appserver'
            os.makedirs(temp_appserver)

            for item2 in glob.glob(item + '/*'):
                if 'static' in item2:
                    temp_appserver_static = temp_appserver + '/static'
                    os.makedirs(temp_appserver_static)

                    for item3 in glob.glob(item2 + '/*'):
                        if 'visualizations' in item3:
                            temp_appserver_static_visualizations = temp_appserver_static + '/visualizations'
                            os.makedirs(temp_appserver_static_visualizations)

                            for viz in glob.glob(item3 + '/*'):
                                viz_basename = os.path.basename(viz)
                                temp_viz = temp_appserver_static_visualizations + '/' + viz_basename
                                os.makedirs(temp_viz)
                                copy(viz + '/formatter.html', temp_viz)
                                copy(viz + '/visualization.css', temp_viz)
                                copy(viz + '/visualization.js', temp_viz)

                            continue

                        copy(item3, temp_appserver_static)

                    continue

                copy(item2, temp_appserver)

            continue

        copy(item, temp_dir)

    temp_local = temp_dir + '/local'
    temp_default = temp_dir + '/default'
    temp_local_meta = temp_dir + '/metadata/local.meta'
    temp_default_meta = temp_dir + '/metadata/default.meta'

    # Check for temp/app_name/local
    if os.path.isdir(temp_local):
        os.rename(temp_local, temp_default)
        os.makedirs(temp_local)
        shutil.copy(temp_default + '/indexes.conf', temp_local)
        os.remove(temp_default + '/indexes.conf')
        print('Renamed local to default')
    elif os.path.isdir(temp_default):
        os.makedirs(temp_local)
        shutil.copy(temp_default + '/indexes.conf', temp_local)
        os.remove(temp_default + '/indexes.conf')

    # Check for temp/app_name/metadata/local.meta
    if os.path.exists(temp_local_meta):
        # local.meta should have all the index stanzas and default.meta should have everything else
        index_stanza_operations(temp_local_meta, temp_local_meta, temp_default_meta)
        print('Found local.meta, created default.meta, removed index stanzas from default.meta')
    elif os.path.exists(temp_default_meta):
        # local.meta should have all the index stanzas and default.meta should have everything else
        index_stanza_operations(temp_default_meta, temp_local_meta, temp_default_meta)
        print('Found default.meta, created local.meta, removed index stanzas from default.meta')

    if '.git' in os.listdir(temp_dir):
        print('Removed .git')
        shutil.rmtree(temp_dir + '/.git')

    return True


def index_stanza_operations(meta_file, temp_local_meta, temp_default_meta):
    """
    Open the meta file and read in [Indexes... to the local_lines array.
    If the read line is [ and is not [Indexes... then read all following lines into default_lines.
    The local_lines array will have stanzas with [Indexes... and default_lines will have every
    other type of stanza.

    :param meta_file: The file that contains all stanzas
    :param temp_local_meta: local.meta to be overwritten
    :param temp_default_meta: default.meta to be overwritten
    :return: None
    """
    with open(meta_file) as file:
        lines = file.readlines()
        default_lines = []
        local_lines = []
        in_index = False
        for line in lines:
            if not in_index:
                if line.startswith('[indexes'):
                    in_index = True
                    local_lines.append(line)
                else:
                    default_lines.append(line)
            else:
                if line.startswith('[') and not line.startswith('[indexes'):
                    in_index = False
                    default_lines.append(line)
                else:
                    local_lines.append(line)

    with open(temp_local_meta, 'w') as file:
        file.writelines(local_lines)
    with open(temp_default_meta, 'w') as file:
        file.writelines(default_lines)


def zip_up(archive_name, source_dir):
    """
    Zip the temp directory that has the renamed local to default files and directories.
    The zip file will be located where ever the Python script is ran.

    :param archive_name: The name we call the zipfile
    :param source_dir: The folder to zip
    :return: None
    """
    # lower() means case-insensitive
    if archive_name.lower().endswith('.tar.gz'):

        if os.path.exists(source_dir):
            print('Compressing files to %s...\n' % archive_name)
            tar = tarfile.open(archive_name, 'w:gz')
            for file_name in glob.glob(os.path.join(source_dir, '*')):
                tar.add(file_name, os.path.basename(file_name))
                tar.close()
            print('Done!')
            return True
        LOGGER.error('Source Directory to Zip was not found! Archiving process terminated.')
        sys.exit(11)

    LOGGER.error('Archive name is not a ".tar.gz" type of file! Archiving process terminated.')
    sys.exit(12)


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except Exception:
        LOGGER.exception('Fatal error')
        raise
