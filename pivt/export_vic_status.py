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
Exports VIC status data
"""

import json
import time
from pivt.util import util


class VicStatusPlugin:
    """
    Export VIC status data from a RTN-hosted web page.
    """
    def __init__(self):
        util.setup()

        self.logger = util.get_logger(self)

        self.vic_status_url = util.conf_manager.get('pivt', 'export_vic_status', 'vic_status_url')

        self.timestamp = time.time()
        gmtime = time.gmtime(self.timestamp)
        date = time.strftime('%Y%m%d%H%M%S', gmtime)[2:]
        base_dir = util.new_data_dir / date

        self.data_dir = base_dir / 'vic_status'

    def main(self):
        """
        Export data.
        :return:
        """
        self.logger.info('Starting VIC status pull')
        self.logger.info('URL: %s', self.vic_status_url)

        self.logger.info('Fetching data')
        raw_data = VicStatusSensor.get_data(url=self.vic_status_url)

        self.logger.info('Parsing data')
        parsed_data = VicStatusParser.parse(raw_data, timestamp=self.timestamp)

        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info('Writing data to %s', self.data_dir.resolve())
        self.write(parsed_data)

        self.logger.info('Done')

    def write(self, parsed_data):
        """
        Write parsed data to file.
        :param parsed_data:
        :return:
        """
        file_path = self.data_dir / 'vic_status.json'
        with file_path.open('w') as file:
            file.write(json.dumps(parsed_data))

        self.logger.info('Data written to %s', file_path.resolve())


class VicStatusSensor:
    """
    Class encompassing methods to pull data.
    """
    @staticmethod
    def get_data(**kwargs):
        """
        Get data from URL.
        :param kwargs:
        :return: pulled data
        """
        url = kwargs['url']
        data = str(util.get(url), 'utf-8', 'replace')
        return data


class VicStatusParser:
    """
    Class encompassing methods to parse data.
    """
    @staticmethod
    def parse(raw_data, **kwargs):
        """
        Parse the raw data.
        :param raw_data:
        :param kwargs:
        :return: parsed data
        """
        data = json.loads(raw_data)

        timestamp = kwargs['timestamp']
        for item in data:
            item['timestamp'] = timestamp

        return data


if __name__ == '__main__':
    PLUGIN = VicStatusPlugin()

    try:
        PLUGIN.main()
    except Exception:
        PLUGIN.logger.exception('Fatal error')
        raise
