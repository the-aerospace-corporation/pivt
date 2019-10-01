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

from pivt import process
import unittest
import os
from unittest.mock import patch
from unittest.mock import call
from unittest.mock import MagicMock
import json
import csv
import zipfile
import copy
import tempfile
from copy import deepcopy
from pathlib import Path
from pivt.util import util
from pivt.util import Constants
from pivt.conf_manager import ConfManager

orig_conf_load = ConfManager.load

orig_ci_to_ss = None
orig_ci_subs = None


def setUpModule():
    os.environ['PIVT_HOME'] = tempfile.mkdtemp().replace('\\', '/')

    ConfManager.load = MagicMock()

    util.setup()

    global orig_ci_to_ss
    orig_ci_to_ss = deepcopy(util.ci_to_ss)

    util.ci_to_ss = {
        'ci2': 'ss5',
        'ci3': 'ss6'
    }

    global orig_ci_subs
    orig_ci_subs = deepcopy(process.CI_SUBS)

    process.CI_SUBS = {
        'ci3-sub': 'ci3'
    }


def tearDownModule():
    util.teardown()
    util.rmtree(os.environ['PIVT_HOME'], no_exist_ok=True)
    if 'PIVT_HOME' in os.environ:
        del(os.environ['PIVT_HOME'])

    ConfManager.load = orig_conf_load

    util.ci_to_ss = orig_ci_to_ss
    process.CI_SUBS = orig_ci_subs


def find_file(filename):
    """Finds the file_name, or returns blank if not found.
    Allows the unit tests to be run from an arbitrary
    directory, rather than assuming it is run from the utility directory directly
    """
    filename = os.path.normpath(filename)
    for root, dirs, files in os.walk('.'):
        for name in files:
            path = os.path.join(root, name).replace('.\\', '')
            if filename in path:
                return path
    return ''


if __name__ == '__main__':
    unittest.main()


"""
Processor
"""
class TestMain(unittest.TestCase):
    # TODO
    pass

class TestParseArgs(unittest.TestCase):
    def setUp(self):
        self.processor = process.Processor([])

    def test_no_args(self):
        args = self.processor.parse_args([])
        self.assertFalse(args.reverse)

    def test_reverse(self):
        args = self.processor.parse_args(['--reverse'])
        self.assertTrue(args.reverse)


class TestProcessorDeleteIndex(unittest.TestCase):
    @patch('time.sleep')
    @patch('requests.get')
    @patch('requests.delete')
    def test(self, mock_requests_delete, mock_requests_get, mock_sleep):
        mock_requests_get.status_code = 200
        process.Processor.delete_index('derp_index', 'derp_app')


class TestProcessorCreateIndex(unittest.TestCase):
    pass


class TestProcessorRefreshApp(unittest.TestCase):
    # def test(self):
    #     self.processor.refresh_app('pivt', 'https://localhost:8089')
    pass


class TestProcessorGetIndexPath(unittest.TestCase):
    def test(self):
        assert process.Processor._get_index_path('pivt_cq', 'pivt') == '/servicesNS/nobody/pivt/data/indexes/pivt_cq'


class TestProcessorGetIndexesPath(unittest.TestCase):
    def test(self):
        assert process.Processor._get_indexes_path('pivt') == '/servicesNS/nobody/pivt/data/indexes'


class TestProcessorGetAppPath(unittest.TestCase):
    def test(self):
        assert process.Processor._get_app_path('pivt') == '/servicesNS/nobody/pivt'


"""
Source
"""
class TestSourceSetup(unittest.TestCase):
    def setUp(self):
        self.name = 'name'
        self.data_dir = util.data_dir / 'test_dir'

        self.source = process.Source(self.name, self.data_dir)

    def tearDown(self):
        util.rmtree(util.data_dir, no_exist_ok=True)

    def test_dir_no_exist(self):
        self.source.setup()
        self.assertTrue(self.data_dir.exists())

    def test_dir_exists(self):
        self.data_dir.mkdir(parents=True)
        self.source.setup()
        self.assertTrue(self.data_dir.exists())


"""
JenkinsSource
"""
class TestJenkinsSourceSetup(unittest.TestCase):
    def setUp(self):
        self.name = 'name'
        self.data_dir = util.data_dir / 'test_dir'

        self.source = process.JenkinsSource(self.name, self.data_dir)

        self.files = []
        self.dirs = []

        self.expected_files = []

    def tearDown(self):
        util.rmtree(util.data_dir, no_exist_ok=True)

    def do_it(self):
        self.data_dir.mkdir(parents=True)

        for filename in self.files:
            file_path = self.data_dir / filename
            file_path.open('w').close()

        for dir_name in self.dirs:
            dir_path = self.data_dir / dir_name
            dir_path.mkdir()

        with patch.object(process.JenkinsSource, '_load_event_keys') as mock_load_keys:
            self.source.setup()
            self.make_asserts(mock_load_keys)

    def make_asserts(self, mock_load_keys):
        self.assertTrue(self.data_dir.exists())
        files_called_with = mock_load_keys.call_args[0][0]
        self.assertEqual(set(self.expected_files), set(files_called_with))

    def test_no_files(self):
        self.do_it()

    def test_some_files(self):
        self.files = ['f1.txt', 'f2.txt']
        self.dirs = ['some_dir']

        self.expected_files = [self.data_dir / filename for filename in self.files]

        self.do_it()

class TestJenkinsSourceLoadEventKeys(unittest.TestCase):
    def setUp(self):
        self.name = 'name'
        self.data_dir = util.data_dir / 'test_dir'

        self.source = process.JenkinsSource(self.name, self.data_dir)

        self.files = []
        self.key_return_vals = []
        self.expected_event_keys = {}

    def do_it(self):
        with patch.object(process.JenkinsSource, '_load_db_file_event_keys') as mock_load_file_keys:
            self.set_mocks(mock_load_file_keys)
            self.source._load_event_keys(self.files)
            self.make_asserts()

    def set_mocks(self, mock_load_file_keys):
        mock_load_file_keys.side_effect = self.key_return_vals

    def make_asserts(self):
        self.assertEqual(self.expected_event_keys, self.source.event_keys)

    def test_no_files(self):
        self.do_it()

    def test(self):
        self.files = [Path('path/f1.json'), Path('path/f2.json')]
        self.key_return_vals = ['keys1', 'keys2']

        self.expected_event_keys = {}
        for i in range(len(self.files)):
            file_path = util.basename(self.files[i])
            keys = self.key_return_vals[i]
            self.expected_event_keys[file_path] = {'new': set(), 'existing': keys}

        self.do_it()

class TestJenkinsSourceLoadDbFileEventKeys(unittest.TestCase):
    def setUp(self):
        self.name = 'name'
        self.data_dir = util.data_dir / 'test_dir'

        self.source = process.JenkinsSource(self.name, self.data_dir)

        self.events = None
        self.expected_keys = set()

    def tearDown(self):
        util.rmtree(util.data_dir, no_exist_ok=True)

    def do_it(self):
        file_path = self.data_dir/'test.json'

        if self.events is not None:
            self.data_dir.mkdir(parents=True)
            with file_path.open('w') as file:
                for event in self.events:
                    file.write(json.dumps(event) + '\n')

        with patch.object(process.JenkinsSource, '_get_event_key', side_effect=lambda e: json.loads(e)['id']):
            keys = self.source._load_db_file_event_keys(file_path)
            self.make_asserts(keys)

    def make_asserts(self, keys):
        self.assertEqual(self.expected_keys, keys)

    def test_no_file(self):
        self.do_it()

    def test(self):
        self.events = [
            {'herp': 'derp', 'id': 1, 'ci': 'ci1'},
            {'herp': 'derp', 'id': 2, 'ci': 'ci1'},
            {'herp': 'derp', 'id': 3, 'ci': 'ci1'}
        ]

        self.expected_keys = {event['id'] for event in self.events}

        self.do_it()

class TestJenkinsSourceLoadNewData(unittest.TestCase):
    def setUp(self):
        self.name = 'name'
        self.data_dir = util.data_dir / 'test_dir'
        self.pull_source_path = 'cool_path'

        self.source = process.JenkinsSource(self.name, self.data_dir)

        self.file_names = []
        self.expected_file_process_calls = None
        self.expected_added = 0
        self.expected_skipped = 0
        self.expected_logger_statement = 'INFO:JenkinsSource:Added: 0, skipped: 0'

    def do_it(self):
        files = (process.DataFile(filename) for filename in self.file_names)
        with patch.object(process.JenkinsSource, '_load_new_files') as mock_load_files, patch.object(process.DataFile, 'process') as mock_file_process, self.assertLogs('JenkinsSource', 'INFO') as logger:
            self.set_mocks(files, 2, 1, mock_load_files, mock_file_process)
            self.source.load_new_data(self.pull_source_path)
            self.make_asserts(mock_load_files, mock_file_process, logger)

    @staticmethod
    def set_mocks(files, added, skipped, mock_load_files, mock_file_process):
        mock_load_files.return_value = files
        mock_file_process.return_value = added, skipped

    def make_asserts(self, mock_load_files, mock_file_process, logger):
        mock_load_files.assert_called_once_with(self.pull_source_path)

        if self.expected_file_process_calls is None:
            mock_file_process.assert_not_called()
        else:
            self.assertEqual(self.expected_file_process_calls, mock_file_process.call_args_list)

        self.assertEqual([self.expected_logger_statement], logger.output)

    def test_no_files(self):
        self.do_it()

    def test(self):
        self.file_names = ['f1', 'f2', 'f3']

        self.expected_file_process_calls = [call(self.data_dir, self.source.file_stats, self.source.event_keys) for _ in self.file_names]
        self.expected_added = len(self.file_names) * 2
        self.expected_skipped = len(self.file_names)
        self.expected_logger_statement = 'INFO:JenkinsSource:Added: {0}, skipped: {1}'.format(self.expected_added, self.expected_skipped)

        self.do_it()

class TestJenkinsSourceLoadNewFiles(unittest.TestCase):
    def setUp(self):
        self.name = 'name'
        self.data_dir = util.data_dir / 'test_dir'
        self.files_path = util.data_dir / 'cool_files'

        self.source = process.JenkinsSource(self.name, self.data_dir)

        self.file_names = []

        self.expected_files = []
        self.expected_file_load_events_call_count = 0

    def tearDown(self):
        util.rmtree(util.data_dir, no_exist_ok=True)

    @staticmethod
    def get_file(file_path, **kwargs):
        return process.DataFile(file_path)

    def do_it(self):
        self.files_path.mkdir(parents=True)

        for filename in self.file_names:
            file_path = self.files_path / filename
            if 'empty' in filename:
                file_path.open('w').close()
            else:
                with file_path.open('w') as file:
                    file.write('dummy data')

        with patch.object(process.JenkinsSource, '_get_data_file') as mock_get_file, patch.object(process.DataFile, 'load_events') as mock_file_load_events:
            self.set_mocks(mock_get_file)
            files = self.source._load_new_files(self.files_path)
            self.make_asserts(files, mock_file_load_events)

    def set_mocks(self, mock_get_file):
        mock_get_file.side_effect = self.get_file

    def make_asserts(self, actual_files, mock_file_load_events):
        self.expected_file_paths = [file.path for file in self.expected_files]
        self.actual_file_paths = [file.path for file in actual_files]
        self.assertEqual(set(self.expected_file_paths), set(self.actual_file_paths))

        self.assertEqual(self.expected_file_load_events_call_count, mock_file_load_events.call_count)

    def test_no_files(self):
        self.do_it()

    def test(self):
        self.file_names = ['f1.json', 'f2.json', 'ins.json', 'empty.json']

        self.expected_files = [process.DataFile(self.files_path / 'f1.json'), process.DataFile(self.files_path / 'f2.json')]
        self.expected_file_load_events_call_count = 2

        self.do_it()

class TestJenkinsSourcePrintFileStats(unittest.TestCase):
    pass


"""
ProductSource
"""
class TestProductSourceInit(unittest.TestCase):
    def test(self):
        self.source = process.ProductSource()
        self.assertEqual('jenkins', self.source.name)
        self.assertEqual(util.jenkins_data_dir, self.source.data_dir)

class TestProductSourceSetup(unittest.TestCase):
    def setUp(self):
        self.source = process.ProductSource()

    def tearDown(self):
        util.rmtree(util.data_dir, no_exist_ok=True)

    def test_dir_no_exist(self):
        self.source.setup()
        self.assertTrue(util.jenkins_ft_data_dir.exists())

    def test_dir_exists(self):
        util.jenkins_ft_data_dir.mkdir(parents=True, exist_ok=True)
        self.source.setup()
        self.assertTrue(util.jenkins_ft_data_dir.exists())

class TestProductSourceGetDataFile(unittest.TestCase):
    def setUp(self):
        self.source = process.ProductSource()

    def test(self):
        path = Path('path/hi.txt')
        default_instance = 'derp'

        file = self.source._get_data_file(path, default_instance=default_instance)

        self.assertEqual(path, file.path)
        self.assertEqual(default_instance, file.default_instance)


"""
InsSource
"""
class TestInsSourceInit(unittest.TestCase):
    def test(self):
        source = process.InsSource()
        self.assertEqual('ins', source.name)
        self.assertEqual(util.ins_data_dir, source.data_dir)

class TestInsSourceGetDataFile(unittest.TestCase):
    def setUp(self):
        self.source = process.InsSource()

    def test(self):
        path = Path('path/hi.txt')
        file = self.source._get_data_file(path)
        self.assertEqual(path, file.path)


"""
VicSource
"""
class TestVicSourceInit(unittest.TestCase):
    def test(self):
        source = process.VicSource()
        self.assertEqual('vic', source.name)
        self.assertEqual(util.vic_data_dir, source.data_dir)

class TestVicSourceGetDataFile(unittest.TestCase):
    def setUp(self):
        self.source = process.VicSource()

    def test_incorrect_file(self):
        path = Path('path/hi.txt')
        file = self.source._get_data_file(path)
        self.assertIsNone(file)

    def test(self):
        path = Path('path/AWS-VIC-Manager.json')
        file = self.source._get_data_file(path)
        self.assertEqual(path, file.path)


"""
CqSource
"""
class TestCqSourceInit(unittest.TestCase):
    def test(self):
        source = process.CqSource()
        self.assertEqual('cq', source.name)
        self.assertEqual(util.cq_data_dir, source.data_dir)


