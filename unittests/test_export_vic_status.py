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

from pivt import export_vic_status as export
import unittest
from unittest.mock import patch
from unittest.mock import MagicMock
import os
import tempfile
import json
from pivt.util import util
from pivt.conf_manager import ConfManager

orig_conf_load = ConfManager.load
orig_conf_get = ConfManager.get


def setUpModule():
    os.environ['PIVT_HOME'] = tempfile.mkdtemp().replace('\\', '/')

    ConfManager.load = MagicMock()
    ConfManager.get = MagicMock(return_value='hi')

    util.setup()


def tearDownModule():
    util.teardown()
    util.rmtree(os.environ['PIVT_HOME'], no_exist_ok=True)
    if 'PIVT_HOME' in os.environ:
        del os.environ['PIVT_HOME']

    ConfManager.load = orig_conf_load
    ConfManager.get = orig_conf_get


if __name__ == '__main__':
    unittest.main()


"""
VicStatusPlugin
"""
class TestVicStatusPluginMain(unittest.TestCase):
    def setUp(self):
        self.plugin = export.VicStatusPlugin()

    def tearDown(self):
        util.rmtree(util.data_dir, no_exist_ok=True)

    @patch('pivt.export_vic_status.VicStatusPlugin.write')
    @patch('pivt.export_vic_status.VicStatusParser.parse')
    @patch('pivt.export_vic_status.VicStatusSensor.get_data')
    def test(self, mock_get_data, mock_parse, mock_write):
        mock_get_data.return_value = 'raw'
        mock_parse.return_value = 'parsed'

        self.plugin.main()

        mock_get_data.assert_called_once_with(url=self.plugin.vic_status_url)
        mock_parse.assert_called_once_with('raw', timestamp=self.plugin.timestamp)
        self.assertTrue(self.plugin.data_dir.exists())
        mock_write.assert_called_once_with('parsed')

class TestVicStatusPluginWrite(unittest.TestCase):
    def setUp(self):
        self.plugin = export.VicStatusPlugin()
        self.plugin.data_dir.mkdir(parents=True)

    def tearDown(self):
        util.rmtree(util.data_dir)

    def test(self):
        parsed_data = {
            'derp': 'herp'
        }

        self.plugin.write(parsed_data)

        self.assertEqual(['vic_status.json'], util.listdir(self.plugin.data_dir))

        with (self.plugin.data_dir / 'vic_status.json').open() as file:
            contents = file.read()

        self.assertEqual(parsed_data, json.loads(contents))


"""
VicStatusSensor
"""
class TestVicStatusSensorGetData(unittest.TestCase):
    @patch('pivt.util.util.get')
    def test(self, mock_get):
        mock_get.return_value = b'hi'
        url = 'url'
        raw_data = export.VicStatusSensor.get_data(url=url)
        self.assertEqual('hi', raw_data)
        mock_get.assert_called_once_with(url)


"""
VicStatusParser
"""
class TestVicStatusParserParse(unittest.TestCase):
    def test(self):
        data = [
            {'derp': 'herp'},
            {'lerp': 'gerp'}
        ]

        expected_data = [
            {'derp': 'herp', 'timestamp': 'derp'},
            {'lerp': 'gerp', 'timestamp': 'derp'}
        ]

        raw_data = json.dumps(data)

        parsed_data = export.VicStatusParser.parse(raw_data, timestamp='derp')

        self.assertEqual(expected_data, parsed_data)

