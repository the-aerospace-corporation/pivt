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
Packages the files listed in manifest.in into a .tar.gz,
where manifest.txt is in the same directory as this file. These files are
searched for starting at the root directory provided as a command line
argument to this script. The first column in manifest.in is the source;
the second column is the destination within the resulting archive.
The source can be a blob pattern.

path/to/file1       target1
path/to/file2       target1
path/to/dir/*.txt   target2
path/to/file4       target3

The second column (target) can be a dot ('.'). This represents the top
directory in the output archive.
"""

import sys
import argparse
import os
from glob import glob
import tarfile


def main(args):
    """
    Create the release tar.gz
    :param args: command line arguments
    :return:
    """
    args = parse_args(args)

    # read in manifest file and check for any issues
    manifest = load_manifest(args.manifest)

    if not manifest:
        print('Empty manifest. Exiting')
        return

    out_file_name = args.out
    if not out_file_name.endswith('.tar.gz'):
        out_file_name += '.tar.gz'

    # create temp directory, copy each file in manifest to temp
    # directory and dos2unix it, and create output manifest file
    with tarfile.open(out_file_name, 'w:gz') as tar_file:
        manifest_out = []

        for src, dest in manifest.items():
            if dest == '.':
                dest_dir = args.top_dir
            else:
                if dest.startswith('./'):
                    dest_dir = os.path.join(args.top_dir, dest[2:])
                else:
                    dest_dir = os.path.join(args.top_dir, dest)
                    # for the manifest file
                    dest = './' + dest

            src_files = glob(os.path.join(args.root, src))

            if not src_files:
                print('Warning: found nothing for ' + src)

            for src_file in src_files:
                dos_2_unix(src_file)

                src_basename = os.path.basename(src_file)

                dest_file = os.path.join(dest_dir, src_basename)
                tar_file.add(src_file, arcname=dest_file, filter=set_perms)

                manifest_out.append(os.path.join(dest, src_basename).replace('\\', '/'))

        with open('MANIFEST', 'w') as file:
            file.writelines('\n'.join(manifest_out))

        tar_file.add('MANIFEST', arcname=os.path.join(args.top_dir, 'MANIFEST'), filter=set_perms)

        os.remove('MANIFEST')

    print('Release created at ' + out_file_name)


def set_perms(tarinfo):
    """
    Set permissions for a file going into a tar
    :param tarinfo: the tarinfo for the file
    :return: the modified tarinfo object
    """
    if tarinfo.isfile():
        if tarinfo.name.endswith('.sh'):
            mode = '774'
        else:
            mode = '664'
    else:
        mode = '775'

    tarinfo.mode = int(mode, 8)  # octal to decimal

    return tarinfo


def parse_args(args):
    """
    Parse command line arguments using argparse.
    :param args: command line arguments
    :return: parsed arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('root', help='path to root directory')
    parser.add_argument('top_dir', help='name of top directory in output archive')
    parser.add_argument('--out', default='release', help='name of output file')
    parser.add_argument('--manifest', default='manifest.in', help='path to manifest.in')

    return parser.parse_args(args)


def load_manifest(manifest_path):
    """
    Load the manifest file into a dictionary
    :param manifest_path: path to the manifest file
    :return: dictionary representing the manifest
    """
    manifest = {}

    with open(manifest_path, 'r') as file:
        for line in file:
            line = line.strip()

            if line == '':
                continue

            columns = line.split()

            if len(columns) != 2:
                print('File does not follow convention! Line: ' + line)
                return {}

            src = columns[0]
            dest = columns[1]

            manifest[src] = dest

    return manifest


def dos_2_unix(path):
    """
    Replace DOS-like line endings with Unix-like line-endings in a file
    :param path: path to the file
    :return:
    """
    if not path.endswith('.sh'):
        return

    with open(path, 'rb') as file:
        contents = file.read()

    contents = contents.replace(b'\r\n', b'\n')

    with open(path, 'wb') as file:
        file.write(contents)


if __name__ == '__main__':
    main(sys.argv[1:])