class TestCqSourceSetup(unittest.TestCase):
    def setUp(self):
        self.source = process.CqSource()
        self.source.data_dir.mkdir(parents=True)

        self.existing_cq_data = None

        self.expected_drs = {}

    def tearDown(self):
        util.rmtree(util.data_dir, no_exist_ok=True)

    def do_it(self):
        if self.existing_cq_data is not None:
            with util.cq_data_path.open('w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=list(self.existing_cq_data[0].keys()))
                writer.writeheader()
                writer.writerows(self.existing_cq_data)

        with patch.object(process.CqSource, '_load_event_keys'):
            self.source.setup()

        self.assertEqual(self.expected_drs, self.source.drs)

    def test_no_data_path(self):
        self.do_it()

    def test_empty_file(self):
        self.existing_cq_data = [{}]

        self.do_it()

    def test(self):
        self.existing_cq_data = [
            {'id': 'id1', 'some_field': 1},
            {'id': 'id2', 'some_field': 2},
            {'id': 'id1', 'some_field': 3}
        ]

        self.expected_drs = {
            'id1': {'id': 'id1', 'some_field': '3'},
            'id2': {'id': 'id2', 'some_field': '2'}
        }

        self.do_it()


class TestCqSourceLoadEventKeys(unittest.TestCase):
    def setUp(self):
        self.source = process.CqSource()
        self.source.data_dir.mkdir(parents=True)

        self.existing_events = None

        self.expected_existing_keys = set()

    def tearDown(self):
        util.rmtree(util.data_dir, no_exist_ok=True)

    def do_it(self):
        keys = []

        if self.existing_events is not None:
            with util.cq_events_path.open('w') as file:
                for event in self.existing_events:
                    file.write(json.dumps(event) + '\n')
                    keys.append(event['key'])

        with patch.object(process.CqCookedEvent, 'get_key') as mock_get_key:
            mock_get_key.side_effect = keys
            self.source._load_event_keys()

        self.assertEqual(self.source.event_keys, {'new': set(), 'existing': self.expected_existing_keys})

    def test_no_data_path(self):
        self.do_it()

    def test_empty_file(self):
        self.existing_events = []

        self.do_it()

    def test(self):
        self.existing_events = [
            {'key': 'event1', 'derp': 'herp'},
            {'key': 'event2', 'hello': 'hi'}
        ]

        self.expected_existing_keys = {'event1', 'event2'}

        self.do_it()


class TestCqSourceLoadNewData(unittest.TestCase):
    def setUp(self):
        self.source = process.CqSource()
        self.pull_source_path = Path(tempfile.mkdtemp())

        self.new_data = None

        self.expected_event_ids = []

    def tearDown(self):
        util.rmtree(self.pull_source_path)

    @staticmethod
    def load_dr(dr, events):
        events.append(dr['id'])

    def do_it(self):
        if self.new_data is not None:
            with (self.pull_source_path / 'added_modified.csv').open('w', newline='') as file:
                if self.new_data:
                    writer = csv.DictWriter(file, fieldnames=self.new_data[0].keys())
                    writer.writeheader()
                    writer.writerows(self.new_data)

        with patch.object(process.CqSource, '_load_dr') as mock_load_dr, patch.object(process.CqSource, '_write_events') as mock_write_events:
            mock_load_dr.side_effect = self.load_dr

            self.source.load_new_data(self.pull_source_path)

            mock_write_events.assert_called_once_with(self.expected_event_ids)

    def test_no_file(self):
        self.do_it()

    def test_empty_file(self):
        self.new_data = []

        self.do_it()

    def test(self):
        self.new_data = [
            {'id': 1, 'greeting': 'hi'},
            {'id': 2, 'greeting': 'hello'}
        ]

        self.expected_event_ids = ['1', '2']

        self.do_it()


class TestCqSourceLoadDr(unittest.TestCase):
    def setUp(self):
        self.source = process.CqSource()

        self.dr = None

        self.events = []
        self.skipped = 0

        self.expected_drs = {}
        self.expected_events = []
        self.expected_stats = {'added': 0, 'skipped': 0, 'modified_drs': set()}
        self.expected_header_fields = set()

    def do_it(self):
        self.source.dr_stats = {'skipped': self.skipped}

        self.source.dr_stats['added'] = len([e for e in self.events if e['type'] == 'add'])
        self.source.dr_stats['modified_drs'] = set([e['id'] for e in self.events if e['type'] == 'modify'])

        self.source._load_dr(self.dr, self.events)

        self.assertEqual(self.expected_drs, self.source.drs)
        self.assertEqual(self.expected_events, self.events)
        self.assertEqual(self.expected_stats, self.source.dr_stats)
        self.assertEqual(self.expected_header_fields, self.source.header_fields)

    def test_add_no_existing(self):
        self.dr = {
            'history.action_timestamp': 5,
            'id': 3
        }

        self.expected_drs = {
            3: {
                'last_changed': 5,
                'id': 3
            }
        }

        self.expected_events = [
            {'type': 'add', 'dr_id': 3, 'timestamp': 5}
        ]

        self.expected_stats = {
            'added': 1,
            'skipped': 0,
            'modified_drs': set()
        }

        self.expected_header_fields = {'last_changed', 'id'}

        self.do_it()

    def test_add_existing(self):
        self.dr = {
            'history.action_timestamp': 5,
            'id': 3
        }

        self.source.drs = {
            1: {
                'last_changed': 1,
                'id': 1
            },
            2: {
                'last_changed': 3,
                'id': 2
            }
        }

        self.events = [
            {'type': 'add', 'dr_id': 2, 'timestamp': 3}
        ]

        self.expected_drs = {
            1: {
                'last_changed': 1,
                'id': 1
            },
            2: {
                'last_changed': 3,
                'id': 2
            },
            3: {
                'last_changed': 5,
                'id': 3
            }
        }

        self.expected_events = [
            {'type': 'add', 'dr_id': 2, 'timestamp': 3},
            {'type': 'add', 'dr_id': 3, 'timestamp': 5}
        ]

        self.expected_stats = {
            'added': 2,
            'skipped': 0,
            'modified_drs': set()
        }

        self.expected_header_fields = {'last_changed', 'id'}

        self.do_it()

    def test_skip(self):
        self.dr = {
            'history.action_timestamp': 5,
            'id': 3
        }

        self.source.drs = {
            2: {
                'last_changed': 3,
                'id': 2
            },
            3: {
                'last_changed': 6,
                'id': 3
            }
        }

        self.events = [
            {'type': 'add', 'dr_id': 2, 'timestamp': 3},
            {'type': 'add', 'dr_id': 3, 'timestamp': 6}
        ]

        self.expected_drs = {
            2: {
                'last_changed': 3,
                'id': 2
            },
            3: {
                'last_changed': 6,
                'id': 3
            }
        }

        self.expected_events = [
            {'type': 'add', 'dr_id': 2, 'timestamp': 3},
            {'type': 'add', 'dr_id': 3, 'timestamp': 6}
        ]

        self.expected_stats = {
            'added': 2,
            'skipped': 1,
            'modified_drs': set()
        }

        self.do_it()

    def test_modify_same_timestamp(self):
        self.dr = {
            'history.action_timestamp': 5,
            'id': 3,
            'hello': 'hola'
        }

        self.source.drs = {
            2: {
                'last_changed': 3,
                'id': 2
            },
            3: {
                'last_changed': 5,
                'id': 3,
                'hello': 'hi'
            }
        }

        self.events = [
            {'type': 'add', 'dr_id': 2, 'timestamp': 3},
            {'type': 'add', 'dr_id': 3, 'timestamp': 5}
        ]

        self.expected_drs = {
            2: {
                'last_changed': 3,
                'id': 2
            },
            3: {
                'last_changed': 5,
                'id': 3,
                'hello': 'hola'
            }
        }

        self.expected_events = [
            {'type': 'add', 'dr_id': 2, 'timestamp': 3},
            {'type': 'add', 'dr_id': 3, 'timestamp': 5},
            {'type': 'modify', 'dr_id': 3, 'timestamp': 5, 'change_field': 'hello', 'before': 'hi', 'after': 'hola'}
        ]

        self.expected_stats = {
            'added': 2,
            'skipped': 0,
            'modified_drs': {3}
        }

        self.expected_header_fields = {'last_changed', 'id', 'hello'}

        self.do_it()

    def test_modify_later_timestamp(self):
        self.dr = {
            'history.action_timestamp': 6,
            'id': 3,
            'hello': 'hola'
        }

        self.source.drs = {
            2: {
                'last_changed': 3,
                'id': 2
            },
            3: {
                'last_changed': 5,
                'id': 3,
                'hello': 'hi'
            }
        }

        self.events = [
            {'type': 'add', 'dr_id': 2, 'timestamp': 3},
            {'type': 'add', 'dr_id': 3, 'timestamp': 5}
        ]

        self.expected_drs = {
            2: {
                'last_changed': 3,
                'id': 2
            },
            3: {
                'last_changed': 6,
                'id': 3,
                'hello': 'hola'
            }
        }

        self.expected_events = [
            {'type': 'add', 'dr_id': 2, 'timestamp': 3},
            {'type': 'add', 'dr_id': 3, 'timestamp': 5},
            {'type': 'modify', 'dr_id': 3, 'timestamp': 6, 'change_field': 'hello', 'before': 'hi', 'after': 'hola'}
        ]

        self.expected_stats = {
            'added': 2,
            'skipped': 0,
            'modified_drs': {3}
        }

        self.expected_header_fields = {'last_changed', 'id', 'hello'}

        self.do_it()

    def test_modify_no_changes(self):
        self.dr = {
            'history.action_timestamp': 6,
            'id': 3,
            'hello': 'hi'
        }

        self.source.drs = {
            2: {
                'last_changed': 3,
                'id': 2
            },
            3: {
                'last_changed': 5,
                'id': 3,
                'hello': 'hi'
            }
        }

        self.events = [
            {'type': 'add', 'dr_id': 2, 'timestamp': 3},
            {'type': 'add', 'dr_id': 3, 'timestamp': 5}
        ]

        self.expected_drs = {
            2: {
                'last_changed': 3,
                'id': 2
            },
            3: {
                'last_changed': 6,
                'id': 3,
                'hello': 'hi'
            }
        }

        self.expected_events = [
            {'type': 'add', 'dr_id': 2, 'timestamp': 3},
            {'type': 'add', 'dr_id': 3, 'timestamp': 5}
        ]

        self.expected_stats = {
            'added': 2,
            'skipped': 0,
            'modified_drs': set()
        }

        self.expected_header_fields = {'last_changed', 'id', 'hello'}

        self.do_it()


class TestCqSourceGetChanges(unittest.TestCase):
    def setUp(self):
        self.old_dr = {}
        self.new_dr = {}

        self.expected_changes = []

    def do_it(self):
        actual_changes = process.CqSource._get_changes(self.old_dr, self.new_dr)
        self.assertEqual(len(self.expected_changes), len(actual_changes))
        for change in self.expected_changes:
            self.assertIn(change, actual_changes)

    def test_empty_drs(self):
        self.do_it()

    def test_new_empty(self):
        self.old_dr = {'derp': 'herp', 'hi': 'hello'}

        self.expected_changes = [
            {'change_field': 'derp', 'before': 'herp', 'after': '%%NONE%%'},
            {'change_field': 'hi', 'before': 'hello', 'after': '%%NONE%%'}
        ]

        self.do_it()

    def test_old_empty(self):
        self.new_dr = {'derp': 'herp', 'hi': 'hello'}

        self.expected_changes = [
            {'change_field': 'derp', 'before': '%%NONE%%', 'after': 'herp'},
            {'change_field': 'hi', 'before': '%%NONE%%', 'after': 'hello'}
        ]

        self.do_it()

    def test_same(self):
        self.old_dr = {'derp': 'herp', 'hi': 'hello'}
        self.new_dr = {'derp': 'herp', 'hi': 'hello'}

        self.do_it()

    def test_added(self):
        self.old_dr = {'derp': 'herp', 'hi': 'hello'}
        self.new_dr = {'derp': 'herp', 'hi': 'hello', 'omg': 'ya'}

        self.expected_changes = [
            {'change_field': 'omg', 'before': '%%NONE%%', 'after': 'ya'}
        ]

        self.do_it()

    def test_removed(self):
        self.old_dr = {'derp': 'herp', 'hi': 'hello', 'omg': 'ya'}
        self.new_dr = {'derp': 'herp', 'hi': 'hello'}

        self.expected_changes = [
            {'change_field': 'omg', 'before': 'ya', 'after': '%%NONE%%'}
        ]

        self.do_it()

    def test_added_removed_changed(self):
        self.old_dr = {'derp': 'herp', 'hi': 'hello', 'omg': 'ya'}
        self.new_dr = {'derp': 'herp', 'hi': 'hola', 'wow': 'cool'}

        self.expected_changes = [
            {'change_field': 'omg', 'before': 'ya', 'after': '%%NONE%%'},
            {'change_field': 'wow', 'before': '%%NONE%%', 'after': 'cool'},
            {'change_field': 'hi', 'before': 'hello', 'after': 'hola'}
        ]

        self.do_it()


class TestCqSourceWriteEvents(unittest.TestCase):
    def setUp(self):
        self.source = process.CqSource()
        util.cq_data_dir.mkdir(parents=True)

        self.existing_event_keys = set()
        self.new_event_keys = set()

        self.existing_events = None

        self.events = []

        self.expected_new_event_keys = set()
        self.expected_events = []
        self.expected_logged_added_events = 0
        self.expected_logged_skipped_events = 0

    def tearDown(self):
        util.rmtree(util.data_dir)

    def load_events_file(self):
        if not util.cq_events_path.exists():
            return []

        with util.cq_events_path.open() as file:
            return [json.loads(line) for line in file]

    def do_it(self):
        if self.existing_events is not None:
            with util.cq_events_path.open('w') as file:
                for event in self.existing_events:
                    file.write(json.dumps(event) + '\n')

        self.source.event_keys['existing'] = self.existing_event_keys
        self.source.event_keys['new'] = self.new_event_keys

        get_key_values = [event['id'] for event in self.events]

        with patch.object(process.CqCookedEvent, 'get_key') as mock_get_key, self.assertLogs('CqSource', 'INFO') as logger:
            mock_get_key.side_effect = get_key_values

            self.source._write_events(self.events)

            self.assertEqual(self.expected_new_event_keys, self.source.event_keys['new'])
            self.assertEqual(self.expected_events, self.load_events_file())
            self.assertEqual('INFO:CqSource:{} added events'.format(self.expected_logged_added_events), logger.output[0])
            self.assertEqual('INFO:CqSource:{} skipped events'.format(self.expected_logged_skipped_events), logger.output[1])

    def test_no_existing_events_no_new_events(self):
        self.do_it()

    def test_no_existing_events_no_new_event_keys_some_new_events(self):
        self.events = [
            {'id': 1, 'greeting': 'hi'},
            {'id': 2, 'greeting': 'hello'}
        ]

        self.expected_new_event_keys = {1, 2}
        self.expected_events = [
            {'id': 1, 'greeting': 'hi'},
            {'id': 2, 'greeting': 'hello'}
        ]
        self.expected_logged_added_events = 2

        self.do_it()

    def test_no_existing_events_no_new_event_keys_some_new_events_one_duplicate(self):
        self.events = [
            {'id': 1, 'greeting': 'hi'},
            {'id': 2, 'greeting': 'hello'},
            {'id': 2, 'greeting': 'hola'}
        ]

        self.expected_new_event_keys = {1, 2}
        self.expected_events = [
            {'id': 1, 'greeting': 'hi'},
            {'id': 2, 'greeting': 'hello'}
        ]
        self.expected_logged_added_events = 2

        self.do_it()

    def test_no_existing_events_one_new_event_key_some_new_events(self):
        self.new_event_keys = {1}

        self.existing_events = [
            {'id': 1, 'greeting': 'hi'}
        ]

        self.events = [
            {'id': 1, 'greeting': 'hi'},
            {'id': 2, 'greeting': 'hello'},
            {'id': 3, 'greeting': 'hola'}
        ]

        self.expected_new_event_keys = {1, 2, 3}
        self.expected_events = [
            {'id': 1, 'greeting': 'hi'},
            {'id': 2, 'greeting': 'hello'},
            {'id': 3, 'greeting': 'hola'}
        ]
        self.expected_logged_added_events = 2

        self.do_it()

    def test_one_existing_event_no_new_event_keys_some_new_events(self):
        self.existing_event_keys = {1}

        self.existing_events = [
            {'id': 1, 'greeting': 'hi'}
        ]

        self.events = [
            {'id': 1, 'greeting': 'hi'},
            {'id': 2, 'greeting': 'hello'},
            {'id': 3, 'greeting': 'hola'}
        ]

        self.expected_new_event_keys = {2, 3}
        self.expected_events = [
            {'id': 1, 'greeting': 'hi'},
            {'id': 2, 'greeting': 'hello'},
            {'id': 3, 'greeting': 'hola'}
        ]
        self.expected_logged_added_events = 2
        self.expected_logged_skipped_events = 1

        self.do_it()

    def test_one_existing_event_one_new_event_key_one_new_event(self):
        self.existing_event_keys = {1}
        self.new_event_keys = {2}

        self.existing_events = [
            {'id': 1, 'greeting': 'hi'},
            {'id': 2, 'greeting': 'hello'}
        ]

        self.events = [
            {'id': 1, 'greeting': 'hi'},
            {'id': 2, 'greeting': 'hello'},
            {'id': 3, 'greeting': 'hola'}
        ]

        self.expected_new_event_keys = {2, 3}
        self.expected_events = [
            {'id': 1, 'greeting': 'hi'},
            {'id': 2, 'greeting': 'hello'},
            {'id': 3, 'greeting': 'hola'}
        ]
        self.expected_logged_added_events = 1
        self.expected_logged_skipped_events = 1

        self.do_it()


class TestCqSourceWriteDrs(unittest.TestCase):
    def setUp(self):
        self.source = process.CqSource()
        util.cq_data_dir.mkdir(parents=True)

        self.existing_drs = []

        self.expected_drs = []

    def tearDown(self):
        util.rmtree(util.data_dir)

    def do_it(self):
        if self.existing_drs:
            with util.cq_data_path.open('w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=self.existing_drs[0].keys())
                writer.writeheader()
                writer.writerows(self.existing_drs)

        with patch.object(process.Processor, 'delete_index'), patch.object(process.Processor, 'create_index'):
            self.source._write_drs()

        with util.cq_data_path.open('r', newline='') as file:
            reader = csv.DictReader(file)
            actual_drs = [row for row in reader]

        self.assertEqual(len(self.expected_drs), len(actual_drs))
        for dr in self.expected_drs:
            self.assertIn(dr, actual_drs)

    def test_no_drs(self):
        self.do_it()

    def test_no_existing_file(self):
        self.source.header_fields = ['id', 'greeting']

        self.source.drs = {
            '1': {
                'id': '1',
                'greeting': 'hi'
            },
            '2': {
                'id': '2',
                'greeting': 'hello'
            }
        }

        self.expected_drs = [
            {
                'id': '1',
                'greeting': 'hi'
            },
            {
                'id': '2',
                'greeting': 'hello'
            }
        ]

        self.do_it()

    def test_existing_file(self):
        self.existing_drs = [
            {
                'id': '1',
                'greeting': 'hi'
            },
            {
                'id': '2',
                'greeting': 'hello'
            }
        ]

        self.source.header_fields = ['id', 'greeting']

        self.source.drs = {
            '1': {
                'id': '1',
                'greeting': 'hi'
            },
            '2': {
                'id': '2',
                'greeting': 'hello'
            },
            '3': {
                'id': '3',
                'greeting': 'hola'
            }
        }

        self.expected_drs = [
            {
                'id': '1',
                'greeting': 'hi'
            },
            {
                'id': '2',
                'greeting': 'hello'
            },
            {
                'id': '3',
                'greeting': 'hola'
            }
        ]

        self.do_it()


"""
CqSourceOld
"""
class TestCqSourceOldInit(unittest.TestCase):
    def test(self):
        source = process.CqSourceOld()
        self.assertEqual('cq_old', source.name)
        self.assertEqual(util.cq_data_dir, source.data_dir)

class TestCqSourceOldLoadExistingData(unittest.TestCase):
    def setUp(self):
        self.source = process.CqSourceOld()

        self.drs = None
        self.changed_files = None

        self.expected_orig_cq_data = {}
        self.expected_orig_cq_changed_files = {}

    def tearDown(self):
        util.rmtree(util.data_dir, no_exist_ok=True)

    def do_it(self):
        util.cq_data_dir.mkdir(parents=True)

        if self.drs is not None:
            with util.cq_data_path_old.open('w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=['id', 'greeting'])
                writer.writeheader()
                writer.writerows(self.drs)

        if self.changed_files is not None:
            with util.cq_changed_files_path.open('w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=['id', 'file'])
                writer.writeheader()
                writer.writerows(self.changed_files)

        self.source.load_existing_data()

        self.make_asserts()

    def make_asserts(self):
        self.assertEqual(self.expected_orig_cq_data, self.source.orig_data)
        self.assertEqual(self.expected_orig_cq_changed_files, self.source.orig_changed_files)

    def test_no_data_files(self):
        self.do_it()

    def test_cq_data(self):
        self.drs = [
            {'id': '0', 'greeting': 'hello'},
            {'id': '1', 'greeting': 'hi'},
            {'id': '2', 'greeting': 'hola'}
        ]

        self.expected_orig_cq_data = {
            '0': {'id': '0', 'greeting': 'hello'},
            '1': {'id': '1', 'greeting': 'hi'},
            '2': {'id': '2', 'greeting': 'hola'}
        }

        self.do_it()

    def test_cq_changed_files(self):
        self.changed_files = [
            {'id': '0', 'file': 'hello'},
            {'id': '0', 'file': 'derp'},
            {'id': '1', 'file': 'hi'},
            {'id': '2', 'file': 'hola'},
            {'id': '2', 'file': 'como estas'},
            {'id': '2', 'file': 'herp'},
            {'id': '2', 'file': 'herp'}
        ]

        self.expected_orig_cq_changed_files = {
            '0': ['hello', 'derp'],
            '1': ['hi'],
            '2': ['hola', 'como estas', 'herp']
        }

        self.do_it()

    def test_both(self):
        self.drs = [
            {'id': '0', 'greeting': 'hello'},
            {'id': '1', 'greeting': 'hi'},
            {'id': '2', 'greeting': 'hola'}
        ]

        self.changed_files = [
            {'id': '0', 'file': 'hello'},
            {'id': '0', 'file': 'derp'},
            {'id': '1', 'file': 'hi'},
            {'id': '2', 'file': 'hola'},
            {'id': '2', 'file': 'como estas'},
            {'id': '2', 'file': 'herp'}
        ]

        self.expected_orig_cq_data = {
            '0': {'id': '0', 'greeting': 'hello'},
            '1': {'id': '1', 'greeting': 'hi'},
            '2': {'id': '2', 'greeting': 'hola'}
        }

        self.expected_orig_cq_changed_files = {
            '0': ['hello', 'derp'],
            '1': ['hi'],
            '2': ['hola', 'como estas', 'herp']
        }

        self.do_it()

class TestCqSourceOldLoadNewData(unittest.TestCase):
    def setUp(self):
        self.source = process.CqSourceOld()

        util.data_dir.mkdir(parents=True)
        self.file_path = util.data_dir / 'text.csv'
        self.file_path.touch()

        self.drs = []

        self.expected_new_data = {}
        self.expected_new_changed_files = {}

    def tearDown(self):
        util.rmtree(util.data_dir)

    def do_it(self):
        if self.drs:
            fields = self.drs[0].keys()
            with self.file_path.open('w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=fields)
                writer.writeheader()
                writer.writerows(self.drs)

        self.source.load_new_data(self.file_path)

    def make_asserts(self):
        self.assertEqual(self.expected_new_data, self.source.new_data)
        self.assertEqual(self.expected_new_changed_files, self.source.new_changed_files)

    def test_no_new_no_old(self):
        self.do_it()

    def test_no_new_some_old(self):
        self.source.new_data = {
            'id0': {'id': 'id0'},
            'id1': {'id': 'id1'}
        }

        self.source.new_changed_files = {
            'id0': ['f1', 'f2'],
            'id1': ['f3', 'f4']
        }

        self.expected_new_data = copy.deepcopy(self.source.new_data)
        self.expected_new_changed_files = copy.deepcopy(self.source.new_changed_files)

        self.do_it()

    def test_some_new_no_old(self):
        self.drs = [
            {'id': 'id0', 'RTCC_ChangeSet.FileList.Filename': 'f1'},
            {'id': 'id0', 'RTCC_ChangeSet.FileList.Filename': 'f2'},
            {'id': 'id1', 'RTCC_ChangeSet.FileList.Filename': 'f3'}
        ]

        self.expected_new_data = {
            'id0': {'id': 'id0'},
            'id1': {'id': 'id1'}
        }

        self.expected_new_changed_files = {
            'id0': ['f1', 'f2'],
            'id1': ['f3']
        }

        self.do_it()

    def test_some_new_some_old(self):
        self.source.new_data = {
            'id0': {'id': 'id0'},
            'id1': {'id': 'id1'}
        }

        self.source.new_changed_files = {
            'id0': ['f1', 'f2'],
            'id1': ['f3', 'f4']
        }

        self.drs = [
            {'id': 'id1', 'RTCC_ChangeSet.FileList.Filename': 'f4'},
            {'id': 'id1', 'RTCC_ChangeSet.FileList.Filename': 'f5'},
            {'id': 'id2', 'RTCC_ChangeSet.FileList.Filename': 'f6'},
            {'id': 'id2', 'RTCC_ChangeSet.FileList.Filename': 'f7'},
            {'id': 'id3', 'RTCC_ChangeSet.FileList.Filename': 'f8'}
        ]

        self.expected_new_data = {
            'id0': {'id': 'id0'},
            'id1': {'id': 'id1'},
            'id2': {'id': 'id2'},
            'id3': {'id': 'id3'}
        }

        self.expected_new_changed_files = {
            'id0': ['f1', 'f2'],
            'id1': ['f3', 'f4', 'f5'],
            'id2': ['f6', 'f7'],
            'id3': ['f8']
        }

        self.do_it()

class TestCqSourceOldProcess(unittest.TestCase):
    # TODO
    pass

class TestCqSourceOldGetUpdatedData(unittest.TestCase):
    def setUp(self):
        self.source = process.CqSourceOld()

        self.expected_added = 0
        self.expected_updated = 0
        self.expected_skipped = 0

        self.expected_updated_data = {}

    def do_it(self):
        added_rows, updated_rows, skipped_rows, updated_data = self.source._get_updated_data()
        self.make_asserts(added_rows, updated_rows, skipped_rows, updated_data)

    def make_asserts(self, added, updated, skipped, updated_data):
        self.assertEqual(self.expected_added, added)
        self.assertEqual(self.expected_updated, updated)
        self.assertEqual(self.expected_skipped, skipped)

        self.assertEqual(self.expected_updated_data, updated_data)

    def test_empty_cq_data(self):
        self.source.orig_data = {'derp': 'herp'}
        self.expected_updated_data = copy.deepcopy(self.source.orig_data)
        self.do_it()

    def test_no_new(self):
        self.source.orig_data = {
            'id0': {'id': 'id0', 'greeting': 'hi'},
            'id1': {'id': 'id1', 'greeting': 'hello'},
            'id2': {'id': 'id2', 'greeting': 'hola'}
        }

        self.source.new_data = {
            'id1': {'id': 'id1', 'greeting': 'hello'},
            'id2': {'id': 'id2', 'greeting': 'hola'}
        }

        self.expected_skipped = 2
        self.expected_updated_data = copy.deepcopy(self.source.orig_data)

        self.do_it()

    def test_one_updated(self):
        self.source.orig_data = {
            'id0': {'id': 'id0', 'greeting': 'hi'},
            'id1': {'id': 'id1', 'greeting': 'hello'},
            'id2': {'id': 'id2', 'greeting': 'hola'}
        }

        self.source.new_data = {
            'id1': {'id': 'id1', 'greeting': 'derp'},
            'id2': {'id': 'id2', 'greeting': 'hola'}
        }

        self.expected_updated = 1
        self.expected_skipped = 1

        self.expected_updated_data = {
            'id0': {'id': 'id0', 'greeting': 'hi'},
            'id1': {'id': 'id1', 'greeting': 'derp'},
            'id2': {'id': 'id2', 'greeting': 'hola'}
        }

        self.do_it()

    def test_one_added(self):
        self.source.orig_data = {
            'id0': {'id': 'id0', 'greeting': 'hi'},
            'id1': {'id': 'id1', 'greeting': 'hello'},
            'id2': {'id': 'id2', 'greeting': 'hola'}
        }

        self.source.new_data = {
            'id1': {'id': 'id1', 'greeting': 'hello'},
            'id2': {'id': 'id2', 'greeting': 'hola'},
            'id3': {'id': 'id3', 'greeting': 'herp'}
        }

        self.expected_added = 1
        self.expected_skipped = 2

        self.expected_updated_data = {
            'id0': {'id': 'id0', 'greeting': 'hi'},
            'id1': {'id': 'id1', 'greeting': 'hello'},
            'id2': {'id': 'id2', 'greeting': 'hola'},
            'id3': {'id': 'id3', 'greeting': 'herp'}
        }

        self.do_it()

    def test_one_updated_one_added(self):
        self.source.orig_data = {
            'id0': {'id': 'id0', 'greeting': 'hi'},
            'id1': {'id': 'id1', 'greeting': 'hello'},
            'id2': {'id': 'id2', 'greeting': 'hola'}
        }

        self.source.new_data = {
            'id1': {'id': 'id1', 'greeting': 'derp'},
            'id2': {'id': 'id2', 'greeting': 'hola'},
            'id3': {'id': 'id3', 'greeting': 'herp'}
        }

        self.expected_added = 1
        self.expected_updated = 1
        self.expected_skipped = 1

        self.expected_updated_data = {
            'id0': {'id': 'id0', 'greeting': 'hi'},
            'id1': {'id': 'id1', 'greeting': 'derp'},
            'id2': {'id': 'id2', 'greeting': 'hola'},
            'id3': {'id': 'id3', 'greeting': 'herp'}
        }

        self.do_it()

class TestCqSourceOldDictCompare(unittest.TestCase):
    def test_both_empty(self):
        dict1 = {}
        dict2 = {}

        self.assertTrue(process.CqSourceOld._dict_compare(dict1, dict2))

    def test_first_empty(self):
        dict1 = {'derp': 'herp'}
        dict2 = {}

        self.assertFalse(process.CqSourceOld._dict_compare(dict1, dict2))

    def test_second_empty(self):
        dict1 = {}
        dict2 = {'derp': 'herp'}

        self.assertFalse(process.CqSourceOld._dict_compare(dict1, dict2))

    def test_same_order(self):
        dict1 = {'derp': 1, 'herp': 2}
        dict2 = {'derp': 1, 'herp': 2}

        self.assertTrue(process.CqSourceOld._dict_compare(dict1, dict2))

    def test_different_values(self):
        dict1 = {'derp': 1, 'herp': 2}
        dict2 = {'derp': 1, 'herp': 5}

        self.assertFalse(process.CqSourceOld._dict_compare(dict1, dict2))

    def test_different_order(self):
        dict1 = {'derp': 1, 'herp': 2}
        dict2 = {'herp': 2, 'derp': 1}

        self.assertTrue(process.CqSourceOld._dict_compare(dict1, dict2))

    def test_more(self):
        dict1 = {'derp': 1, 'herp': 2}
        dict2 = {'derp': 1, 'herp': 2, 'lerp': 3}

        self.assertFalse(process.CqSourceOld._dict_compare(dict1, dict2))

class TestCqSourceOldWriteData(unittest.TestCase):
    def setUp(self):
        self.source = process.CqSourceOld()
        self.source.data_dir.mkdir(parents=True)

    def tearDown(self):
        util.rmtree(util.data_dir)

    def test_different_header_order_one_write(self):
        events = [
            {'id': 'myid1', 'time': 'mytime15'},
            {'id': 'myid2', 'time': 'mytime20'},
            {'time': 'mytime50', 'id': 'myid3'},
            {'time': 'mytime55', 'id': 'myid4'},
            {'id': 'myid5', 'time': 'mytime62'}
        ]
        self.source._write_data(events)

        with util.cq_data_path_old.open() as file:
            header = file.readline().strip()
            header_fields = header.split(',')
            id_index = header_fields.index('id')
            time_index = header_fields.index('time')

            for line in file:
                fields = line.split(',')
                self.assertIn('myid', fields[id_index])
                self.assertIn('mytime', fields[time_index])

    def test_different_header_order_multiple_writes(self):
        events = [
            {'id': 'myid1', 'time': 'mytime15'},
            {'id': 'myid2', 'time': 'mytime20'}
        ]
        self.source._write_data(events)

        events2 = [
            {'id': 'myid1', 'time': 'mytime15'},
            {'id': 'myid2', 'time': 'mytime20'},
            {'time': 'mytime50', 'id': 'myid3'},
            {'id': 'myid4', 'time': 'mytime55'}
        ]
        self.source._write_data(events2)

        with util.cq_data_path_old.open() as file:
            header = file.readline().strip()

        header_fields = header.split(',')
        id_index = header_fields.index('id')
        time_index = header_fields.index('time')

        with util.cq_data_path_old.open() as file:
            file.readline()
            for line in file:
                fields = line.split(',')
                self.assertIn('myid', fields[id_index])
                self.assertIn('mytime', fields[time_index])

    def test_more_fields_one_write(self):
        events = [
            {'id': 'myid1', 'time': 'mytime15'},
            {'id': 'myid2', 'time': 'mytime20'},
            {'time': 'mytime50', 'id': 'myid3', 'derp': 'herp'}
        ]
        self.source._write_data(events)

        with util.cq_data_path_old.open() as file:
            header = set(file.readline().strip().split(','))
            self.assertEqual({'id', 'time', 'derp'}, header)

            lines = [set(line.strip().split(',')) for line in file]
            self.assertEqual([
                {'myid1', 'mytime15', ''},
                {'myid2', 'mytime20', ''},
                {'myid3', 'mytime50', 'herp'}
            ], lines)

    def test_more_fields_multiple_writes(self):
        events = [
            {'id': 'myid1', 'time': 'mytime15'},
            {'id': 'myid2', 'time': 'mytime20'}
        ]
        self.source._write_data(events)

        events2 = [
            {'id': 'myid1', 'time': 'mytime15'},
            {'id': 'myid2', 'time': 'mytime20'},
            {'time': 'mytime50', 'id': 'myid3', 'derp': 'herp'}
        ]
        self.source._write_data(events2)

        with util.cq_data_path_old.open() as file:
            header = set(file.readline().strip().split(','))
            self.assertEqual({'id', 'time', 'derp'}, header)

            lines = [set(line.strip().split(',')) for line in file]
            self.assertEqual([
                {'myid1', 'mytime15', ''},
                {'myid2', 'mytime20', ''},
                {'myid3', 'mytime50', 'herp'}
            ], lines)

class TestCqSourceOldWriteChangedFilesData(unittest.TestCase):
    def setUp(self):
        self.source = process.CqSourceOld()
        self.source.data_dir.mkdir(parents=True)

    def tearDown(self):
        util.rmtree(util.data_dir)

    def test_different_header_order(self):
        self.source.new_changed_files = {
            'myid1': [
                'myfile1',
                'myfile2'
            ],
            'myid2': [
                'myfile3'
            ]
        }
        self.source._write_changed_files_data()

        with util.cq_changed_files_path.open() as file:
            header = file.readline().strip()
            fields = header.split(',')
            assert fields == ['id', 'file']

        self.source.new_changed_files = {
            'myid3': [
                'myfile4',
                'myfile5'
            ]
        }
        self.source._write_changed_files_data()

        self.source.new_changed_files = {
            'myid4': [
                'myfile6'
            ]
        }
        self.source._write_changed_files_data()

        with util.cq_changed_files_path.open() as file:
            file.readline()
            for line in file:
                fields = line.split(',')
                assert 'myid' in fields[0]
                assert 'myfile' in fields[1]


"""
VicStatusSource
"""
class TestVicStatusSourceInit(unittest.TestCase):
    def test(self):
        source = process.VicStatusSource()
        self.assertEqual('vic_status', source.name)
        self.assertEqual(util.vic_status_data_dir, source.data_dir)

class TestVicStatusSourceGetDataFile(unittest.TestCase):
    def setUp(self):
        self.source = process.VicStatusSource()

    def test(self):
        path = Path('path/hi.txt')
        file = self.source._get_data_file(path)
        self.assertEqual(path, file.path)


"""
Archive
"""
class TestArchiveGetDefaultInstance(unittest.TestCase):
    # first default prod date is 2018-01-23

    def test_before_date(self):
        archive_names = ['17-12-05_NewData.zip', '18-01-18_NewData.zip', '18-01-22_NewData.zip']
        for archive_name in archive_names:
            archive = process.Archive(archive_name, None)
            self.assertEqual(archive.default_instance, 'Development')

    def test_after_date(self):
        archive_names = ['18-01-23_NewData.zip', '18-02-01_NewData.zip', '19-01-10_NewData.zip']
        for archive_name in archive_names:
            archive = process.Archive(archive_name, None)
            self.assertEqual(archive.default_instance, 'Production')

class TestArchiveLoad(unittest.TestCase):
    def setUp(self):
        self.path = Path('archive/path.zip')
        self.sources = {'cq_old': process.CqSourceOld()}
        self.default_instance = 'def_ins'

        self.pull_dir_1 = 'p1'
        self.pull_dir_2 = 'p2'
        self.cq_file_path = 'cq_file_path'

        with patch.object(process.Archive, '_get_default_instance', return_value=self.default_instance):
            self.archive = process.Archive(self.path, self.sources)

        util.collected_dir.mkdir(parents=True)
        util.archive_dir.mkdir(parents=True)

        self.archives = []

        self.pull_dir_paths = None
        self.cq_file_path = None
        self.archive_temp_dir = None
        self.reverse = False

        self.expected_get_components_args = []
        self.expected_pull_dirs_processed = []
        self.expected_ft_info_process_called = False
        self.expected_cq_load_data_args = None
        self.expected_rmtree_args = None

    def tearDown(self):
        util.rmtree(util.data_dir)

    def do_it(self):
        with patch.object(process.Archive, '_get_components') as mock_get_components, \
                patch.object(process.Archive, '_process_pull_dir') as mock_process_pull_dir, \
                patch.object(process.FtInfo, 'process') as mock_ft_info_process, \
                patch.object(process.CqSourceOld, 'load_new_data') as mock_cq_load_new_data, \
                patch.object(Path, 'replace'), \
                patch.object(util.__class__, 'rmtree') as mock_rmtree:
            self.set_mocks(mock_get_components)
            self.archive.load(self.archives, self.reverse)
            self.make_asserts(mock_get_components, mock_process_pull_dir, mock_ft_info_process, mock_cq_load_new_data, mock_rmtree)

    def set_mocks(self, mock_get_components):
        mock_get_components.return_value = self.pull_dir_paths, self.cq_file_path, self.archive_temp_dir

    def make_asserts(self, mock_get_components, mock_process_pull_dir, mock_ft_info_process, mock_cq_load_new_data, mock_rmtree):
        mock_get_components.assert_called_once_with(self.expected_get_components_args)

        processed_pull_dirs = [args_list[0][0] for args_list in mock_process_pull_dir.call_args_list]
        self.assertEqual(self.expected_pull_dirs_processed, processed_pull_dirs)

        if self.expected_ft_info_process_called:
            self.assertEqual(1, mock_ft_info_process.call_count)
        else:
            mock_ft_info_process.assert_not_called()

        if self.expected_cq_load_data_args is not None:
            mock_cq_load_new_data.assert_called_once_with(self.expected_cq_load_data_args)
        else:
            mock_cq_load_new_data.assert_not_called()

        if self.expected_rmtree_args is not None:
            mock_rmtree.assert_called_once_with(self.expected_rmtree_args[0], no_exist_ok=self.expected_rmtree_args[1])
        else:
            mock_rmtree.assert_not_called()

    def test_none(self):
        self.do_it()

    def test(self):
        self.archives = 'cool archives, dude'
        self.pull_dir_paths = ['pull_dir1', 'pull_dir2']
        self.cq_file_path = 'cq_path.csv'
        self.archive_temp_dir = 'archive_temp_dir'

        self.expected_get_components_args = self.archives
        self.expected_pull_dirs_processed = self.pull_dir_paths
        self.expected_ft_info_process_called = True
        self.expected_cq_load_data_args = self.cq_file_path
        self.expected_rmtree_args = (self.archive_temp_dir, True)

        self.do_it()

    def test_reverse(self):
        self.archives = 'cool archives, dude'
        self.pull_dir_paths = ['pull_dir1', 'pull_dir2']
        self.cq_file_path = 'cq_path.csv'
        self.archive_temp_dir = 'archive_temp_dir'
        self.reverse = True

        self.expected_get_components_args = self.archives
        self.expected_pull_dirs_processed = ['pull_dir2', 'pull_dir1']
        self.expected_ft_info_process_called = True
        self.expected_cq_load_data_args = self.cq_file_path
        self.expected_rmtree_args = (self.archive_temp_dir, True)

        self.do_it()

class TestArchiveGetComponents(unittest.TestCase):
    def setUp(self):
        self.path = Path('dummy_path')
        self.default_instance = 'def_ins'

        with patch.object(process.Archive, '_get_default_instance', return_value=self.default_instance):
            self.archive = process.Archive(self.path, None)

        self.archives = []
        self.archive_temp_dir = None
        self.pull_dir_names = None
        self.cq_file_name = None

        self.expected_rmtree_args = None
        self.expected_extract_archive_args = None
        self.expected_get_paths_args = None

        self.expected_pull_dir_paths = None
        self.expected_cq_file_path = None
        self.expected_archive_temp_dir = None

    def tearDown(self):
        util.rmtree(util.data_dir, no_exist_ok=True)

    def do_it(self):
        if self.archive_temp_dir:
            self.archive_temp_dir.mkdir(parents=True)

            if self.pull_dir_names:
                for pull_dir_name in self.pull_dir_names:
                    pull_dir_path = self.archive_temp_dir / pull_dir_name
                    pull_dir_path.mkdir()

            if self.cq_file_name:
                cq_file_path = self.archive_temp_dir / self.cq_file_name
                cq_file_path.open('w').close()

        with patch.object(util.__class__, 'rmtree') as mock_rmtree, \
                patch.object(process.Archive, '_extract') as mock_extract, \
                patch.object(process.Archive, '_get_pull_data_paths') as mock_get_paths:
            self.set_mocks(mock_extract, mock_get_paths)
            pull_dir_paths, cq_file_path, archive_temp_dir = self.archive._get_components(self.archives)
            self.make_asserts(pull_dir_paths, cq_file_path, archive_temp_dir, mock_rmtree, mock_extract, mock_get_paths)

    def set_mocks(self, mock_extract, mock_get_paths):
        mock_extract.return_value = self.archive_temp_dir
        mock_get_paths.return_value = self.pull_dir_names, self.cq_file_name

    def make_asserts(self, pull_dir_paths, cq_file_path, archive_temp_dir, mock_rmtree, mock_extract, mock_get_paths):
        self.assertEqual(self.expected_pull_dir_paths, pull_dir_paths)
        self.assertEqual(self.expected_cq_file_path, cq_file_path)
        self.assertEqual(self.expected_archive_temp_dir, archive_temp_dir)

        if self.expected_rmtree_args is not None:
            mock_rmtree.assert_called_once_with(self.expected_rmtree_args)
        else:
            mock_rmtree.assert_not_called()

        if self.expected_extract_archive_args is not None:
            mock_extract.assert_called_once_with(self.expected_extract_archive_args)
        else:
            mock_extract.assert_not_called()

        if self.expected_get_paths_args is not None:
            self.assertEqual(1, mock_get_paths.call_count)
            args = mock_get_paths.call_args[0][0]
            self.assertEqual(set(self.expected_get_paths_args), set(args))
        else:
            mock_get_paths.assert_not_called()

    def test_folder_with_no_matching_archive(self):
        self.archive.path = util.collected_dir / 'a1'
        self.archive.name = 'a1'

        self.archives = [
            util.collected_dir / 'a1',
            util.collected_dir / 'a2.zip'
        ]

        self.do_it()

    def test_folder_with_matching_archive(self):
        self.archive.path = util.collected_dir / 'a1'
        self.archive.name = 'a1'

        self.archives = [
            util.collected_dir / 'a1',
            util.collected_dir / 'a1.zip',
            util.collected_dir / 'a2.zip'
        ]

        self.expected_rmtree_args = self.archive.path

        self.do_it()

    def test_archive(self):
        self.pull_dir_names = ['d1', 'd2']
        self.cq_file_name = 'cq.csv'

        self.archive.path = util.collected_dir / 'a1.zip'
        self.archive.name = 'a1.zip'

        self.archive_temp_dir = util.collected_dir / 'a1'

        self.archives = [
            util.collected_dir / 'a1.zip',
            util.collected_dir / 'a2.zip'
        ]

        self.expected_extract_archive_args = self.archives
        self.expected_get_paths_args = [self.archive_temp_dir / dir_name for dir_name in self.pull_dir_names] + [self.archive_temp_dir / self.cq_file_name]

        self.expected_pull_dir_paths = self.pull_dir_names
        self.expected_cq_file_path = self.cq_file_name
        self.expected_archive_temp_dir = self.archive_temp_dir

        self.do_it()

class TestArchiveExtract(unittest.TestCase):
    def setUp(self):
        self.path = Path('dummy_path')
        self.default_instance = 'def_ins'

        with patch.object(process.Archive, '_get_default_instance', return_value=self.default_instance):
            self.archive = process.Archive(self.path, None)

        util.collected_dir.mkdir(parents=True)

        self.archives = []

        self.expected_archive_temp_path = None
        self.expected_temp_path_exists = False
        self.expected_archive_contents = []
        self.expected_archives = []

    def tearDown(self):
        util.rmtree(util.data_dir)

    def do_it(self):
        open('test.txt', 'w').close()
        with zipfile.ZipFile(str(util.collected_dir) + '/a1.zip', mode='w') as archive:
            archive.write('test.txt')
        with zipfile.ZipFile(str(util.collected_dir) + '/a2.zip', mode='w') as archive:
            archive.write('test.txt')
        os.remove('test.txt')

        archive_temp_path = self.archive._extract(self.archives)

        self.make_asserts(archive_temp_path)

    def make_asserts(self, archive_temp_path):
        self.assertEqual(self.expected_archive_temp_path, archive_temp_path)
        self.assertEqual(self.expected_temp_path_exists, self.expected_archive_temp_path.exists())
        self.assertEqual(self.expected_archive_contents, util.listdir(archive_temp_path))
        self.assertEqual(self.expected_archives, self.archives)

    def test(self):
        self.archive.path = util.collected_dir / 'a1.zip'
        self.archive.name = 'a1.zip'

        self.archives = [
            util.collected_dir / 'a1.zip',
            util.collected_dir / 'a2.zip'
        ]

        self.expected_archive_temp_path = util.collected_dir / 'a1'
        self.expected_temp_path_exists = True
        self.expected_archive_contents = ['test.txt']
        self.expected_archives = [
            util.collected_dir / 'a1.zip',
            util.collected_dir / 'a2.zip'
        ]

        self.do_it()

    def test_dir_exists_not_in_archives(self):
        self.archive.path = util.collected_dir / 'a1.zip'
        self.archive.name = 'a1.zip'

        self.archives = [
            util.collected_dir / 'a1.zip',
            util.collected_dir / 'a2.zip'
        ]

        self.expected_archive_temp_path = util.collected_dir / 'a1'
        self.expected_temp_path_exists = True
        self.expected_archive_contents = ['test.txt']
        self.expected_archives = [
            util.collected_dir / 'a1.zip',
            util.collected_dir / 'a2.zip'
        ]

        self.expected_archive_temp_path.mkdir()

        self.do_it()

    def test_dir_exists_in_archives(self):
        self.archive.path = util.collected_dir / 'a1.zip'
        self.archive.name = 'a1.zip'

        self.archives = [
            util.collected_dir / 'a1',
            util.collected_dir / 'a1.zip',
            util.collected_dir / 'a2.zip'
        ]

        self.expected_archive_temp_path = util.collected_dir / 'a1'
        self.expected_temp_path_exists = True
        self.expected_archive_contents = ['test.txt']
        self.expected_archives = [
            util.collected_dir / 'a1.zip',
            util.collected_dir / 'a2.zip'
        ]

        self.expected_archive_temp_path.mkdir()

        self.do_it()

    def test_dir_not_exists_in_archives(self):
        self.archive.path = util.collected_dir / 'a1.zip'
        self.archive.name = 'a1.zip'

        self.archives = [
            util.collected_dir / 'a1',
            util.collected_dir / 'a1.zip',
            util.collected_dir / 'a2.zip'
        ]

        self.expected_archive_temp_path = util.collected_dir / 'a1'
        self.expected_temp_path_exists = True
        self.expected_archive_contents = ['test.txt']
        self.expected_archives = [
            util.collected_dir / 'a1.zip',
            util.collected_dir / 'a2.zip'
        ]

        self.do_it()


class TestArchiveGetPullDataPaths(unittest.TestCase):
    def setUp(self):
        self.path = util.collected_dir/'archive'
        self.default_instance = 'def_ins'

        with patch.object(process.Archive, '_get_default_instance', return_value=self.default_instance):
            self.archive = process.Archive(self.path, None)

        self.path.mkdir(parents=True)

        self.pull_dir_names = []
        self.cq_file_name = None

        self.expected_pull_dirs = []
        self.expected_cq_file_path = None

    def tearDown(self):
        util.rmtree(util.data_dir)

    def do_it(self):
        archive_contents = []
        for pull_dir in self.pull_dir_names:
            pull_dir_path = self.archive.path / pull_dir
            pull_dir_path.mkdir()
            archive_contents.append(pull_dir_path)

        if self.cq_file_name:
            cq_file_path = self.archive.path / self.cq_file_name
            cq_file_path.open('w').close()
            archive_contents.append(cq_file_path)

        pull_dirs, cq_file_path = self.archive._get_pull_data_paths(archive_contents)
        self.make_asserts(pull_dirs, cq_file_path)

    def make_asserts(self, pull_dirs, cq_file_path):
        self.assertEqual(self.expected_pull_dirs, pull_dirs)
        self.assertEqual(self.expected_cq_file_path, cq_file_path)

    def test_no_contents(self):
        self.do_it()

    def test_one_pull_dir_no_cq(self):
        self.pull_dir_names = ['d1']
        self.expected_pull_dirs = [self.archive.path / pull_dir for pull_dir in self.pull_dir_names]
        self.do_it()

    def test_two_pull_dir_no_cq(self):
        self.pull_dir_names = ['d1', 'd2']
        self.expected_pull_dirs = [self.archive.path / pull_dir for pull_dir in self.pull_dir_names]
        self.do_it()

    def test_no_pull_dir_one_cq(self):
        self.cq_file_name = 'CQ_Data.csv'
        self.expected_cq_file_path = self.archive.path / self.cq_file_name
        self.do_it()

    def test_two_pull_dir_one_cq(self):
        self.pull_dir_names = ['d1', 'd2']
        self.cq_file_name = 'CQ_Data.csv'

        self.expected_pull_dirs = [self.archive.path / pull_dir for pull_dir in self.pull_dir_names]
        self.expected_cq_file_path = self.archive.path / self.cq_file_name

        self.do_it()

class TestArchiveProcessPullDir(unittest.TestCase):
    def setUp(self):
        self.path = util.collected_dir / 'archive'
        self.default_instance = 'def_ins'
        self.archive_sources = {'jenkins': process.ProductSource(), 'ins': process.InsSource(), 'vic': process.VicSource(), 'cq_old': process.CqSourceOld(), 'vic_status': process.VicStatusSource()}
        self.pull_dir_name = '181203182605'
        self.pull_dir_path = self.path / self.pull_dir_name

        with patch.object(process.Archive, '_get_default_instance', return_value=self.default_instance):
            self.archive = process.Archive(self.path, self.archive_sources)

        self.pull_dir_path.mkdir(parents=True)

        self.pull_sources = []

        self.expected_source_load_new_data_arg_list = None

    def tearDown(self):
        util.rmtree(util.data_dir)

    def do_it(self):
        for source in self.pull_sources:
            source_path = self.pull_dir_path / source
            source_path.mkdir()

        with patch.object(process.JenkinsSource, 'load_new_data') as mock_source_load_new_data:
            self.archive._process_pull_dir(self.pull_dir_path, None)
            self.make_asserts(mock_source_load_new_data)

    def make_asserts(self, mock_source_load_new_data):
        if self.expected_source_load_new_data_arg_list is not None:
            self.assertEqual(len(self.expected_source_load_new_data_arg_list), mock_source_load_new_data.call_count)
            for expected_call in self.expected_source_load_new_data_arg_list:
                self.assertIn(expected_call, mock_source_load_new_data.call_args_list)
        else:
            mock_source_load_new_data.assert_not_called()

    def test_no_sources(self):
        self.do_it()

    def test(self):
        self.pull_sources = ['jenkins', 'ins', 'vic', 'vic_status', 'unknown']
        self.expected_source_load_new_data_arg_list = [
            call(self.pull_dir_path / 'jenkins', default_instance=self.default_instance, ft_info=None),
            call(self.pull_dir_path / 'ins'),
            call(self.pull_dir_path / 'vic'),
            call(self.pull_dir_path / 'vic_status', timestamp=1543861565.0)]
        self.do_it()


"""
FtInfo
"""
class TestFtInfoProcessFile(unittest.TestCase):
    def setUp(self):
        self.ft_info = process.FtInfo()
        self.ft_dir = util.jenkins_data_dir / 'ft'
        self.ft_dir.mkdir(parents=True)

    def tearDown(self):
        util.rmtree(util.data_dir)

    def test_no_content(self):
        filename = 'Production_ci1'
        table_name = 'features'
        content = {}

        self.ft_info._process_file(filename, table_name, content)

        self.assertEqual(util.listdir(self.ft_dir), [])

    def test_bad_table_name(self):
        filename = 'Production_ci1'
        table_name = 'derp'
        content = {'hi'}

        with self.assertRaises(Exception):
            self.ft_info._process_file(filename, table_name, content)

    def test_features_no_existing(self):
        filename = 'Production_ci1_1.7.1.0'
        table_name = 'features'
        content = {
            '1': {'id': '1', 'result': 'passed', 'job_timestamp': '1'},
            '2': {'id': '2', 'result': 'failed', 'job_timestamp': '2'},
            '3': {'id': '3', 'result': 'passed', 'job_timestamp': '3'}
        }

        self.ft_info._process_file(filename, table_name, content)

        full_filename = '{0}_{1}.csv'.format(filename, table_name)

        self.assertEqual(util.listdir(self.ft_dir), [full_filename])

        expected = {}
        file_path = self.ft_dir / full_filename
        with file_path.open(newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                expected[row['id']] = dict(row)

        self.assertEqual(expected, content)

    def test_scenarios_no_existing(self):
        filename = 'Production_ci1_1.7.1.0'
        table_name = 'scenarios'
        content = {
            '1': {'id': '1', 'result': 'passed', 'job_timestamp': '1'},
            '2': {'id': '2', 'result': 'failed', 'job_timestamp': '2'},
            '3': {'id': '3', 'result': 'passed', 'job_timestamp': '3'}
        }

        self.ft_info._process_file(filename, table_name, content)

        full_filename = '{0}_{1}.csv'.format(filename, table_name)

        self.assertEqual(util.listdir(self.ft_dir), [full_filename])

        expected = {}
        file_path = self.ft_dir / full_filename
        with file_path.open(newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                expected[row['id']] = dict(row)

        self.assertEqual(expected, content)

    @patch('pivt.process.FtInfo._gen_ft_feature_key')
    def test_features_one_existing_inclusive(self, mock_key_func):
        filename = 'Production_ci1_1.7.1.0'
        table_name = 'features'
        content = {
            '1': {'id': '1', 'result': 'passed', 'job_timestamp': '1'},
            '2': {'id': '2', 'result': 'failed', 'job_timestamp': '2'},
            '3': {'id': '3', 'result': 'passed', 'job_timestamp': '3'}
        }

        full_filename = '{0}_{1}.csv'.format(filename, table_name)

        existing_content = [
            {'id': '2', 'result': 'failed', 'job_timestamp': '2'}
        ]

        file_path = self.ft_dir / full_filename
        with file_path.open('w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=existing_content[0].keys())
            writer.writeheader()
            writer.writerows(existing_content)

        def key_func(a_row):
            return a_row['id']

        mock_key_func.side_effect = key_func

        self.ft_info._process_file(filename, table_name, content)

        self.assertEqual(util.listdir(self.ft_dir), [full_filename])

        expected = {}
        file_path = self.ft_dir / full_filename
        with file_path.open(newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                expected[row['id']] = dict(row)

        self.assertEqual(expected, content)

    @patch('pivt.process.FtInfo._gen_ft_scenario_key')
    def test_scenarios_one_existing_exclusive(self, mock_key_func):
        filename = 'Production_ci1_1.7.1.0'
        table_name = 'scenarios'
        content = {
            '1': {'id': '1', 'result': 'passed', 'job_timestamp': '1'},
            '3': {'id': '3', 'result': 'passed', 'job_timestamp': '3'}
        }

        full_filename = '{0}_{1}.csv'.format(filename, table_name)

        existing_content = [
            {'id': '2', 'result': 'failed', 'job_timestamp': '2'}
        ]

        file_path = self.ft_dir / full_filename
        with file_path.open('w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=existing_content[0].keys())
            writer.writeheader()
            writer.writerows(existing_content)

        def key_func(a_row):
            return a_row['id']

        mock_key_func.side_effect = key_func

        self.ft_info._process_file(filename, table_name, content)

        self.assertEqual(util.listdir(self.ft_dir), [full_filename])

        expected = {}
        file_path = self.ft_dir / full_filename
        with file_path.open(newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                expected[row['id']] = dict(row)

        content['2'] = existing_content[0]

        self.assertEqual(expected, content)

    @patch('pivt.process.FtInfo._gen_ft_feature_key')
    def test_no_new_no_existing(self, mock_key_func):
        filename = 'Production_ci1_1.7.1.0'
        table_name = 'features'

        def key_func(a_row):
            return a_row['id']

        mock_key_func.side_effect = key_func

        self.ft_info._process_file(filename, table_name, {})

        self.assertEqual(util.listdir(self.ft_dir), [])

    @patch('pivt.process.FtInfo._gen_ft_feature_key')
    def test_no_new_one_existing(self, mock_key_func):
        filename = 'Production_ci1_1.7.1.0'
        table_name = 'features'
        content = {
            '2': {'id': '2', 'result': 'failed', 'job_timestamp': '2'}
        }

        full_filename = '{0}_{1}.csv'.format(filename, table_name)

        existing_content = [
            {'id': '2', 'result': 'failed', 'job_timestamp': '2'}
        ]

        file_path = self.ft_dir / full_filename
        with file_path.open('w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=existing_content[0].keys())
            writer.writeheader()
            writer.writerows(existing_content)

        def key_func(a_row):
            return a_row['id']

        mock_key_func.side_effect = key_func

        self.ft_info._process_file(filename, table_name, content)

        self.assertEqual(util.listdir(self.ft_dir), [full_filename])

        expected = {}
        file_path = self.ft_dir / full_filename
        with file_path.open(newline='') as file:
            reader = csv.DictReader(file)
            for row in reader:
                expected[row['id']] = dict(row)

        self.assertEqual(expected, content)


class TestFtInfoLoadFtInfo(unittest.TestCase):
    def test_no_reports(self):
        event = {'no': 'reports'}

        features, scenarios = process.FtInfo.load_ft_info(event)

        expected_features = {}
        expected_scenarios = {}

        self.assertEqual(expected_features, features)
        self.assertEqual(expected_scenarios, scenarios)

    def test_empty_reports(self):
        event = {
            'id': 1,
            'reports': {}
        }

        features, scenarios = process.FtInfo.load_ft_info(event)

        expected_features = {}
        expected_scenarios = {}

        self.assertEqual(expected_features, features)
        self.assertEqual(expected_scenarios, scenarios)

    def test_null_report(self):
        event = {
            'id': 1,
            'reports': {'r1': {}}
        }

        features, scenarios = process.FtInfo.load_ft_info(event)

        expected_features = {}
        expected_scenarios = {}

        self.assertEqual(expected_features, features)
        self.assertEqual(expected_scenarios, scenarios)

    def test_invalid(self):
        with open(find_file('resources/cucumber_reports/invalid.json'), 'r') as file:
            report = json.loads(file.read())

        event = {
            'instance': 'Production',
            'ci': 'ci1',
            'number': 5,
            'timestamp': 10,
            'reports': {
                'invalid.json': report
            }
        }

        features, scenarios = process.FtInfo.load_ft_info(event)

        expected_features = {}
        expected_scenarios = {}

        self.assertEqual(expected_features, features)
        self.assertEqual(expected_scenarios, scenarios)

    def test_invalid_report(self):
        with open(find_file('resources/cucumber_reports/invalid-report.json'), 'r') as file:
            report = json.loads(file.read())

        event = {
            'instance': 'Production',
            'ci': 'ci1',
            'number': 5,
            'timestamp': 10,
            'reports': {
                'invalid-report.json': report
            }
        }

        features, scenarios = process.FtInfo.load_ft_info(event)

        expected_features = {}
        expected_scenarios = {}

        self.assertEqual(expected_features, features)
        self.assertEqual(expected_scenarios, scenarios)

    def test_invalid_report_2(self):
        with open(find_file('resources/cucumber_reports/invalid-report-2.json'), 'r') as file:
            report = json.loads(file.read())

        event = {
            'instance': 'Production',
            'ci': 'ci1',
            'number': 5,
            'timestamp': 10,
            'release': '1.7.1.0',
            'reports': {
                'invalid-report-2.json': report
            }
        }

        features, scenarios = process.FtInfo.load_ft_info(event)

        expected_features = {
                'Production:ci1:5:10:invalid-report-2.json:simpleId': {
                    # 'duration': 123456789,
                    'id': 'simpleId',
                    'job_ci': 'ci1',
                    'job_instance': 'Production',
                    'job_number': 5,
                    'job_timestamp': 10,
                    'job_release': '1.7.1.0',
                    'name': 'Simple '
                            'feature',
                    'report_name': 'invalid-report-2.json',
                    'result': 'passed',
                    'tags': ''
                }
            }
        expected_scenarios = {}

        self.assertEqual(expected_features, features)
        self.assertEqual(expected_scenarios, scenarios)

    def test_simple(self):
        with open(find_file('resources/cucumber_reports/simple.json'), 'r') as file:
            report = json.loads(file.read())

        event = {
            'instance': 'Production',
            'ci': 'ci1',
            'number': 5,
            'timestamp': 10,
            'release': '1.7.1.0',
            'reports': {
                'simple.json': report
            }
        }

        features, scenarios = process.FtInfo.load_ft_info(event)

        expected_features = {
            'Production:ci1:5:10:simple.json:simpleId': {
                # 'duration': 123456789,
                'id': 'simpleId',
                'job_ci': 'ci1',
                'job_instance': 'Production',
                'job_number': 5,
                'job_timestamp': 10,
                'job_release': '1.7.1.0',
                'name': 'Simple '
                        'feature',
                'report_name': 'simple.json',
                'result': 'passed',
                'tags': ''
            }
        }
        expected_scenarios = {
            'Production:ci1:5:10:simpleId:Simple scenario': {
                # 'duration': 123456789,
                'feature_id': 'simpleId',
                'id': 'Simple '
                      'scenario',
                'job_ci': 'ci1',
                'job_instance': 'Production',
                'job_number': 5,
                'job_timestamp': 10,
                'job_release': '1.7.1.0',
                'name': 'Simple '
                        'scenario',
                'report_name': 'simple.json',
                'result': 'passed',
                'tags': ''
            }
        }

        self.assertEqual(expected_features, features)
        self.assertEqual(expected_scenarios, scenarios)

    def test_simple_artifact_in_report_name(self):
        with open(find_file('resources/cucumber_reports/simple.json'), 'r') as file:
            report = json.loads(file.read())

        event = {
            'instance': 'Production',
            'ci': 'ci1',
            'number': 5,
            'timestamp': 10,
            'release': '1.7.1.0',
            'reports': {
                'http://derp/artifact/simple.json': report
            }
        }

        features, scenarios = process.FtInfo.load_ft_info(event)

        expected_features = {
            'Production:ci1:5:10:simple.json:simpleId': {
                # 'duration': 123456789,
                'id': 'simpleId',
                'job_ci': 'ci1',
                'job_instance': 'Production',
                'job_number': 5,
                'job_timestamp': 10,
                'job_release': '1.7.1.0',
                'name': 'Simple '
                        'feature',
                'report_name': 'simple.json',
                'result': 'passed',
                'tags': ''
            }
        }
        expected_scenarios = {
            'Production:ci1:5:10:simpleId:Simple scenario': {
                # 'duration': 123456789,
                'feature_id': 'simpleId',
                'id': 'Simple '
                      'scenario',
                'job_ci': 'ci1',
                'job_instance': 'Production',
                'job_number': 5,
                'job_timestamp': 10,
                'job_release': '1.7.1.0',
                'name': 'Simple '
                        'scenario',
                'report_name': 'simple.json',
                'result': 'passed',
                'tags': ''
            }
        }

        self.assertEqual(expected_features, features)
        self.assertEqual(expected_scenarios, scenarios)

    def test_complex(self):
        with open(find_file('resources/cucumber_reports/sample.json'), 'r', encoding='utf-8') as file:
            report = json.loads(file.read())

        event = {
            'instance': 'Production',
            'ci': 'ci1',
            'number': 5,
            'timestamp': 10,
            'release': '1.7.1.0',
            'reports': {
                'sample.json': report
            }
        }

        features, scenarios = process.FtInfo.load_ft_info(event)

        expected_features = {
            "Production:ci1:5:10:sample.json:account-holder-withdraws-cash": {
                "name": "1st feature",
                "id": "account-holder-withdraws-cash",
                "result": "passed",
                # "duration": 99263122889,
                "tags": {'featureTag'},
                "report_name": "sample.json",
                "job_instance": "Production",
                "job_ci": "ci1",
                "job_number": 5,
                "job_timestamp": 10,
                'job_release': '1.7.1.0'
            },
            "Production:ci1:5:10:sample.json:account-holder-withdraws-more-cash": {
                "name": "Second feature",
                "id": "account-holder-withdraws-more-cash",
                "result": "failed",
                # "duration": 92610000,
                "tags": {''},
                "report_name": "sample.json",
                "job_instance": "Production",
                "job_ci": "ci1",
                "job_number": 5,
                "job_timestamp": 10,
                'job_release': '1.7.1.0'
            },
            "Production:ci1:5:10:sample.json:failed-background": {
                "name": "some feature",
                "id": "failed-background",
                "result": "failed",
                # "duration": 99124118111,
                "tags": {'featureTag'},
                "report_name": "sample.json",
                "job_instance": "Production",
                "job_ci": "ci1",
                "job_number": 5,
                "job_timestamp": 10,
                'job_release': '1.7.1.0'
            }
        }
        expected_scenarios = {
            "Production:ci1:5:10:account-holder-withdraws-cash:account-holder-withdraws-cash;account-has-'sufficient-funds';;2": {
                "name": "Account has <sufficient funds>",
                "id": "account-holder-withdraws-cash;account-has-'sufficient-funds';;2",
                "result": "passed",
                # "duration": 139004778,
                "tags": {"featureTag", "fast", "checkout"},
                "report_name": "sample.json",
                "feature_id": "account-holder-withdraws-cash",
                "job_instance": "Production",
                "job_ci": "ci1",
                "job_number": 5,
                "job_timestamp": 10,
                'job_release': '1.7.1.0'
            },
            "Production:ci1:5:10:account-holder-withdraws-more-cash:account-holder-withdraws-more-cash;account-has-sufficient-funds;;2": {
                "name": "Account may not have sufficient funds",
                "id": "account-holder-withdraws-more-cash;account-has-sufficient-funds;;2",
                "result": "failed",
                # "duration": 92050000,
                "tags": {"checkout"},
                "report_name": "sample.json",
                "feature_id": "account-holder-withdraws-more-cash",
                "job_instance": "Production",
                "job_ci": "ci1",
                "job_number": 5,
                "job_timestamp": 10,
                'job_release': '1.7.1.0'
            },
            "Production:ci1:5:10:account-holder-withdraws-more-cash:account-holder-withdraws-more-cash;clean-up": {
                "name": "Clean-up",
                "id": "account-holder-withdraws-more-cash;clean-up",
                "result": "passed",
                # "duration": 560000,
                "tags": {''},
                "report_name": "sample.json",
                "feature_id": "account-holder-withdraws-more-cash",
                "job_instance": "Production",
                "job_ci": "ci1",
                "job_number": 5,
                "job_timestamp": 10,
                'job_release': '1.7.1.0'
            },
            "Production:ci1:5:10:account-holder-withdraws-more-cash:undefined-result": {
                "name": "This step has no result...",
                "id": "undefined-result",
                "result": "skipped",
                # "duration": 0,
                "tags": {''},
                "report_name": "sample.json",
                "feature_id": "account-holder-withdraws-more-cash",
                "job_instance": "Production",
                "job_ci": "ci1",
                "job_number": 5,
                "job_timestamp": 10,
                'job_release': '1.7.1.0'
            },
            "Production:ci1:5:10:failed-background:failed-background;account-has-'sufficient-funds';;2": {
                "name": "Account has <sufficient funds>",
                "id": "failed-background;account-has-'sufficient-funds';;2",
                "result": "failed",
                # "duration": 0,
                "tags": {"featureTag", "fast", "checkout"},
                "report_name": "sample.json",
                "feature_id": "failed-background",
                "job_instance": "Production",
                "job_ci": "ci1",
                "job_number": 5,
                "job_timestamp": 10,
                'job_release': '1.7.1.0'
            }
        }

        for name, item in features.items():
            if 'tags' in item:
                item['tags'] = set(item['tags'].split(':'))

        for name, item in scenarios.items():
            if 'tags' in item:
                item['tags'] = set(item['tags'].split(':'))

        self.assertEqual(expected_features, features)
        self.assertEqual(expected_scenarios, scenarios)

    def test_duplicate_scenarios_one_report(self):
        with open(find_file('resources/cucumber_reports/duplicate-scenarios-1.json'), 'r', encoding='utf-8') as file:
            report = json.loads(file.read())

        event = {
            'instance': 'Production',
            'ci': 'ci1',
            'number': 5,
            'timestamp': 10,
            'release': '1.7.1.0',
            'reports': {
                'sample.json': report
            }
        }

        features, scenarios = process.FtInfo.load_ft_info(event)

        expected_features = {
            "Production:ci1:5:10:sample.json:1st-feature": {
                "name": "1st feature",
                "id": "1st-feature",
                "result": "passed",
                "tags": '',
                "report_name": "sample.json",
                "job_instance": "Production",
                "job_ci": "ci1",
                "job_number": 5,
                "job_timestamp": 10,
                'job_release': '1.7.1.0'
            },
            "Production:ci1:5:10:sample.json:2nd-feature": {
                "name": "2nd feature",
                "id": "2nd-feature",
                "result": "failed",
                "tags": '',
                "report_name": "sample.json",
                "job_instance": "Production",
                "job_ci": "ci1",
                "job_number": 5,
                "job_timestamp": 10,
                'job_release': '1.7.1.0'
            }
        }
        expected_scenarios = {
            "Production:ci1:5:10:1st-feature:1st-feature;1st-scenario": {
                "name": "1st scenario",
                "id": "1st-feature;1st-scenario",
                "result": "passed",
                "tags": '',
                "report_name": "sample.json",
                "feature_id": "1st-feature",
                "job_instance": "Production",
                "job_ci": "ci1",
                "job_number": 5,
                "job_timestamp": 10,
                'job_release': '1.7.1.0'
            },
            "Production:ci1:5:10:2nd-feature:2nd-feature;1st-scenario": {
                "name": "1st scenario",
                "id": "2nd-feature;1st-scenario",
                "result": "failed",
                "tags": '',
                "report_name": "sample.json",
                "feature_id": "2nd-feature",
                "job_instance": "Production",
                "job_ci": "ci1",
                "job_number": 5,
                "job_timestamp": 10,
                'job_release': '1.7.1.0'
            },
            "Production:ci1:5:10:2nd-feature:2nd-feature;2nd-scenario": {
                "name": "2nd scenario",
                "id": "2nd-feature;2nd-scenario",
                "result": "skipped",
                "tags": '',
                "report_name": "sample.json",
                "feature_id": "2nd-feature",
                "job_instance": "Production",
                "job_ci": "ci1",
                "job_number": 5,
                "job_timestamp": 10,
                'job_release': '1.7.1.0'
            },
        }

        self.assertEqual(expected_features, features)
        self.assertEqual(expected_scenarios, scenarios)

    def test_duplicate_scenarios_multiple_reports(self):
        with open(find_file('resources/cucumber_reports/duplicate-scenarios-1.json'), 'r', encoding='utf-8') as file:
            report1 = json.loads(file.read())

        with open(find_file('resources/cucumber_reports/duplicate-scenarios-2.json'), 'r', encoding='utf-8') as file:
            report2 = json.loads(file.read())

        event = {
            'instance': 'Production',
            'ci': 'ci1',
            'number': 5,
            'timestamp': 10,
            'release': '1.7.1.0',
            'reports': {
                'sample.json': report1,
                'sample2.json': report2
            }
        }

        features, scenarios = process.FtInfo.load_ft_info(event)

        expected_features = {
            "Production:ci1:5:10:sample.json:1st-feature": {
                "name": "1st feature",
                "id": "1st-feature",
                "result": "passed",
                "tags": '',
                "report_name": "sample.json",
                "job_instance": "Production",
                "job_ci": "ci1",
                "job_number": 5,
                "job_timestamp": 10,
                'job_release': '1.7.1.0'
            },
            "Production:ci1:5:10:sample.json:2nd-feature": {
                "name": "2nd feature",
                "id": "2nd-feature",
                "result": "failed",
                "tags": '',
                "report_name": "sample.json",
                "job_instance": "Production",
                "job_ci": "ci1",
                "job_number": 5,
                "job_timestamp": 10,
                'job_release': '1.7.1.0'
            }
        }
        expected_scenarios = {
            "Production:ci1:5:10:1st-feature:1st-feature;1st-scenario": {
                "name": "1st scenario",
                "id": "1st-feature;1st-scenario",
                "result": "passed",
                "tags": '',
                "report_name": "sample.json",
                "feature_id": "1st-feature",
                "job_instance": "Production",
                "job_ci": "ci1",
                "job_number": 5,
                "job_timestamp": 10,
                'job_release': '1.7.1.0'
            },
            "Production:ci1:5:10:2nd-feature:2nd-feature;1st-scenario": {
                "name": "1st scenario",
                "id": "2nd-feature;1st-scenario",
                "result": "failed",
                "tags": '',
                "report_name": "sample.json",
                "feature_id": "2nd-feature",
                "job_instance": "Production",
                "job_ci": "ci1",
                "job_number": 5,
                "job_timestamp": 10,
                'job_release': '1.7.1.0'
            },
            "Production:ci1:5:10:2nd-feature:2nd-feature;2nd-scenario": {
                "name": "2nd scenario",
                "id": "2nd-feature;2nd-scenario",
                "result": "passed",
                "tags": '',
                "report_name": "sample2.json",
                "feature_id": "2nd-feature",
                "job_instance": "Production",
                "job_ci": "ci1",
                "job_number": 5,
                "job_timestamp": 10,
                'job_release': '1.7.1.0'
            },
        }

        self.assertEqual(expected_features, features)
        self.assertEqual(expected_scenarios, scenarios)

    def test_simple_2(self):
        with open(find_file('resources/cucumber_reports/simple-2.json'), 'r', encoding='utf-8') as file:
            report = json.loads(file.read())

        event = {
            'instance': 'Production',
            'ci': 'ci1',
            'number': 5,
            'timestamp': 10,
            'release': '1.7.1.0',
            'reports': {
                'sample.json': report
            }
        }

        features, scenarios = process.FtInfo.load_ft_info(event)

        expected_features = {
            "Production:ci1:5:10:sample.json:1st-feature": {
                "name": "1st feature",
                "id": "1st-feature",
                "result": "failed",
                "tags": '',
                "report_name": "sample.json",
                "job_instance": "Production",
                "job_ci": "ci1",
                "job_number": 5,
                "job_timestamp": 10,
                'job_release': '1.7.1.0'
            },
            "Production:ci1:5:10:sample.json:2nd-feature": {
                "name": "2nd feature",
                "id": "2nd-feature",
                "result": "failed",
                "tags": '',
                "report_name": "sample.json",
                "job_instance": "Production",
                "job_ci": "ci1",
                "job_number": 5,
                "job_timestamp": 10,
                'job_release': '1.7.1.0'
            }
        }
        expected_scenarios = {
            "Production:ci1:5:10:1st-feature:1st-feature;1st-scenario": {
                "name": "1st scenario",
                "id": "1st-feature;1st-scenario",
                "result": "passed",
                "tags": '',
                "report_name": "sample.json",
                "feature_id": "1st-feature",
                "job_instance": "Production",
                "job_ci": "ci1",
                "job_number": 5,
                "job_timestamp": 10,
                'job_release': '1.7.1.0'
            },
            "Production:ci1:5:10:1st-feature:1st-feature;2nd-scenario": {
                "name": "2nd scenario",
                "id": "1st-feature;2nd-scenario",
                "result": "failed",
                "tags": '',
                "report_name": "sample.json",
                "feature_id": "1st-feature",
                "job_instance": "Production",
                "job_ci": "ci1",
                "job_number": 5,
                "job_timestamp": 10,
                'job_release': '1.7.1.0'
            },
            "Production:ci1:5:10:2nd-feature:2nd-feature;1st-scenario": {
                "name": "1st scenario",
                "id": "2nd-feature;1st-scenario",
                "result": "failed",
                "tags": '',
                "report_name": "sample.json",
                "feature_id": "2nd-feature",
                "job_instance": "Production",
                "job_ci": "ci1",
                "job_number": 5,
                "job_timestamp": 10,
                'job_release': '1.7.1.0'
            },
            "Production:ci1:5:10:2nd-feature:2nd-feature;2nd-scenario": {
                "name": "2nd scenario",
                "id": "2nd-feature;2nd-scenario",
                "result": "skipped",
                "tags": '',
                "report_name": "sample.json",
                "feature_id": "2nd-feature",
                "job_instance": "Production",
                "job_ci": "ci1",
                "job_number": 5,
                "job_timestamp": 10,
                'job_release': '1.7.1.0'
            },
        }

        self.assertEqual(expected_features, features)
        self.assertEqual(expected_scenarios, scenarios)


class TestFtTagsGetFtTags(unittest.TestCase):
    def test_no_tags(self):
        element = {'no': 'tags'}

        actual = process.FtInfo._get_ft_tags(element)
        expected = []

        self.assertEqual(actual, expected)

    def test_empty_tags(self):
        element = {'id': 1, 'tags': []}

        actual = process.FtInfo._get_ft_tags(element)
        expected = []

        self.assertEqual(actual, expected)

    def test(self):
        element = {
            'id': 1,
            'tags': [
                {'name': '@dict_with_at', 'type': 'derp'},
                {'name': 'dict_no_at', 'type': 'herp'},
                '@str_with_at',
                'str_no_at',
                {'name': '@dict_with_at', 'type': 'derp'}
            ]
        }

        actual = set(process.FtInfo._get_ft_tags(element))
        expected = {'dict_with_at', 'dict_no_at', 'str_with_at', 'str_no_at'}

        self.assertEqual(actual, expected)

    def test_unknown_tag_type(self):
        element = {
            'id': 1,
            'tags': [
                {'name': '@dict', 'type': 'derp'},
                '@str',
                5
            ]
        }

        with self.assertRaises(Exception):
            process.FtInfo._get_ft_tags(element)


class TestFtInfoGenFtScenarioKey(unittest.TestCase):
    def test(self):
        scenario = {'job_instance': 'Production', 'job_ci': 'ci1', 'job_number': 5, 'job_timestamp': 3, 'feature_id': 'f1', 'id': 's1', 'duration': 7}
        self.assertEqual(process.FtInfo._gen_ft_scenario_key(scenario), 'Production:ci1:5:3:f1:s1')

class TestFtInfoGenFtFeatureKey(unittest.TestCase):
    def test(self):
        feature = {'job_instance': 'Production', 'job_ci': 'ci1', 'job_number': 5, 'job_timestamp': 3, 'report_name': 'report1', 'id': 'f1', 'duration': 7}
        self.assertEqual(process.FtInfo._gen_ft_feature_key(feature), 'Production:ci1:5:3:report1:f1')

class TestFtInfoUpdate(unittest.TestCase):
    def test(self):
        ft_info = process.FtInfo()
        ft_info.ft_info = {
            'f1': {
                'features': {
                    'feat1': {'id': 'feat1'},
                    'feat2': {'id': 'feat2'}
                },
                'scenarios': {
                    'scen1': {'id': 'scen1'},
                    'scen2': {'id': 'scen2'}
                }
            },
            'f2': {
                'features': {
                    'feat3': {'id': 'feat3'},
                    'feat4': {'id': 'feat4'}
                }
            },
            'f3': {
                'scenarios': {
                    'scen3': {'id': 'scen3'},
                    'scen4': {'id': 'scen4'}
                }
            }
        }

        ft_info2 = {
            'f2': {
                'features': {
                    'feat4': {'id': 'feat4'},
                    'feat5': {'id': 'feat5'}
                },
                'scenarios': {
                    'scen5': {'id': 'scen5'},
                    'scen6': {'id': 'scen6'}
                }
            },
            'f3': {
                'features': {
                    'feat6': {'id': 'feat6'}
                },
                'scenarios': {
                    'scen7': {'id': 'scen7'}
                }
            },
            'f4': {
                'features': {
                    'feat7': {'id': 'feat7'}
                },
                'scenarios': {
                    'scen8': {'id': 'scen8'}
                }
            }
        }

        ft_info.update(ft_info2)

        self.assertEqual({
            'f1': {
                'features': {
                    'feat1': {'id': 'feat1'},
                    'feat2': {'id': 'feat2'}
                },
                'scenarios': {
                    'scen1': {'id': 'scen1'},
                    'scen2': {'id': 'scen2'}
                }
            },
            'f2': {
                'features': {
                    'feat3': {'id': 'feat3'},
                    'feat4': {'id': 'feat4'},
                    'feat5': {'id': 'feat5'}
                },
                'scenarios': {
                    'scen5': {'id': 'scen5'},
                    'scen6': {'id': 'scen6'}
                }
            },
            'f3': {
                'features': {
                    'feat6': {'id': 'feat6'}
                },
                'scenarios': {
                    'scen3': {'id': 'scen3'},
                    'scen4': {'id': 'scen4'},
                    'scen7': {'id': 'scen7'}
                }
            },
            'f4': {
                'features': {
                    'feat7': {'id': 'feat7'}
                },
                'scenarios': {
                    'scen8': {'id': 'scen8'}
                }
            }
        }, ft_info.ft_info)


"""
DataFile
"""
class TestDataFileIsEmpty(unittest.TestCase):
    def setUp(self):
        util.data_dir.mkdir()

    def tearDown(self):
        util.rmtree(util.data_dir)

    @patch('pivt.process.DataFile._normalize_filename')
    def test_empty(self, mock_normalize):
        mock_normalize.return_value = None

        file_path = util.data_dir / 'test.txt'
        file_path.touch()

        data_file = process.DataFile(file_path)

        self.assertTrue(data_file.is_empty())

    @patch('pivt.process.DataFile._normalize_filename')
    def test_not_empty(self, mock_normalize):
        mock_normalize.return_value = None

        file_path = util.data_dir / 'test.txt'
        with file_path.open('w') as file:
            file.write('hi!')

        data_file = process.DataFile(file_path)

        self.assertFalse(data_file.is_empty())

class TestDataFileConstructDbPath(unittest.TestCase):
    def test(self):
        data_dir = Path('/data')
        data_file = process.DataFile(Path('/path/omg/hi.txt'))
        self.assertEqual(Path('/data/hi.txt'), data_file._construct_db_path(data_dir))


"""
JsonDataFile
"""
class TestJsonDataFileLoadEvents(unittest.TestCase):
    @patch('pivt.process.JsonDataFile._load_event')
    @patch('pivt.process.DataFile._normalize_filename')
    def test(self, mock_normalize, mock_load_event):
        mock_normalize.return_value = None

        util.data_dir.mkdir()

        file_path = util.data_dir / 'test.txt'
        with file_path.open('w') as file:
            file.write('hi!\n')
            file.write('hello\n')
            file.write('world\n')

        data_file = process.JsonDataFile(file_path)

        data_file.load_events()

        mock_load_event.assert_has_calls([
            call('hi!\n'),
            call('hello\n'),
            call('world\n')
        ])

        util.rmtree(util.data_dir)

class TestJsonFileProcess(unittest.TestCase):
    def setUp(self):
        self.file_path = util.data_dir / 'test.json'

        self.data_file = process.JsonDataFile(self.file_path)

        self.data_dir = util.data_dir / 'test_dir'
        self.data_dir.mkdir(parents=True)

        self.db_file = self.data_dir / util.basename(self.file_path)

        self.file_stats = {}
        self.event_keys = {}

        self.expected_file_stats = {}
        self.expected_events = {}
        self.expected_added = 0
        self.expected_skipped = 0

    def tearDown(self):
        util.rmtree(util.data_dir)

    def make_db_files(self):
        for filename, stats in self.event_keys.items():
            for status, event_keys in stats.items():
                if not event_keys:
                    continue
                file_path = self.data_dir / filename
                with file_path.open('a') as file:
                    for key in event_keys:
                        event = {'id': key}
                        file.write(json.dumps(event) + '\n')

    def load_events(self):
        events = []
        with self.db_file.open() as file:
            for line in file:
                events.append(json.loads(line))
        return events

    def do_it(self):
        self.make_db_files()
        self.set_mocks()

        added, skipped = self.data_file.process(self.data_dir, self.file_stats, self.event_keys)

        self.make_asserts(added, skipped)

    def set_mocks(self):
        pass

    def make_asserts(self, added, skipped):
        self.assertEqual(self.expected_file_stats, self.file_stats)

        actual_events = self.load_events()
        self.assertEqual(len(self.expected_events), len(actual_events))
        for expected_event in self.expected_events:
            self.assertIn(expected_event, actual_events)

        self.assertEqual(self.expected_added, added)
        self.assertEqual(self.expected_skipped, skipped)

    def test_all_new(self):
        self.data_file.events = {
            '1': {'id': '1'},
            '2': {'id': '2'}
        }

        self.expected_file_stats = {
            'test.json': {
                'added': 2,
                'skipped': 0
            }
        }

        self.expected_events = [
            {'id': '1'},
            {'id': '2'}
        ]

        self.expected_added = 2
        self.expected_skipped = 0

        self.do_it()

    def test_no_new(self):
        self.data_file.events = {
            '1': {'id': '1'},
            '2': {'id': '2'}
        }

        self.event_keys['test.json'] = {
            'existing': {'1', '2'},
            'new': set()
        }

        self.expected_file_stats = {
            'test.json': {
                'added': 0,
                'skipped': 2
            }
        }

        self.expected_events = [
            {'id': '1'},
            {'id': '2'}
        ]

        self.expected_added = 0
        self.expected_skipped = 2

        self.do_it()

    def test_mix(self):
        self.data_file.events = {
            '1': {'id': '1'},
            '2': {'id': '2'},
            '3': {'id': '3'}
        }

        self.event_keys['test.json'] = {
            'existing': {'1'},
            'new': {'2'}
        }

        self.expected_file_stats['test.json'] = {
            'added': 1,
            'skipped': 1
        }

        self.expected_events = [
            {'id': '1'},
            {'id': '2'},
            {'id': '3'}
        ]

        self.expected_added = 1
        self.expected_skipped = 2

        self.do_it()

    def test_existing_stats(self):
        self.data_file.events = {
            '1': {'id': '1'},
            '2': {'id': '2'},
            '3': {'id': '3'}
        }

        self.file_stats['test.json'] = {
            'added': 3,
            'skipped': 2
        }

        self.event_keys['test.json'] = {
            'existing': {'1'},
            'new': {'2'}
        }

        self.expected_file_stats['test.json'] = {
            'added': 4,
            'skipped': 3
        }

        self.expected_events = [
            {'id': '1'},
            {'id': '2'},
            {'id': '3'}
        ]

        self.expected_added = 1
        self.expected_skipped = 2

        self.do_it()


"""
ProductDataFile
"""
class TestProductDataFileNormalizeFilename(unittest.TestCase):
    def do_it(self, path_name, default_instance, expected):
        data_file = process.ProductDataFile(Path(path_name), default_instance)
        self.assertEqual(expected, data_file.name)

    def test_no_instance_default_dev_no_sub(self):
        self.do_it('jenkins/ci2_Build.json', 'Development', 'Development_ci2_Build.json')

    def test_no_instance_default_prod_no_sub(self):
        self.do_it('jenkins/ci2_Build.json', 'Production', 'Production_ci2_Build.json')

    def test_instance_dev_default_dev_no_sub(self):
        self.do_it('jenkins/Development_ci2_Build.json', 'Development', 'Development_ci2_Build.json')

    def test_instance_dev_default_prod_no_sub(self):
        self.do_it('jenkins/Development_ci2_Build.json', 'Production', 'Development_ci2_Build.json')

    def test_instance_prod_default_dev_no_sub(self):
        self.do_it('jenkins/Production_ci2_Build.json', 'Development', 'Production_ci2_Build.json')

    def test_instance_prod_default_prod_no_sub(self):
        self.do_it('jenkins/Production_ci2_Build.json', 'Production', 'Production_ci2_Build.json')

    def test_no_instance_default_dev_with_sub(self):
        self.do_it('jenkins/ci3-sub_Build.json', 'Development', 'Development_ci3_Build.json')

    def test_no_instance_default_prod_with_sub(self):
        self.do_it('jenkins/ci3-sub_Build.json', 'Production', 'Production_ci3_Build.json')

    def test_instance_dev_default_dev_with_sub(self):
        self.do_it('jenkins/Development_ci3-sub_Build.json', 'Development', 'Development_ci3_Build.json')

    def test_instance_dev_default_prod_with_sub(self):
        self.do_it('jenkins/Development_ci3-sub_Build.json', 'Production', 'Development_ci3_Build.json')

    def test_instance_prod_default_dev_with_sub(self):
        self.do_it('jenkins/Production_ci3-sub_Build.json', 'Development', 'Production_ci3_Build.json')

    def test_instance_prod_default_prod_with_sub(self):
        self.do_it('jenkins/Production_ci3-sub_Build.json', 'Production', 'Production_ci3_Build.json')

class TestProductDataFileLoadEvent(unittest.TestCase):
    def setUp(self):
        self.path = Path('dummy_path')
        self.default_instance = 'default_instance'

        self.data_file = process.ProductDataFile(self.path, self.default_instance)

        self.event = {}
        self.event_key = 'coolkey'

        self.expected_strip_called = False
        self.expected_load_ft_info_called = False
        self.expected_events = {}

    def do_it(self):
        raw_event = json.dumps(self.event)

        with patch.object(process.ProductRawEvent, 'cook') as mock_event_cook, \
                patch.object(process.ProductDataFile, '_load_ft_info') as mock_load_ft_info, \
                patch.object(process.ProductCookedEvent, 'get_key') as mock_event_get_key:
            self.set_mocks(raw_event, mock_event_cook, mock_event_get_key)
            self.data_file._load_event(raw_event)
            self.make_asserts(mock_event_cook, mock_load_ft_info)

    def set_mocks(self, raw_event, mock_event_cook, mock_event_get_key):
        mock_event_cook.return_value = process.ProductCookedEvent(raw_event)
        mock_event_get_key.return_value = self.event_key

    def make_asserts(self, mock_event_cook, mock_load_ft_info):
        self.assertEqual(self.expected_strip_called, mock_event_cook.called)
        self.assertEqual(self.expected_load_ft_info_called, mock_load_ft_info.called)
        self.assertEqual(self.expected_events, self.data_file.events)

    def test_building_event(self):
        self.event = {'cool': 'word', 'building': True}
        self.do_it()

    def test_basic_event(self):
        self.event = {'cool': 'word', 'id': 2, 'stage': 'Build'}
        self.expected_strip_called = True
        self.expected_events = {
            'coolkey': self.event
        }
        self.do_it()

    def test_basic_event_overwrite(self):
        self.event = {'cool': 'word', 'id': 2, 'stage': 'Build'}
        self.data_file.events = {
            'coolkey': {'cool': 'word', 'id': 1, 'stage': 'Build'}
        }
        self.expected_strip_called = True
        self.expected_events = {
            'coolkey': self.event
        }
        self.do_it()

    def test_ft_event(self):
        self.event = {'id': 2, 'stage': 'AWS_FunctionalTest'}
        self.expected_strip_called = True
        self.expected_load_ft_info_called = True
        self.expected_events = {
            'coolkey': self.event
        }
        self.do_it()

class TestProductDataFileLoadFtInfo(unittest.TestCase):
    def setUp(self):
        self.path = Path('dummy_path')
        self.default_instance = 'default_instance'

        self.data_file = process.ProductDataFile(self.path, self.default_instance)

        self.event = {}
        self.features = {}
        self.scenarios = {}

        self.expected_ft_info = {}

    def do_it(self):
        with patch.object(process.FtInfo, 'load_ft_info') as mock_ft_info_load:
            self.set_mocks(mock_ft_info_load)
            self.data_file._load_ft_info(self.event)
            self.make_asserts()

    def set_mocks(self, mock_ft_info_load):
        mock_ft_info_load.return_value = self.features, self.scenarios

    def make_asserts(self):
        self.assertEqual(self.expected_ft_info, self.data_file.ft_info_dict)
        self.assertTrue('reports' not in self.event)

    def test_no_ft_info(self):
        instance = 'Production'
        ci = 'ci1'
        release = '1.7.2.0'

        ft_info_filename = '{0}_{1}_{2}'.format(instance, ci, release)

        self.event = {'instance': instance, 'ci': ci, 'release': release}

        self.expected_ft_info = {
            ft_info_filename: {
                'features': {},
                'scenarios': {}
            }
        }

        self.do_it()

    def test_fresh(self):
        instance = 'Production'
        ci = 'ci1'
        release = '1.7.2.0'

        ft_info_filename = '{0}_{1}_{2}'.format(instance, ci, release)

        self.event = {'instance': instance, 'ci': ci, 'release': release, 'reports': 'cool reports'}
        self.features = {
            'f1': 'hi'
        }
        self.scenarios = {
            's1': 'hola',
            's2': 'hello'
        }

        self.expected_ft_info = {
            ft_info_filename: {
                'features': {
                    'f1': 'hi'
                },
                'scenarios': {
                    's1': 'hola',
                    's2': 'hello'
                }
            }
        }

        self.do_it()

    def test_new_file(self):
        instance = 'Production'
        ci = 'ci1'
        release = '1.7.2.0'

        ft_info_filename = '{0}_{1}_{2}'.format(instance, ci, release)

        self.event = {'instance': instance, 'ci': ci, 'release': release, 'reports': 'cool reports'}
        self.features = {
            'f1': 'hi'
        }
        self.scenarios = {
            's1': 'hola',
            's2': 'hello'
        }

        self.data_file.ft_info_dict = {
            'other_file': {
                'features': 'derp',
                'scenarios': 'herp'
            }
        }

        self.expected_ft_info = {
            'other_file': {
                'features': 'derp',
                'scenarios': 'herp'
            },
            ft_info_filename: {
                'features': {
                    'f1': 'hi'
                },
                'scenarios': {
                    's1': 'hola',
                    's2': 'hello'
                }
            }
        }

        self.do_it()

    def test_existing_file(self):
        instance = 'Production'
        ci = 'ci1'
        release = '1.7.2.0'

        ft_info_filename = '{0}_{1}_{2}'.format(instance, ci, release)

        self.event = {'instance': instance, 'ci': ci, 'release': release, 'reports': 'cool reports'}
        self.features = {
            'f2': 'hi'
        }
        self.scenarios = {
            's2': 'hola',
            's3': 'hello'
        }

        self.data_file.ft_info_dict = {
            ft_info_filename: {
                'features': {
                    'f1': 'derp'
                },
                'scenarios': {
                    's1': 'herp',
                    's2': 'hola'
                }
            }
        }

        self.expected_ft_info = {
            ft_info_filename: {
                'features': {
                    'f1': 'derp',
                    'f2': 'hi'
                },
                'scenarios': {
                    's1': 'herp',
                    's2': 'hola',
                    's3': 'hello'
                }
            }
        }

        self.do_it()


"""
InsDataFile
"""
class TestInsDataFileNormalizeFilename(unittest.TestCase):
    def do_it(self, path_name, expected):
        data_file = process.InsDataFile(Path(path_name))
        self.assertEqual(expected, data_file.name)

    def test_no_instance_default_dev_no_sub(self):
        self.do_it('ins/Core1.json', 'Core1_develop.json')

    def test_dev_instance(self):
        self.do_it('ins/Core1_develop.json', 'Core1_develop.json')

    def test_master_instance(self):
        self.do_it('ins/Core1_master.json', 'Core1_master.json')

class TestInsDataFileLoadEvent(unittest.TestCase):
    def setUp(self):
        self.path = Path('dummy_path')

        self.data_file = process.InsDataFile(self.path)

        self.event = {}
        self.event_key = 'coolkey'

        self.expected_strip_called = False
        self.expected_events = {}

    def do_it(self):
        raw_event = json.dumps(self.event)

        with patch.object(process.InsRawEvent, 'cook') as mock_event_cook, \
                patch.object(process.InsCookedEvent, 'get_key') as mock_event_get_key:
            self.set_mocks(raw_event, mock_event_cook, mock_event_get_key)
            self.data_file._load_event(raw_event)
            self.make_asserts(mock_event_cook)

    def set_mocks(self, raw_event, mock_event_cook, mock_event_get_key):
        mock_event_cook.return_value = process.InsCookedEvent(raw_event)
        mock_event_get_key.return_value = self.event_key

    def make_asserts(self, mock_event_cook):
        self.assertEqual(self.expected_strip_called, mock_event_cook.called)
        self.assertEqual(self.expected_events, self.data_file.events)

    def test_building_event(self):
        self.event = {'cool': 'word', 'status': 'IN_PROGRESS'}
        self.do_it()

    def test_basic_event(self):
        self.event = {'cool': 'word', 'id': 2, 'stage': 'Build', 'status': 'DONE'}
        self.expected_strip_called = True
        self.expected_events = {
            'coolkey': self.event
        }
        self.do_it()

    def test_basic_event_overwrite(self):
        self.event = {'cool': 'word', 'id': 2, 'stage': 'Build'}
        self.data_file.events = {
            'coolkey': {'cool': 'word', 'id': 1, 'stage': 'Build'}
        }
        self.expected_strip_called = True
        self.expected_events = {
            'coolkey': self.event
        }
        self.do_it()


"""
VicDataFile
"""
class TestVicDataFileNormalizeFilename(unittest.TestCase):
    def do_it(self, path_name, expected):
        data_file = process.VicDataFile(Path(path_name))
        self.assertEqual(expected, data_file.name)

    def test_no_instance_default_dev_no_sub(self):
        self.do_it('vic/AWS-VIC-Manager.json', 'Production_AWS-VIC-Manager.json')

    def test_dev_instance(self):
        self.do_it('vic/Production_AWS-VIC-Manager.json', 'Production_AWS-VIC-Manager.json')

    def test_master_instance(self):
        self.do_it('vic/Development_AWS-VIC-Manager.json', 'Development_AWS-VIC-Manager.json')

class TestVicDataFileLoadEvent(unittest.TestCase):
    def setUp(self):
        self.path = Path('dummy_path')

        self.data_file = process.VicDataFile(self.path)

        self.event = {}
        self.event_key = 'coolkey'

        self.expected_cooked_called = False
        self.expected_events = {}

    def do_it(self):
        raw_event = json.dumps(self.event)

        with patch.object(process.VicRawEvent, 'cook') as mock_event_cook, \
                patch.object(process.VicCookedEvent, 'get_key') as mock_event_get_key:
            self.set_mocks(raw_event, mock_event_cook, mock_event_get_key)
            self.data_file._load_event(raw_event)
            self.make_asserts(mock_event_cook)

    def set_mocks(self, raw_event, mock_event_cook, mock_event_get_key):
        mock_event_cook.return_value = process.VicCookedEvent(raw_event)
        mock_event_get_key.return_value = self.event_key

    def make_asserts(self, mock_event_cook):
        self.assertEqual(self.expected_cooked_called, mock_event_cook.called)
        self.assertEqual(self.expected_events, self.data_file.events)

    def test_building1_event(self):
        self.event = {'cool': 'word', 'building': True}
        self.do_it()

    def test_building2_event(self):
        self.event = {'cool': 'word', 'status': 'IN_PROGRESS'}
        self.do_it()

    def test_basic_event(self):
        self.event = {'cool': 'word', 'id': 2, 'stage': 'Build', 'status': 'DONE'}
        self.expected_cooked_called = True
        self.expected_events = {
            'coolkey': self.event
        }
        self.do_it()

    def test_basic_event_overwrite(self):
        self.event = {'cool': 'word', 'id': 2, 'stage': 'Build'}
        self.data_file.events = {
            'coolkey': {'cool': 'word', 'id': 1, 'stage': 'Build'}
        }
        self.expected_cooked_called = True
        self.expected_events = {
            'coolkey': self.event
        }
        self.do_it()


"""
VicStatusDataFile
"""
class TestVicStatusDataFileLoadEvent(unittest.TestCase):
    def setUp(self):
        self.path = Path('dummy_path')

        self.data_file = process.VicStatusDataFile(self.path)

        self.event = {}
        self.cooked_events = []
        self.cooked_event_keys = []

        self.expected_events = {}

    def do_it(self):
        raw_data = json.dumps(self.event)

        with patch.object(process.VicStatusRawEvent, 'cook') as mock_event_cook, \
                patch.object(process.VicStatusCookedEvent, 'get_key') as mock_event_get_key:
            self.set_mocks(mock_event_cook, mock_event_get_key)
            self.data_file._load_event(raw_data)
            self.make_asserts()

    def set_mocks(self, mock_event_cook, mock_event_get_key):
        mock_event_cook.return_value = self.cooked_events
        mock_event_get_key.side_effect = self.cooked_event_keys

    def make_asserts(self):
        self.assertEqual(self.expected_events, self.data_file.events)

    def test(self):
        self.event = {'derp': 'herp'}
        self.cooked_events = [
            process.VicStatusCookedEvent({'id': 1}),
            process.VicStatusCookedEvent({'id': 2}),
            process.VicStatusCookedEvent({'id': 3})
        ]
        self.cooked_event_keys = ['k1', 'k2', 'k3']

        self.expected_events = {
            'k1': self.cooked_events[0],
            'k2': self.cooked_events[1],
            'k3': self.cooked_events[2]
        }

        self.do_it()


"""
JsonDictEvent
"""
class TestJsonDictEventInit(unittest.TestCase):
    def setUp(self):
        self.default_keys = [1, 2, 3, 4, 5]
        self.default_values = ['a', 'b', 'c', 'd', 'e']

    def create_dict_event(self, keys, values):
        return dict(zip(keys, values))

    def create_string_event(self, keys, values):
        return json.dumps(self.create_dict_event(keys, values))

    def create_test_criteria(self, keys, values,
            test_case_generator, expected_generator):
        test_case = test_case_generator(keys, values)
        expected = util.inner_stringify(expected_generator(keys, values))

        return process.JsonDictEvent(test_case), expected

    def test_string_empty(self):
        keys = []
        values = []
        json_event, expected = self.create_test_criteria(
            keys=keys,
            values=values,
            test_case_generator=self.create_string_event,
            expected_generator=self.create_dict_event)

        self.assertIsInstance(json_event, dict)
        self.assertEqual(json_event, expected)

    def test_string_instance(self):
        json_event, expected = self.create_test_criteria(
            keys=self.default_keys,
            values=self.default_values,
            test_case_generator=self.create_string_event,
            expected_generator=self.create_dict_event)

        self.assertIsInstance(json_event, dict)
        self.assertEqual(json_event, expected)

    def test_dict_empty(self):
        keys = []
        values = []

        json_event, expected = self.create_test_criteria(
            keys=keys,
            values=values,
            test_case_generator=self.create_dict_event,
            expected_generator=self.create_dict_event)

        self.assertIsInstance(json_event, dict)
        self.assertEqual(json_event, expected)

    def test_dict_instance(self):
        json_event, expected = self.create_test_criteria(
            keys=self.default_keys,
            values=self.default_values,
            test_case_generator=self.create_dict_event,
            expected_generator=self.create_dict_event)

        self.assertIsInstance(json_event, dict)
        self.assertEqual(json_event, expected)

    def test_integrity(self):
        test_case_str = self.create_string_event(
            self.default_keys, self.default_values)
        test_case_dict = self.create_dict_event(
            self.default_keys, self.default_values)
        test_case_str_copy = copy.deepcopy(test_case_str)
        test_case_dict_copy = copy.deepcopy(test_case_dict)

        json_event_str = process.JsonDictEvent(test_case_str)
        json_event_dict = process.JsonDictEvent(test_case_dict)

        self.assertIsNot(json_event_str, test_case_str)
        self.assertEqual(test_case_str, test_case_str_copy)
        self.assertIsNot(json_event_dict, test_case_dict)
        self.assertEqual(test_case_dict, test_case_dict_copy)

    def test_bad_instance(self):
        with self.assertRaises(TypeError):
            _ = process.JsonDictEvent([])


"""
JsonListEvent
"""
class TestJsonListEventInit(unittest.TestCase):
    def setUp(self):
        self.default_values = ['a', 'b', 'c', 'd', 'e']

    @staticmethod
    def create_list_event(values):
        return values

    @staticmethod
    def create_string_event(values):
        return json.dumps(values)

    def create_test_criteria(self, values, test_case_generator, expected_generator):
        test_case = test_case_generator(values)
        expected = util.inner_stringify(expected_generator(values))

        return process.JsonListEvent(test_case), expected

    def test_string_empty(self):
        values = []
        json_event, expected = self.create_test_criteria(
            values=values,
            test_case_generator=self.create_string_event,
            expected_generator=self.create_list_event)

        self.assertIsInstance(json_event, list)
        self.assertEqual(json_event, expected)

    def test_string_instance(self):
        json_event, expected = self.create_test_criteria(
            values=self.default_values,
            test_case_generator=self.create_string_event,
            expected_generator=self.create_list_event)

        self.assertIsInstance(json_event, list)
        self.assertEqual(json_event, expected)

    def test_list_empty(self):
        values = []

        json_event, expected = self.create_test_criteria(
            values=values,
            test_case_generator=self.create_list_event,
            expected_generator=self.create_list_event)

        self.assertIsInstance(json_event, list)
        self.assertEqual(json_event, expected)

    def test_dict_instance(self):
        json_event, expected = self.create_test_criteria(
            values=self.default_values,
            test_case_generator=self.create_list_event,
            expected_generator=self.create_list_event)

        self.assertIsInstance(json_event, list)
        self.assertEqual(json_event, expected)

    def test_integrity(self):
        test_case_str = self.create_string_event(self.default_values)
        test_case_dict = self.create_list_event(self.default_values)
        test_case_str_copy = copy.deepcopy(test_case_str)
        test_case_dict_copy = copy.deepcopy(test_case_dict)

        json_event_str = process.JsonListEvent(test_case_str)
        json_event_dict = process.JsonListEvent(test_case_dict)

        self.assertIsNot(json_event_str, test_case_str)
        self.assertEqual(test_case_str, test_case_str_copy)
        self.assertIsNot(json_event_dict, test_case_dict)
        self.assertEqual(test_case_dict, test_case_dict_copy)

    def test_bad_instance(self):
        with self.assertRaises(TypeError):
            _ = process.JsonListEvent({})


"""
JenkinsRawEvent
"""
class TestGetParameters(unittest.TestCase):
    def test_empty_event(self):
        event = {}
        expected = {}

        self.assertEqual(expected, process.JenkinsRawEvent(event)._get_parameters())

    def test_empty_actions(self):
        event = {'actions': []}
        expected = {}

        self.assertEqual(expected, process.JenkinsRawEvent(event)._get_parameters())

    def test_no_parameters(self):
        event = {
            'actions': [
                {
                    '_class': 'hudson.model.CauseAction',
                    'causes': []
                }
            ]
        }

        expected = {}

        self.assertEqual(expected, process.JenkinsRawEvent(event)._get_parameters())

    def test_empty_parameters(self):
        event = {
            'actions': [
                {
                    '_class': 'hudson.model.ParametersAction',
                    'parameters': []
                }
            ]
        }

        expected = {}

        self.assertEqual(expected, process.JenkinsRawEvent(event)._get_parameters())

    def test_one_parameter(self):
        event = {
            'actions': [
                {
                    '_class': 'hudson.model.ParametersAction',
                    'parameters': [
                        {'name': 'PIPELINE_VERSION', 'value': '1.2.3.4.434'}
                    ]
                }
            ]
        }

        expected = {'PIPELINE_VERSION': '1.2.3.4.434'}

        self.assertEqual(expected, process.JenkinsRawEvent(event)._get_parameters())

    def test_two_parameters(self):
        event = {
            'actions': [
                {
                    '_class': 'hudson.model.ParametersAction',
                    'parameters': [
                        {'name': 'CI', 'value': 'ci4'},
                        {'name': 'PIPELINE_VERSION', 'value': '1.2.3.4.434'}
                    ]
                }
            ]
        }

        expected = {'CI': 'ci4', 'PIPELINE_VERSION': '1.2.3.4.434'}

        self.assertEqual(expected, process.JenkinsRawEvent(event)._get_parameters())

    def test_empty_action_with_parameters(self):
        event = {
            'actions': [
                {},
                {
                    '_class': 'hudson.model.ParametersAction',
                    'parameters': [
                        {'name': 'CI', 'value': 'ci4'},
                        {'name': 'PIPELINE_VERSION', 'value': '1.2.3.4.434'}
                    ]
                }
            ]
        }

        expected = {'CI': 'ci4', 'PIPELINE_VERSION': '1.2.3.4.434'}

        self.assertEqual(expected, process.JenkinsRawEvent(event)._get_parameters())

    def test_non_interesting_action_with_parameters(self):
        event = {
            'actions': [
                {
                    '_class': 'hudson.model.CauseAction',
                    'causes': []
                },
                {
                    '_class': 'hudson.model.ParametersAction',
                    'parameters': [
                        {'name': 'CI', 'value': 'ci4'},
                        {'name': 'PIPELINE_VERSION', 'value': '1.2.3.4.434'}
                    ]
                }
            ]
        }

        expected = {'CI': 'ci4', 'PIPELINE_VERSION': '1.2.3.4.434'}

        self.assertEqual(expected, process.JenkinsRawEvent(event)._get_parameters())

    def test_multiple_parameter_actions(self):
        event = {
            'actions': [
                {
                    '_class': 'hudson.model.ParametersAction',
                    'parameters': [
                        {'name': 'CI', 'value': 'ci4'},
                        {'name': 'BASELINE_VERSION', 'value': '1.2.3.4'},
                        {'name': 'CLEARCASE_VIEW', 'value': 'gpsbuild_ci4_RelCandidate_int_dev'}
                    ]
                },
                {
                    '_class': 'hudson.model.ParametersAction',
                    'parameters': [
                        {'name': 'PIPELINE_VERSION', 'value': '1.2.3.4.434'}
                    ]
                }
            ]
        }

        expected = {'CI': 'ci4', 'BASELINE_VERSION': '1.2.3.4', 'CLEARCASE_VIEW': 'gpsbuild_ci4_RelCandidate_int_dev', 'PIPELINE_VERSION': '1.2.3.4.434'}

        self.assertEqual(expected, process.JenkinsRawEvent(event)._get_parameters())


"""
ProductRawEvent
"""
class TestProductRawEventInit(unittest.TestCase):
    def test_instance(self):
        pass

    def test_assignment(self):
        pass

    def test_integrity(self):
        pass

class TestProductRawEventCook(unittest.TestCase):
    @patch('pivt.process.ProductRawEvent._get_derived_cause')
    @patch('pivt.process.ProductRawEvent._get_upstream')
    @patch('pivt.process.ProductRawEvent._parse_unit_test_event')
    @patch('pivt.process.ProductRawEvent._get_iteration')
    @patch('pivt.process.ProductRawEvent._get_release')
    @patch('pivt.process.JenkinsRawEvent._get_parameters')
    def test_most_basic_build(self, mock_get_parameters, mock_get_release, mock_get_iteration, mock_parse_ut_event, mock_get_upstream, mock_get_derived_cause):
        mock_get_parameters.return_value = {}
        mock_get_release.return_value = None
        mock_get_iteration.return_value = None
        mock_get_upstream.return_value = None, None
        mock_get_derived_cause.return_value = 'Not Assigned'

        event = {'ci': 'ci2', 'stage': 'Build'}
        new_event = process.ProductRawEvent(event, 'Production').cook()

        self.assertEqual(new_event, {'ci': 'ci2', 'stage': 'Build', 'iteration': None, 'release': None, 'ss': 'ss5', 'instance': 'Production', 'cause': 'Not Assigned', 'derived_cause': 'Not Assigned'})
        self.assertFalse(mock_parse_ut_event.called)

    @patch('pivt.process.ProductRawEvent._get_derived_cause')
    @patch('pivt.process.ProductRawEvent._get_upstream')
    @patch('pivt.process.ProductRawEvent._parse_unit_test_event')
    @patch('pivt.process.ProductRawEvent._get_iteration')
    @patch('pivt.process.ProductRawEvent._get_release')
    @patch('pivt.process.JenkinsRawEvent._get_parameters')
    def test_basic_build_no_upstream_project(self, mock_get_parameters, mock_get_release, mock_get_iteration, mock_parse_ut_event, mock_get_upstream, mock_get_derived_cause):
        mock_get_parameters.return_value = {}
        mock_get_release.return_value = None
        mock_get_iteration.return_value = None
        mock_get_upstream.return_value = None, 5
        mock_get_derived_cause.return_value = 'Not Assigned'

        event = {'ci': 'ci2', 'stage': 'Build'}
        new_event = process.ProductRawEvent(event, 'Production').cook()

        self.assertEqual(new_event, {'ci': 'ci2', 'stage': 'Build', 'iteration': None, 'release': None, 'ss': 'ss5', 'instance': 'Production', 'cause': 'Not Assigned', 'derived_cause': 'Not Assigned'})
        self.assertFalse(mock_parse_ut_event.called)

    @patch('pivt.process.ProductRawEvent._get_derived_cause')
    @patch('pivt.process.ProductRawEvent._get_upstream')
    @patch('pivt.process.ProductRawEvent._parse_unit_test_event')
    @patch('pivt.process.ProductRawEvent._get_iteration')
    @patch('pivt.process.ProductRawEvent._get_release')
    @patch('pivt.process.JenkinsRawEvent._get_parameters')
    def test_basic_build_no_upstream_build(self, mock_get_parameters, mock_get_release, mock_get_iteration, mock_parse_ut_event, mock_get_upstream, mock_get_derived_cause):
        mock_get_parameters.return_value = {}
        mock_get_release.return_value = None
        mock_get_iteration.return_value = None
        mock_get_upstream.return_value = 'ci2-Pipeline', None
        mock_get_derived_cause.return_value = 'Not Assigned'

        event = {'ci': 'ci2', 'stage': 'Build'}
        new_event = process.ProductRawEvent(event, 'Production').cook()

        self.assertEqual(new_event, {'ci': 'ci2', 'stage': 'Build', 'iteration': None, 'release': None, 'ss': 'ss5', 'instance': 'Production', 'cause': 'Not Assigned', 'derived_cause': 'Not Assigned'})
        self.assertFalse(mock_parse_ut_event.called)

    @patch('pivt.process.ProductRawEvent._get_derived_cause')
    @patch('pivt.process.ProductRawEvent._get_upstream')
    @patch('pivt.process.ProductRawEvent._parse_unit_test_event')
    @patch('pivt.process.ProductRawEvent._get_iteration')
    @patch('pivt.process.ProductRawEvent._get_release')
    @patch('pivt.process.JenkinsRawEvent._get_parameters')
    def test_basic_build(self, mock_get_parameters, mock_get_release, mock_get_iteration, mock_parse_ut_event, mock_get_upstream, mock_get_derived_cause):
        mock_get_parameters.return_value = {'p1': 'derp', 'p2': 'herp'}
        mock_get_release.return_value = '1.6.2.3'
        mock_get_iteration.return_value = '1.6'
        mock_get_upstream.return_value = 'ci2-Pipeline', 5
        mock_get_derived_cause.return_value = 'Not Assigned'

        event = {'ci': 'ci2', 'stage': 'Build'}
        new_event = process.ProductRawEvent(event, 'Production').cook()

        self.assertEqual(new_event, {'ci': 'ci2', 'stage': 'Build', 'iteration': '1.6', 'release': '1.6.2.3', 'ss': 'ss5', 'instance': 'Production', 'upstreamProject': 'ci2-Pipeline', 'upstreamBuild': 5, 'cause': 'Not Assigned', 'derived_cause': 'Not Assigned', 'p1': 'derp', 'p2': 'herp'})
        self.assertFalse(mock_parse_ut_event.called)

    @patch('pivt.process.ProductRawEvent._get_derived_cause')
    @patch('pivt.process.ProductRawEvent._get_upstream')
    @patch('pivt.process.ProductRawEvent._parse_unit_test_event')
    @patch('pivt.process.ProductRawEvent._get_iteration')
    @patch('pivt.process.ProductRawEvent._get_release')
    @patch('pivt.process.JenkinsRawEvent._get_parameters')
    def test_basic_build_ci_sub(self, mock_get_parameters, mock_get_release, mock_get_iteration, mock_parse_ut_event, mock_get_upstream, mock_get_derived_cause):
        mock_get_parameters.return_value = {}
        mock_get_release.return_value = None
        mock_get_iteration.return_value = None
        mock_get_upstream.return_value = None, None
        mock_get_derived_cause.return_value = 'Not Assigned'

        event = {'ci': 'ci3-sub', 'stage': 'Build'}
        new_event = process.ProductRawEvent(event, 'Production').cook()

        self.assertEqual(new_event, {'ci': 'ci3', 'stage': 'Build', 'iteration': None, 'release': None, 'ss': 'ss6', 'instance': 'Production', 'cause': 'Not Assigned', 'derived_cause': 'Not Assigned'})
        self.assertFalse(mock_parse_ut_event.called)

    @patch('pivt.process.ProductRawEvent._get_derived_cause')
    @patch('pivt.process.ProductRawEvent._get_upstream')
    @patch('pivt.process.ProductRawEvent._parse_unit_test_event')
    @patch('pivt.process.ProductRawEvent._get_iteration')
    @patch('pivt.process.ProductRawEvent._get_release')
    @patch('pivt.process.JenkinsRawEvent._get_parameters')
    def test_less_basic_build(self, mock_get_parameters, mock_get_release, mock_get_iteration, mock_parse_ut_event, mock_get_upstream, mock_get_derived_cause):
        mock_get_parameters.return_value = {}
        mock_get_release.return_value = None
        mock_get_iteration.return_value = None
        mock_get_upstream.return_value = None, None
        mock_get_derived_cause.return_value = 'Not Assigned'

        event = {'instance': 'Production', 'ss': 'ss5', 'ci': 'ci2', 'stage': 'Build'}
        new_event = process.ProductRawEvent(event, 'Production').cook()

        self.assertEqual(new_event, {'ci': 'ci2', 'stage': 'Build', 'iteration': None, 'release': None, 'ss': 'ss5', 'instance': 'Production', 'cause': 'Not Assigned', 'derived_cause': 'Not Assigned'})
        self.assertFalse(mock_parse_ut_event.called)

    @patch('pivt.process.ProductRawEvent._get_derived_cause')
    @patch('pivt.process.ProductRawEvent._get_upstream')
    @patch('pivt.process.ProductRawEvent._parse_unit_test_event')
    @patch('pivt.process.ProductRawEvent._get_iteration')
    @patch('pivt.process.ProductRawEvent._get_release')
    @patch('pivt.process.JenkinsRawEvent._get_parameters')
    def test_advanced_build(self, mock_get_parameters, mock_get_release, mock_get_iteration, mock_parse_ut_event, mock_get_upstream, mock_get_derived_cause):
        mock_get_parameters.return_value = {}
        mock_get_release.return_value = None
        mock_get_iteration.return_value = None
        mock_get_upstream.return_value = None, None
        mock_get_derived_cause.return_value = 'Not Assigned'

        event = {'instance': 'Development', 'ss': 'ss5', 'ci': 'ci2', 'stage': 'Build', 'duration': 10, 'result': 'FAILED', 'derp': 'herp'}
        new_event = process.ProductRawEvent(event, 'Production').cook()

        self.assertEqual(new_event, {'ci': 'ci2', 'stage': 'Build', 'iteration': None, 'release': None, 'ss': 'ss5', 'instance': 'Development', 'duration': 10, 'result': 'FAILED', 'cause': 'Not Assigned', 'derived_cause': 'Not Assigned'})
        self.assertFalse(mock_parse_ut_event.called)

    @patch('pivt.process.ProductRawEvent._get_derived_cause')
    @patch('pivt.process.ProductRawEvent._get_upstream')
    @patch('pivt.process.ProductRawEvent._parse_unit_test_event')
    @patch('pivt.process.ProductRawEvent._get_iteration')
    @patch('pivt.process.ProductRawEvent._get_release')
    @patch('pivt.process.JenkinsRawEvent._get_parameters')
    def test_basic_deploy(self, mock_get_parameters, mock_get_release, mock_get_iteration, mock_parse_ut_event, mock_get_upstream, mock_get_derived_cause):
        mock_get_parameters.return_value = {}
        mock_get_release.return_value = None
        mock_get_iteration.return_value = None
        mock_get_upstream.return_value = None, None
        mock_get_derived_cause.return_value = 'Not Assigned'

        event = {'ci': 'ci2', 'stage': 'Deploy'}
        new_event = process.ProductRawEvent(event, 'Production').cook()

        self.assertEqual(new_event, {'ci': 'ci2', 'stage': 'Deploy', 'iteration': None, 'release': None, 'ss': 'ss5', 'instance': 'Production', 'cause': 'Not Assigned', 'derived_cause': 'Not Assigned'})
        self.assertFalse(mock_parse_ut_event.called)

    @patch('pivt.process.ProductRawEvent._get_derived_cause')
    @patch('pivt.process.ProductRawEvent._get_upstream')
    @patch('pivt.process.ProductRawEvent._parse_unit_test_event')
    @patch('pivt.process.ProductRawEvent._get_iteration')
    @patch('pivt.process.ProductRawEvent._get_release')
    @patch('pivt.process.JenkinsRawEvent._get_parameters')
    def test_basic_ut(self, mock_get_parameters, mock_get_release, mock_get_iteration, mock_parse_ut_event, mock_get_upstream, mock_get_derived_cause):
        mock_get_parameters.return_value = {}
        mock_get_release.return_value = None
        mock_get_iteration.return_value = None
        mock_get_upstream.return_value = None, None
        mock_get_derived_cause.return_value = 'Not Assigned'

        event = {'ci': 'ci2', 'stage': 'UnitTest'}
        new_event = process.ProductRawEvent(event, 'Production').cook()

        self.assertEqual(new_event, {'ci': 'ci2', 'stage': 'UnitTest', 'iteration': None, 'release': None, 'ss': 'ss5', 'instance': 'Production', 'cause': 'Not Assigned', 'derived_cause': 'Not Assigned'})
        self.assertTrue(mock_parse_ut_event.called)

    @patch('pivt.process.ProductRawEvent._get_derived_cause')
    @patch('pivt.process.ProductRawEvent._get_upstream')
    @patch('pivt.process.ProductRawEvent._parse_unit_test_event')
    @patch('pivt.process.ProductRawEvent._get_iteration')
    @patch('pivt.process.ProductRawEvent._get_release')
    @patch('pivt.process.JenkinsRawEvent._get_parameters')
    def test_basic_ft_no_reports(self, mock_get_parameters, mock_get_release, mock_get_iteration, mock_parse_ut_event, mock_get_upstream, mock_get_derived_cause):
        mock_get_parameters.return_value = {}
        mock_get_release.return_value = None
        mock_get_iteration.return_value = None
        mock_get_upstream.return_value = None, None
        mock_get_derived_cause.return_value = 'Not Assigned'

        event = {'ci': 'ci2', 'stage': 'FunctionalTest'}
        new_event = process.ProductRawEvent(event, 'Production').cook()

        self.assertEqual(new_event, {'ci': 'ci2', 'stage': 'FunctionalTest', 'iteration': None, 'release': None, 'ss': 'ss5', 'instance': 'Production', 'cause': 'Not Assigned', 'derived_cause': 'Not Assigned'})
        self.assertFalse(mock_parse_ut_event.called)

    @patch('pivt.process.ProductRawEvent._get_derived_cause')
    @patch('pivt.process.ProductRawEvent._get_upstream')
    @patch('pivt.process.ProductRawEvent._parse_unit_test_event')
    @patch('pivt.process.ProductRawEvent._get_iteration')
    @patch('pivt.process.ProductRawEvent._get_release')
    @patch('pivt.process.JenkinsRawEvent._get_parameters')
    def test_basic_ft_with_reports(self, mock_get_parameters, mock_get_release, mock_get_iteration, mock_parse_ut_event, mock_get_upstream, mock_get_derived_cause):
        mock_get_parameters.return_value = {}
        mock_get_release.return_value = None
        mock_get_iteration.return_value = None
        mock_get_upstream.return_value = None, None
        mock_get_derived_cause.return_value = 'Not Assigned'

        event = {'ci': 'ci2', 'stage': 'FunctionalTest', 'reports': 'derp'}
        new_event = process.ProductRawEvent(event, 'Production').cook()

        self.assertEqual(new_event, {'ci': 'ci2', 'stage': 'FunctionalTest', 'iteration': None, 'release': None, 'ss': 'ss5', 'instance': 'Production', 'reports': 'derp', 'cause': 'Not Assigned', 'derived_cause': 'Not Assigned'})
        self.assertFalse(mock_parse_ut_event.called)

    @patch('pivt.process.ProductRawEvent._get_derived_cause')
    @patch('pivt.process.ProductRawEvent._get_upstream')
    @patch('pivt.process.ProductRawEvent._parse_unit_test_event')
    @patch('pivt.process.ProductRawEvent._get_iteration')
    @patch('pivt.process.ProductRawEvent._get_release')
    @patch('pivt.process.JenkinsRawEvent._get_parameters')
    def test_basic_build_with_cause(self, mock_get_parameters, mock_get_release, mock_get_iteration, mock_parse_ut_event, mock_get_upstream, mock_get_derived_cause):
        mock_get_parameters.return_value = {'p1': 'derp', 'p2': 'herp'}
        mock_get_release.return_value = '1.6.2.3'
        mock_get_iteration.return_value = '1.6'
        mock_get_upstream.return_value = 'ci2-Pipeline', 5
        mock_get_derived_cause.return_value = 'Weekly'

        event = {'ci': 'ci2', 'stage': 'Build', 'cause': 'Weekly-Builds'}
        new_event = process.ProductRawEvent(event, 'Production').cook()

        self.assertEqual(new_event,
                         {'ci': 'ci2', 'stage': 'Build', 'iteration': '1.6', 'release': '1.6.2.3', 'ss': 'ss5', 'instance': 'Production', 'upstreamProject': 'ci2-Pipeline',
                          'upstreamBuild': 5, 'p1': 'derp', 'p2': 'herp', 'cause': 'Weekly-Builds', 'derived_cause': 'Weekly'})
        self.assertFalse(mock_parse_ut_event.called)

    @patch('pivt.process.ProductRawEvent._get_derived_cause')
    @patch('pivt.process.ProductRawEvent._get_upstream')
    @patch('pivt.process.ProductRawEvent._parse_unit_test_event')
    @patch('pivt.process.ProductRawEvent._get_iteration')
    @patch('pivt.process.ProductRawEvent._get_release')
    @patch('pivt.process.JenkinsRawEvent._get_parameters')
    def test_aws_stage(self, mock_get_parameters, mock_get_release, mock_get_iteration, mock_parse_ut_event, mock_get_upstream, mock_get_derived_cause):
        mock_get_parameters.return_value = {}
        mock_get_release.return_value = None
        mock_get_iteration.return_value = None
        mock_get_upstream.return_value = None, None
        mock_get_derived_cause.return_value = 'Not Assigned'

        event = {'ci': 'ci2', 'stage': 'AWS', 'fullDisplayName': 'ci2-FuncTest #5'}
        new_event = process.ProductRawEvent(event, 'Production').cook()

        self.assertEqual(new_event, {'ci': 'ci2', 'stage': 'AWS_FunctionalTest', 'iteration': None, 'release': None, 'ss': 'ss5', 'instance': 'Production', 'cause': 'Not Assigned', 'derived_cause': 'Not Assigned', 'fullDisplayName': 'ci2-FuncTest #5'})
        self.assertFalse(mock_parse_ut_event.called)

class TestProductRawEventGetRelease(unittest.TestCase):
    def test_empty_event(self):
        event = {}
        self.assertEqual(process.ProductRawEvent._get_release(event), Constants.VERSION_NOT_ASSIGNED)

    def test_baseline_version(self):
        event = {'BASELINE_VERSION': '1.2.3.4'}
        self.assertEqual(process.ProductRawEvent._get_release(event), '1.2.3.4')

    def test_pipeline_version(self):
        event = {'PIPELINE_VERSION': '1.2.3.4.434'}
        self.assertEqual(process.ProductRawEvent._get_release(event), '1.2.3.4')

    def test_baseline_and_pipeline_version(self):
        event = {'BASELINE_VERSION': '5.6.7.8', 'PIPELINE_VERSION': '5.6.7.8.28'}
        self.assertEqual(process.ProductRawEvent._get_release(event), '5.6.7.8')

    def test_pipeline_version_wrong_format(self):
        event = {'PIPELINE_VERSION': '1.2.3.4.434.derp'}
        self.assertEqual(process.ProductRawEvent._get_release(event), Constants.VERSION_NOT_ASSIGNED)

class TestProductRawEventGetIteration(unittest.TestCase):
    def test_empty_event(self):
        event = {}
        self.assertEqual(process.ProductRawEvent._get_iteration(event), Constants.ITERATION_NOT_ASSIGNED)

    def test_baseline_version(self):
        event = {'release': '1.2.3.4'}
        self.assertEqual(process.ProductRawEvent._get_iteration(event), '1.2')

    def test_baseline_and_pipeline_version(self):
        event = {'release': '5.6.7.8'}
        self.assertEqual(process.ProductRawEvent._get_iteration(event), '5.6')

    def test_invalid_baseline_version(self):
        event = {'release': 'derp'}
        self.assertEqual(process.ProductRawEvent._get_iteration(event), Constants.ITERATION_NOT_ASSIGNED)

    def test_release_not_assigned(self):
        event = {'release': Constants.VERSION_NOT_ASSIGNED}
        self.assertEqual(process.ProductRawEvent._get_iteration(event), Constants.ITERATION_NOT_ASSIGNED)

class TestProductRawEventGetUpstream(unittest.TestCase):
    def test_no_actions(self):
        event = {
            'number': 5,
            'result': 'SUCCESS'
        }

        self.assertEqual(process.ProductRawEvent(event, None)._get_upstream(), (None, None))

    def test_no_cause_action(self):
        event = {
            'number': 5,
            'actions': [
                {
                    '_class': 'some weird action',
                    'derp': 'herp'
                },
                {
                    'kind': 'action with no class'
                },
                {
                    '_class': 'another action',
                }
            ],
            'result': 'SUCCESS'
        }

        self.assertEqual(process.ProductRawEvent(event, None)._get_upstream(), (None, None))

    def test_unknown_cause(self):
        event = {
            'number': 5,
            'actions': [
                {
                    '_class': 'some weird action',
                    'derp': 'herp'
                },
                {
                    'kind': 'action with no class'
                },
                {
                    '_class': 'hudson.model.CauseAction',
                    'causes': [
                        {
                            '_class': 'unknown cause class'
                        }
                    ]
                },
                {
                    '_class': 'another action',
                }
            ],
            'result': 'SUCCESS'
        }

        self.assertEqual(process.ProductRawEvent(event, None)._get_upstream(), (None, None))

    def test_user_cause(self):
        event = {
            'number': 5,
            'actions': [
                {
                    '_class': 'some weird action',
                    'derp': 'herp'
                },
                {
                    'kind': 'action with no class'
                },
                {
                    '_class': 'hudson.model.CauseAction',
                    'causes': [
                        {
                            '_class': 'hudson.model.Cause$UserIdCause'
                        }
                    ]
                },
                {
                    '_class': 'another action',
                }
            ],
            'result': 'SUCCESS'
        }

        self.assertEqual(process.ProductRawEvent(event, None)._get_upstream(), (None, None))

    def test_rebuild_user_cause(self):
        event = {
            'number': 5,
            'actions': [
                {
                    '_class': 'some weird action',
                    'derp': 'herp'
                },
                {
                    'kind': 'action with no class'
                },
                {
                    '_class': 'hudson.model.CauseAction',
                    'causes': [
                        {
                            '_class': 'hudson.model.Cause$RebuildCause'
                        },
                        {
                            '_class': 'hudson.model.Cause$UserIdCause',
                            'userName': 'Herpy Derp'
                        }
                    ]
                },
                {
                    '_class': 'another action',
                }
            ],
            'result': 'SUCCESS'
        }

        self.assertEqual(process.ProductRawEvent(event, None)._get_upstream(), (None, None))

    def test_self_service_cause(self):
        event = {
            'number': 5,
            'actions': [
                {
                    '_class': 'some weird action',
                    'derp': 'herp'
                },
                {
                    'kind': 'action with no class'
                },
                {
                    '_class': 'hudson.model.CauseAction',
                    'causes': [
                        {
                            '_class': 'hudson.model.Cause$UpstreamCause',
                            'upstreamProject': 'Self-Service-Pipeline',
                            'upstreamBuild': 55
                        }
                    ]
                },
                {
                    '_class': 'another action',
                }
            ],
            'result': 'SUCCESS'
        }

        self.assertEqual(process.ProductRawEvent(event, None)._get_upstream(), ('Self-Service-Pipeline', 55))

    def test_nightly_cause(self):
        event = {
            'number': 5,
            'actions': [
                {
                    '_class': 'some weird action',
                    'derp': 'herp'
                },
                {
                    'kind': 'action with no class'
                },
                {
                    '_class': 'hudson.model.CauseAction',
                    'causes': [
                        {
                            '_class': 'hudson.model.Cause$UpstreamCause',
                            'upstreamProject': 'Nightly-Builds',
                            'upstreamBuild': 34
                        }
                    ]
                },
                {
                    '_class': 'another action',
                }
            ],
            'result': 'SUCCESS'
        }

        self.assertEqual(process.ProductRawEvent(event, None)._get_upstream(), ('Nightly-Builds', 34))

    def test_weekly_cause(self):
        event = {
            'number': 5,
            'actions': [
                {
                    '_class': 'some weird action',
                    'derp': 'herp'
                },
                {
                    'kind': 'action with no class'
                },
                {
                    '_class': 'hudson.model.CauseAction',
                    'causes': [
                        {
                            '_class': 'hudson.model.Cause$UpstreamCause',
                            'upstreamProject': 'Weekly-Builds',
                            'upstreamBuild': 34
                        }
                    ]
                },
                {
                    '_class': 'another action',
                }
            ],
            'result': 'SUCCESS'
        }

        self.assertEqual(process.ProductRawEvent(event, None)._get_upstream(), ('Weekly-Builds', 34))

    def test_upstream_cause(self):
        event = {
            'number': 5,
            'actions': [
                {
                    '_class': 'some weird action',
                    'derp': 'herp'
                },
                {
                    'kind': 'action with no class'
                },
                {
                    '_class': 'hudson.model.CauseAction',
                    'causes': [
                        {
                            '_class': 'hudson.model.Cause$UpstreamCause',
                            'upstreamProject': 'ci2-Pipeline',
                            'upstreamBuild': 73
                        }
                    ]
                },
                {
                    '_class': 'another action',
                }
            ],
            'result': 'SUCCESS'
        }

        self.assertEqual(process.ProductRawEvent(event, None)._get_upstream(), ('ci2-Pipeline', 73))

class TestProductRawEventParseUnitTestEvent(unittest.TestCase):
    @patch('pivt.process.ProductRawEvent._get_ut_counts_with_action')
    @patch('pivt.process.ProductRawEvent._get_ut_counts_with_report')
    def test_no_report_no_actions(self, mock_get_ut_counts_with_report, mock_get_ut_counts_with_action):
        event = {'derp': 'herp'}
        new_event = {'herp': 'derp'}

        process.ProductRawEvent(event, None)._parse_unit_test_event(new_event)

        assert new_event == {'herp': 'derp'}
        assert not mock_get_ut_counts_with_report.called
        assert not mock_get_ut_counts_with_action.called

    @patch('pivt.process.ProductRawEvent._get_ut_counts_with_action')
    @patch('pivt.process.ProductRawEvent._get_ut_counts_with_report')
    def test_with_report_no_actions(self, mock_get_ut_counts_with_report, mock_get_ut_counts_with_action):
        event = {
            'derp': 'herp',
            'report': {
                'hi': 'hello'
            }
        }
        new_event = {'herp': 'derp'}

        process.ProductRawEvent(event, None)._parse_unit_test_event(new_event)

        assert new_event == {'herp': 'derp'}
        assert mock_get_ut_counts_with_report.called
        assert not mock_get_ut_counts_with_action.called

    @patch('pivt.process.ProductRawEvent._get_ut_counts_with_action')
    @patch('pivt.process.ProductRawEvent._get_ut_counts_with_report')
    def test_no_report_with_actions_no_total_count(self, mock_get_ut_counts_with_report, mock_get_ut_counts_with_action):
        def get_ut_counts_with_action(*args):
            my_event = args[1]
            my_event['me'] = 'gusta'
        mock_get_ut_counts_with_action.side_effect = get_ut_counts_with_action

        event = {
            'derp': 'herp',
            'actions': [
                {'hi': 'hello'},
                {'hello': 'hi'}
            ]
        }
        new_event = {'herp': 'derp'}

        process.ProductRawEvent(event, None)._parse_unit_test_event(new_event)

        assert new_event == {'herp': 'derp'}
        assert not mock_get_ut_counts_with_report.called
        assert not mock_get_ut_counts_with_action.called

    @patch('pivt.process.ProductRawEvent._get_ut_counts_with_action')
    @patch('pivt.process.ProductRawEvent._get_ut_counts_with_report')
    def test_no_report_with_actions(self, mock_get_ut_counts_with_report, mock_get_ut_counts_with_action):
        def get_ut_counts_with_action(*args):
            my_event = args[1]
            my_event['me'] = 'gusta'

        mock_get_ut_counts_with_action.side_effect = get_ut_counts_with_action

        event = {
            'derp': 'herp',
            'actions': [
                {'hi': 'hello'},
                {'hello': 'hi'},
                {'totalCount': 5}
            ]
        }
        new_event = {'herp': 'derp'}

        process.ProductRawEvent(event, None)._parse_unit_test_event(new_event)

        assert new_event == {'herp': 'derp', 'me': 'gusta'}
        assert not mock_get_ut_counts_with_report.called
        assert mock_get_ut_counts_with_action.called

class TestProductRawEventGetUtCountsWithReport(unittest.TestCase):
    def test_no_tests(self):
        report = {'failCount': 0, 'skipCount': 0, 'passCount': 0, 'derp': 'herp'}
        new_event = {'hi': 'hello', 'result': 'SUCCESS'}
        process.ProductRawEvent._get_ut_counts_with_report(report, new_event)
        self.assertEqual(new_event, {'hi': 'hello', 'result': 'SUCCESS'})

    def test_tests_aborted(self):
        report = {'failCount': 5, 'skipCount': 7, 'passCount': 8, 'derp': 'herp'}
        new_event = {'hi': 'hello', 'result': 'ABORTED'}
        process.ProductRawEvent._get_ut_counts_with_report(report, new_event)
        self.assertEqual(new_event, {'hi': 'hello', 'result': 'ABORTED'})

    def test_no_tests_aborted(self):
        report = {'failCount': 0, 'skipCount': 0, 'passCount': 0, 'derp': 'herp'}
        new_event = {'hi': 'hello', 'result': 'ABORTED'}
        process.ProductRawEvent._get_ut_counts_with_report(report, new_event)
        self.assertEqual(new_event, {'hi': 'hello', 'result': 'ABORTED'})

    def test_tests(self):
        report = {'failCount': 5, 'skipCount': 7, 'passCount': 8, 'derp': 'herp'}
        new_event = {'hi': 'hello', 'result': 'SUCCESS'}
        process.ProductRawEvent._get_ut_counts_with_report(report, new_event)
        self.assertEqual(new_event, {'hi': 'hello', 'result': 'SUCCESS', 'failCount': 5, 'skipCount': 7, 'passCount': 8, 'totalCount': 20})

class TestProductRawEventGetUtCountsWithAction(unittest.TestCase):
    def test(self):
        action = {'failCount': 5, 'skipCount': 7, 'totalCount': 20, 'derp': 'herp'}
        new_event = {'hi': 'hello'}
        process.ProductRawEvent._get_ut_counts_with_action(action, new_event)
        self.assertEqual(new_event, {'hi': 'hello', 'failCount': 5, 'skipCount': 7, 'passCount': 8, 'totalCount': 20})

class TestProductRawEventGetDerivedCause(unittest.TestCase):
    def test_self_service(self):
        cause = 'Self-Service-Pipeline'
        expected = 'Self-Service'
        self.assertEqual(expected, process.ProductRawEvent._get_derived_cause(cause))

    def test_nightly_2nd_wave(self):
        cause = 'Nightly-Builds-2nd-wave'
        expected = 'Nightly-2nd-Wave'
        self.assertEqual(expected, process.ProductRawEvent._get_derived_cause(cause))

    def test_nightly(self):
        cause = 'Nightly-Builds'
        expected = 'Nightly'
        self.assertEqual(expected, process.ProductRawEvent._get_derived_cause(cause))

    def test_weekly(self):
        cause = 'Weekly-Builds'
        expected = 'Weekly'
        self.assertEqual(expected, process.ProductRawEvent._get_derived_cause(cause))

    def test_user(self):
        cause = 'user'
        expected = 'User'
        self.assertEqual(expected, process.ProductRawEvent._get_derived_cause(cause))

    def test_something_else(self):
        cause = 'something_else'
        expected = 'something_else'
        self.assertEqual(expected, process.ProductRawEvent._get_derived_cause(cause))

class TestProductRawEventIsBuilding(unittest.TestCase):
    def test_building(self):
        event = {'id': 5, 'building': True}
        self.assertTrue(process.ProductRawEvent(event, None).is_building())

    def test_not_building(self):
        event = {'id': 5, 'building': False}
        self.assertFalse(process.ProductRawEvent(event, None).is_building())

    def test_no_building(self):
        event = {'id': 5}
        self.assertFalse(process.ProductRawEvent(event, None).is_building())

    def test_something_else(self):
        event = {'id': 5, 'building': 'something_else'}
        self.assertFalse(process.ProductRawEvent(event, None).is_building())


"""
ProductCookedEvent
"""
class TestProductCookedEventGetKey(unittest.TestCase):
    def test(self):
        event = {'ci': 'DERP', 'stage': 'Build', 'number': 666, 'timestamp': 123456789, 'other1': 'herpy', 'other2': 'derpy'}
        self.assertEqual(process.ProductCookedEvent(event).get_key(), 'DERP:Build:666:123456789', 'Should return DERP:Build:666:123456789')


"""
InsRawEvent
"""
class TestInsRawEventCook(unittest.TestCase):
    def test_no_instance(self):
        raw_event = {'id': 1, 'derp': 'herp'}

        expected_cooked_event = process.InsCookedEvent({'id': 1, 'derp': 'herp', 'branch': 'develop'})

        cooked_event = process.InsRawEvent(raw_event).cook()

        self.assertEqual(expected_cooked_event, cooked_event)

    def test_with_instance_dev(self):
        raw_event = {'id': 1, 'derp': 'herp', 'branch': 'develop'}

        expected_cooked_event = process.InsCookedEvent({'id': 1, 'derp': 'herp', 'branch': 'develop'})

        cooked_event = process.InsRawEvent(raw_event).cook()

        self.assertEqual(expected_cooked_event, cooked_event)

    def test_with_instance_prod(self):
        raw_event = {'id': 1, 'derp': 'herp', 'branch': 'production'}

        expected_cooked_event = process.InsCookedEvent({'id': 1, 'derp': 'herp', 'branch': 'production'})

        cooked_event = process.InsRawEvent(raw_event).cook()

        self.assertEqual(expected_cooked_event, cooked_event)

    def test_with_stage_flow_nodes(self):
        raw_event = {
            'id': 1,
            'derp': 'herp',
            'branch': 'production',
            'stages': [
                {
                    'name': 'stage1'
                },
                {
                    'name': 'stage2',
                    'stageFlowNodes': ['derp', 'herp']
                }
            ]
        }

        expected_cooked_event = process.InsCookedEvent({
            'id': 1,
            'derp': 'herp',
            'branch': 'production',
            'stages': [
                {
                    'name': 'stage1'
                },
                {
                    'name': 'stage2'
                }
            ]
        })

        cooked_event = process.InsRawEvent(raw_event).cook()

        self.assertEqual(expected_cooked_event, cooked_event)


"""
InsCookedEvent
"""
class TestInsCookedEventGetKey(unittest.TestCase):
    def test(self):
        event = {'pipeline': 'Core1', 'branch': 'master', 'id': 666, 'timestamp': 123456789, 'other1': 'herpy', 'other2': 'derpy'}
        self.assertEqual(process.InsCookedEvent(event).get_key(), 'Core1:master:666:123456789')


"""
VicRawEvent
"""
class TestVicRawEventCook(unittest.TestCase):
    pass

class TestVicRawEventIsBuilding(unittest.TestCase):
    pass


"""
VicCookedEvent
"""
class TestVicCookedEventGetKey(unittest.TestCase):
    def test(self):
        event = {'id': 666, 'timestamp': 123456789, 'other1': 'herpy', 'other2': 'derpy'}
        self.assertEqual(process.VicCookedEvent(event).get_key(), '666:123456789')


"""
VicStatusRawEvent
"""
class TestVicStatusRawEventCook(unittest.TestCase):
    def test(self):
        raw_event = [
            {'id': 1, 'ci_allocation': 'derp (1 of 2)'},
            {'id': 2, 'ci_allocation': 'derp (2 of 2)', 'timestamp': 'derp'}
        ]

        timestamp = 123

        expected_cooked_events = [
            {'id': 1, 'ci_allocation': 'derp (1 of 2)', 'timestamp': 123},
            {'id': 2, 'ci_allocation': 'derp (2 of 2)', 'timestamp': 'derp'}
        ]

        cooked_events = process.VicStatusRawEvent(raw_event).cook(timestamp=timestamp)

        self.assertEqual(expected_cooked_events, cooked_events)


"""
VicStatusCookedEvent
"""
class TestVicStatusCookedEventGetKey(unittest.TestCase):
    def test(self):
        event = {'id': 666, 'timestamp': 123456789, 'ci_allocation': 'derpy (0 of 12)', 'other1': 'herpy', 'other2': 'derpy'}
        self.assertEqual('123456789:derpy (0 of 12)', process.VicStatusCookedEvent(event).get_key())


"""
CqCookedEvent
"""
class TestCqCookedEventGetKey(unittest.TestCase):
    def test_add(self):
        event = {'type': 'add', 'dr_id': 1, 'timestamp': 2}
        self.assertEqual('add:1:2', process.CqCookedEvent(event).get_key())

    def test_other(self):
        event = {'type': 'derp', 'dr_id': 1, 'timestamp': 2, 'change_field': 'greeting', 'before': 'hi', 'after': 'hello', 'derp': 'herp'}
        self.assertEqual('derp:1:2', process.CqCookedEvent(event).get_key())

    def test_modify(self):
        event = {'type': 'modify', 'dr_id': 1, 'timestamp': 2, 'change_field': 'greeting', 'before': 'hi', 'after': 'hello'}
        self.assertEqual('modify:1:2:greeting:hi:hello', process.CqCookedEvent(event).get_key())
