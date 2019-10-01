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
Script to update any files with previous versions to the new versions

"""
import os
import re
import sys
import argparse
import logging
from shutil import copyfile
import pathspec
from pathlib import Path

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
    This is called from the if __name__ == '__main__" function at the bottom of the file.
    This function controls most of the calls to other methods.

    :param args: An array of arguments you passed in from the command line.
                Example: args = ['path/to/pivt', '0.1.2.4']
    :return: None
    """
    args = parse_args(args)
    # check if path to pivt exists
    if not os.path.exists(args.root):
        LOGGER.error('Path to PIVT does not exist.')
        sys.exit(1)

    root_path = Path(args.root)
    cfg_path = root_path / 'cfg'
    version_path = cfg_path / 'pivt.version'
    version_backup_path = cfg_path / 'pivt.version.backup'

    if not version_path.exists():
        LOGGER.error('path to version file does not exist')
        sys.exit(3)

    # if --revert is false (not used)
    if not args.revert:
        # check for version format
        if not re.match(r'[0-9]\.[0-9]\.[0-9]\.[0-9](\.[0-9])?', args.version):
            LOGGER.error('version was not typed correctly')
            sys.exit(4)
    # if --revert is true
    else:
        if not version_backup_path.exists():
            LOGGER.error('path to backup version file does not exist')
            sys.exit(6)

    ignore_path = root_path / 'ignore.txt'

    # check if ignore.txt file exists
    if not ignore_path.exists():
        LOGGER.error('No ignore file was found')
        sys.exit(9)

    # get CURRENT and PREVIOUS versions from the VERSION file
    current, previous = curr_pre_match(version_path)

    # perform all actions
    perform_actions(root_path,
                    current,
                    previous,
                    args.version,
                    version_path,
                    version_backup_path,
                    ignore_path,
                    args.revert)


def parse_args(args):
    """
    We want the user to tell us where exactly pivt is in their unique file system,
    and what version they want all files to be changed too that have version in them.

    If the user decides they want to revert back to the original version after changing
    the files, use '--revert' and 'path/to/pivt' when you run again.

    :param args: Commandline arguments (must be two, cannot have both '--revert' and '--version')
    :return: Array with path to pivt and current version OR --revert
            example: args = ['path/to/pivt', '0.1.2.4'] or
                    args = [True, 'path/to/pivt']

                    Cannot have both '--revert' and '--version' when running.
    """
    parser = argparse.ArgumentParser(description='Update PIVT files with new version')
    # required argument
    parser.add_argument('root',
                        help='path to pivt')

    # mutually exclusive arguments
    # must have one option (either version string or --revert)
    option_data_source_parser = parser.add_mutually_exclusive_group(required=True)

    option_data_source_parser.add_argument('-r',
                                           '--revert',
                                           help='revert the version back to original',
                                           action='store_true')
    option_data_source_parser.add_argument('-v',
                                           '--version',
                                           help='what you want to be the current version',
                                           type=str)
    parser.set_defaults(revert=False)

    return parser.parse_args(args)


def curr_pre_match(version_path):
    """
    Will return a tuple that has current version and previous version
        example: CURRENT=0.1.2.3 PREVIOUS=0.1.2.2
               returns '0.1.2.3', '0.1.2.2'

    :param version_path: Path to the VERSION file
    :return: array with current and previous from the VERSION file
    """
    with version_path.open() as version_file:
        file_data = version_file.readlines()
        current = None
        previous = None
        for line in file_data:
            current_match = re.match('CURRENT=(.*)\n', line)
            if current_match:
                current = current_match.group(1)

            previous_match = re.match('PREVIOUS=(.*)', line)
            if previous_match:
                previous = previous_match.group(1)

        if not current:
            LOGGER.error("CURRENT not found in version")
            sys.exit(10)
        if not previous:
            LOGGER.error("PREVIOUS not found in version")
            sys.exit(11)

    return current, previous


def perform_actions(pivt_path, current, previous, version,
                    version_path, version_backup_path,
                    ignore_path, revert):
    """
    Main calls this function to perform all the actions necessary to update all files with version
    in them to updated versions, or revert them to previous version.

    :param pivt_path: the path to pivt from the command line 'path/to/pivt'
    :param current: CURRENT from version file
    :param previous: PREVIOUS from version file
    :param version: the version passed in from the command line. Equals None if --revert is used.
    :param version_path: path to version file
    :param version_backup_path: path to backup version file
    :param revert: True or False
    :return: None
    """
    message = True

    ignore_files = ignore_list(pivt_path, ignore_path)

    full_list = walk_root(pivt_path, ignore_files, current)

    if revert:
        proceed = update(full_list, current, previous, message)
    else:
        proceed = update(full_list, current, version, message)

    if not proceed:
        LOGGER.info('No files were changed.')
        sys.exit(0)

    # revert VERSION to what VERSION.BACKUP is, keep last pull date
    if revert:
        # overwrite VERSION
        if not version_path.exists():
            version_backup_path.rename(version_path)
        else:
            # get current from VERSION.BACKUP
            _, previous_backup = curr_pre_match(version_backup_path)

            # overwrite VERSION
            over_write_version(version_path, current, previous, previous_backup, revert)

            # remove outdated VERSION.BACKUP
            version_backup_path.unlink()

        # files with current from VERSION will be replaced with previous from VERSION
        update(full_list, current, previous, False)
    else:
        # create backup of VERSION to preserve original current and previous
        copyfile(version_path, version_backup_path)

        # over write the VERSION file curr_pre_array holds CURRENT and PREVIOUS values and
        # new_curr is args.version
        over_write_version(version_path, current, previous, version, revert)

        # file with current from VERSION will be replaced with args.version
        update(full_list, current, version, False)


