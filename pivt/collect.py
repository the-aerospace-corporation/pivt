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
Gathers data collected from Jenkins and ClearQuest and readies it for processing
"""

import shutil
import time
import sys
from pathlib import Path
from pivt.util import util


class Collector:
    """
    Collects data exported from export_jenkins and compresses it in Collected directory.
    """
    def __init__(self):
        util.setup()
        self.logger = util.get_logger(self)

    def main(self):
        """Collect data and package it in a zip file."""
        self.setup()

        if not util.new_data_dir.exists():
            self.logger.info('New data dir (%s) does not exist. Exiting.', util.new_data_dir)
            sys.exit()

        self.logger.info('Starting collection')

        pull_dirs = self.get_pull_dirs()

        self.logger.info('%s pulls since last collection', len(pull_dirs))

        self.logger.info('Zipping %s', util.new_data_dir)
        archive_path = self.zip_data()

        self.logger.info('Zip file name: %s', archive_path)

        self.logger.info('Archiving...')
        shutil.copy(str(archive_path), str(util.archive_dir))

        self.logger.info('Cleaning up...')
        self.cleanup()

        self.logger.info('Collection complete')

    @staticmethod
    def setup():
        """Create necessary directories."""
        util.archive_dir.mkdir(parents=True, exist_ok=True)
        util.collected_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_pull_dirs():
        """Retrieve pull directories."""
        new_data_paths = util.new_data_dir.glob('*')

        pull_dirs = []
        for path in new_data_paths:
            if path.is_dir():
                pull_dirs.append(path)

        return pull_dirs

    @staticmethod
    def zip_data():
        """Create zip file."""
        date = time.strftime('%Y-%m-%dT%H-%M-%S')[2:]
        archive_name = '{0}/{1}_NewData'.format(util.collected_dir, date)
        archive_path = shutil.make_archive(archive_name, 'zip', str(util.new_data_dir))
        return Path(archive_path)

    @staticmethod
    def cleanup():
        """Clean up."""
        new_data_paths = util.new_data_dir.glob('*')

        for path in new_data_paths:
            if path.is_dir():
                util.rmtree(path)
            else:
                path.unlink()  # remove file


if __name__ == '__main__':
    COLLECTOR = Collector()

    try:
        COLLECTOR.main()
    except Exception:
        COLLECTOR.logger.exception('Fatal error')
        raise