def ignore_list(pivt_path, ignore_path):
    """
    We want to create a list based off of our ignore.txt file.
    If there is a file or directory anywhere under pivt that matches
    what we have in the ignore.txt file then we put it in a list.
    This saves us time from opening files or directories that we know
    we don't watch to check for versions in them when it comes time to
    update the files.
        example: ignore pdf files and .idea directory
                ignore.txt -> *.pdf .idea
                ignores = ['C:/Users/pivt/backend/a.pdf',
                            'C:/Users/pivt/b.pdf', 'C:/Users/backend/.idea']

    :param path: The path to the pivt directory you passed in from the command line.
    :return: A list of files and directories to ignore and they have the full path to them.
    """
    with ignore_path.open() as file:
        spec = pathspec.PathSpec.from_lines('gitwildmatch', file)

    ignores = set()

    for ignore_file in spec.match_tree(pivt_path):
        ignore_file = pivt_path / ignore_file
        ignores.add(str(ignore_file))

    return ignores


def walk_root(path, ignores, current):
    """
    Creates a list and each element is a full path to a file that
    we do not want to ignore and has a version in it.

    :param path: The path to the pivt directory you passed in from the command line
    :param ignores: A list of files and directories to ignore
    :param current: The current version we want to change
    :return: A list of elements that have the full path to files that we don't want
            to ignore and have previous versions in them we need to change to current
    """
    all_files = []
    for file_path in path.glob('**/*'):
        if not file_path.is_file():
            continue
        if not ignore(file_path, ignores) and pre_match(file_path, current):
            all_files.append(file_path)
    return all_files


def ignore(path, ignores):
    """
    If the full path of a file in pivt is equal to the full path
    of an element in the ignore list then we return True because
    we do not want that full path in the list created by walk_root.

    :param path: Full path to a file in the pivt directory
    :param ignores: A list of files to ignore (each element has the full path)
    :return: True or False
    """
    return str(path) in ignores


def pre_match(path, old_version):
    """
    If the file has version in it then return True.

    :param path: Full path to a file in the pivt directory
    :param old_version: The version we want to change
    :return: True or False
    """
    with path.open(encoding='utf-8') as file:
        if old_version in file.read():
            print('found ' + old_version + ' in ' + str(path))
            return True
    return False


def over_write_version(version_path, current, previous, version, revert):
    """
    If revert is NOT used (False) then replace PREVIOUS with CURRENT in VERSION:
        example: 'CURRENT=0.1.2.4 PREVIOUS=0.1.2.3' -> 'CURRENT=0.1.2.4 PREVIOUS=0.1.2.4'
    Then replace CURRENT with version that was passed in from the command line:
        example: 'CURRENT=0.1.2.4 PREVIOUS=0.1.2.4' -> 'CURRENT=0.1.2.5 PREVIOUS=0.1.2.4'

    If revert IS used (True) then replace CURRENT with PREVIOUS in VERSION:
        example: 'CURRENT=0.1.2.4 PREVIOUS=0.1.2.3' -> 'CURRENT=0.1.2.3 PREVIOUS=0.1.2.3'
    Then replace PREVIOUS with version that is equal to PREVIOUS from VERSION.BACKUP
    that we found before calling this function in curr_pre_match:
        example: 'CURRENT=0.1.2.3 PREVIOUS=0.1.2.3' -> 'CURRENT=0.1.2.3 PREVIOUS=0.1.2.2'

    :param version_path: path to VERSION file
    :param current: CURRENT from VERSION
    :param previous: PREVIOUS from VERSION
    :param version: the version passed in from the command line.
                    Equals PREVIOUS from VERSION.BACKUP if --revert is used.
    :param revert: True or False
    :return: None
    """
    with version_path.open(encoding='utf-8', newline='\n') as read_file:
        data = read_file.read()

    if revert:
        # data = data.replace(current, previous)
        data = re.sub(r'CURRENT=.+', 'CURRENT=' + previous, data)
        # data = data.replace('PREVIOUS=' + previous, 'PREVIOUS=' + version)
        data = re.sub(r'PREVIOUS=.+', 'PREVIOUS=' + version, data)
    else:
        # data = data.replace(previous, current)
        data = re.sub(r'PREVIOUS=.+', 'PREVIOUS=' + current, data)
        # data = data.replace('CURRENT=' + current, 'CURRENT=' + version)
        data = re.sub(r'CURRENT=.+', 'CURRENT=' + version, data)

    with version_path.open('w', encoding='utf-8', newline='\n') as write_file:
        write_file.write(data)


def update(all_files, old_current, new_current, warning_message):
    """
    We open each file in 'all_files' and replace previous version
    with current version if the user types 'yes' after prompted by input.
    If user types anything but 'yes' then the process is Terminated.

    :param all_files: A list of elements that have the full path to files
                      that we don't want to ignore and have current versions
                      in them we need to change to updated current.
    :param old_current: The version we want to change
    :param new_current: The version we want to change to
    :param warning_message: Always True at first, but will change to False if user types 'yes'
    :return: None
    """
    if warning_message:
        answer = input('Proceed in changing the files above? yes/no: ')
        return answer == 'yes'

    for file in all_files:
        print(file)
        if os.path.exists(file):
            with open(file, encoding='utf-8', newline='\n') as read_file:
                data = read_file.read()
            data = data.replace(old_current, new_current)
            with open(file, 'w', encoding='utf-8', newline='\n') as write_file:
                write_file.write(data)
    return None


if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except Exception:
        LOGGER.exception('Fatal error')
        raise
