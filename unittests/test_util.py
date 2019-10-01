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

from pivt.util import util
import unittest
from unittest.mock import patch
from unittest.mock import MagicMock
import os
import re
import tempfile
from pathlib import Path
from pivt.conf_manager import ConfManager


if __name__ == '__main__':
    unittest.main()


orig_conf_load = ConfManager.load


def setUpModule():
    os.environ['PIVT_HOME'] = tempfile.mkdtemp().replace('\\', '/')

    ConfManager.load = MagicMock()


def tearDownModule():
    util.teardown()
    util.rmtree(os.environ['PIVT_HOME'], no_exist_ok=True)
    if 'PIVT_HOME' in os.environ:
        del os.environ['PIVT_HOME']

    ConfManager.load = orig_conf_load


# TODO: TestSetupEnv
# TODO: modify TestGetLogger to test file_handler arg
# TODO: TestGetLoggerFileHandler


class TestSetup(unittest.TestCase):
    def setUp(self):
        util.teardown()

    def tearDown(self):
        util.teardown()
        util.rmtree(util.var_dir, no_exist_ok=True)

    def test_no_pivt_home(self):
        pivt_home = os.environ['PIVT_HOME']
        del os.environ['PIVT_HOME']

        with self.assertRaises(SystemExit):
            util.setup()

        os.environ['PIVT_HOME'] = pivt_home

    def test_pivt_home_no_exists(self):
        pivt_home = os.environ['PIVT_HOME']
        os.environ['PIVT_HOME'] = 'does/not/exist'

        with self.assertRaises(SystemExit):
            util.setup()

        os.environ['PIVT_HOME'] = pivt_home

    def test(self):
        pivt_home = Path(os.environ['PIVT_HOME'])

        self.assertFalse(util.initialized)
        self.assertFalse((pivt_home / 'var/log').exists())

        util.setup()

        assert util.pivt_home ==                pivt_home

        assert util.etc_dir ==                  pivt_home / 'etc'
        assert util.var_dir ==                  pivt_home / 'var'

        assert util.version_file ==             pivt_home / 'etc/pivt.version'
        assert util.sources_file ==             pivt_home / 'etc/product.sources'
        assert util.sources_file_ins ==         pivt_home / 'etc/ins.sources'
        assert util.sources_file_vic ==         pivt_home / 'etc/vic.sources'
        assert util.metadata_file ==            pivt_home / 'etc/job_pull_times.ini'
        assert util.unpulled_builds_file ==     pivt_home / 'etc/unpulled.json'

        assert util.log_dir ==                  pivt_home / 'var/log'

        assert util.data_dir ==                 pivt_home / 'var/data'
        assert util.archive_dir ==              pivt_home / 'var/data/archive'
        assert util.collected_dir ==            pivt_home / 'var/data/collected'
        assert util.db_dir ==                   pivt_home / 'var/data/data'
        assert util.new_data_dir ==             pivt_home / 'var/data/newdata'

        assert util.jenkins_data_dir ==         pivt_home / 'var/data/data/jenkins'
        assert util.jenkins_ft_data_dir ==      pivt_home / 'var/data/data/jenkins/ft'

        assert util.ins_data_dir ==             pivt_home / 'var/data/data/ins'

        assert util.cq_data_dir ==              pivt_home / 'var/data/data/cq'
        assert util.cq_data_path_old ==         pivt_home / 'var/data/data/cq/CQ_Data.csv'
        assert util.cq_changed_files_path ==    pivt_home / 'var/data/data/cq/CQ_Changed_Files.csv'

        assert util.cq_data_path ==             pivt_home / 'var/data/data/cq/drs.csv'
        assert util.cq_events_path ==           pivt_home / 'var/data/data/cq/events.json'

        self.assertTrue(util.log_dir.exists())
        self.assertEqual(['pivt.log'], util.listdir(util.log_dir))

        self.assertTrue(util.initialized)


class TestSetupCiToSs(unittest.TestCase):
    def test(self):
        util.setup_ci_to_ss()

        self.assertEqual({
            '%%ci16%%': '%%ci31%%',
            '%%ci17%%': '%%ci31%%',
            '%%ci21%%': '%%ci21%%',
            '%%ci18%%': '%%ci32%%',
            '%%ci19%%': '%%ci32%%',
            '%%ci15%%': '%%ci32%%',
            '%%ci20%%': '%%ci32%%',
            '%%ci12%%': '%%ci32%%',
            '%%ci22%%': '%%ci22%%',
            '%%ci23%%': '%%ci22%%',
            '%%ci24%%': '%%ci22%%',
            '%%ci25%%': '%%ci22%%',
            '%%ci9%%': '%%ci22%%',
            '%%ci7%%': '%%ci22%%',
            '%%ci8%%': '%%ci22%%',
            '%%ci10%%': '%%ci22%%',
            '%%ci26%%': '%%ci33%%',
            '%%ci27%%': '%%ci34%%',
            '%%ci28%%': '%%ci35%%',
            '%%ci11%%': '%%ci35%%',
            '%%ci29%%': '%%ci35%%',
            '%%ci13%%': '%%ci36%%',
            '%%ci14%%': '%%ci36%%',
            '%%ci30%%': '%%ci36%%'
        }, util.ci_to_ss)

        util.teardown()


class TestGenJenkinsEventKey(unittest.TestCase):
    def test_default_timestamp(self):
        event = {'ci': 'DERP', 'stage': 'Build', 'number': 666, 'timestamp': 123456789, 'other1': 'herpy', 'other2': 'derpy'}
        assert util.gen_jenkins_event_key(event) == 'DERP:Build:666:123456789'

    def test_alternate_time_field(self):
        event = {'ci': 'DERP', 'stage': 'Build', 'number': 666, 'time': 123456789, 'other1': 'herpy', 'other2': 'derpy'}
        assert util.gen_jenkins_event_key(event, time_field='time') == 'DERP:Build:666:123456789'

    def test_wrong_time_field(self):
        event = {'ci': 'DERP', 'stage': 'Build', 'number': 666, 'time': 123456789, 'other1': 'herpy', 'other2': 'derpy'}
        with self.assertRaises(KeyError):
            util.gen_jenkins_event_key(event)


class TestGenInsEventKey(unittest.TestCase):
    def test(self):
        event = {'core': 'Core1', 'id': 666, 'timestamp': 123456789, 'other1': 'herpy', 'other2': 'derpy'}
        assert util.gen_ins_event_key(event) == 'Core1:666:123456789'

    def test_alternate_time_field(self):
        event = {'core': 'Core1', 'id': 666, 'time': 123456789, 'other1': 'herpy', 'other2': 'derpy'}
        assert util.gen_ins_event_key(event, time_field='time') == 'Core1:666:123456789'

    def test_wrong_time_field(self):
        event = {'core': 'Core1', 'id': 666, 'time': 123456789, 'other1': 'herpy', 'other2': 'derpy'}
        with self.assertRaises(KeyError):
            util.gen_ins_event_key(event)


class TestGetProjectName(unittest.TestCase):
    def test_no_display_name_no_url(self):
        event = {'derp': 'herp'}
        project_name = util.get_project_name(event)
        assert not project_name

    def test_display_name(self):
        event = {'derp': 'herp', 'fullDisplayName': 'hi 2'}
        project_name = util.get_project_name(event)
        assert project_name == 'hi'

    def test_just_url(self):
        event = {'derp': 'herp', 'url': 'this/is/my/cool/url'}
        project_name = util.get_project_name(event)
        assert project_name == 'my'

    def test_both(self):
        event = {'derp': 'herp', 'url': 'this/is/my/cool/url', 'fullDisplayName': 'hi 2'}
        project_name = util.get_project_name(event)
        assert project_name == 'hi'


class TestUpdateDashboards(unittest.TestCase):
    def test(self):
        pass


class TestGetDashboardsPath(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        util.teardown()

    def test_no_exist(self):
        with self.assertRaises(FileNotFoundError):
            util._get_dashboards_path('', None)

    def test_pivt_default(self):
        with tempfile.TemporaryDirectory() as splunk_path:
            os.makedirs(splunk_path + '/etc/apps/pivt/default/data/ui/views/')
            assert util._get_dashboards_path(splunk_path, None) == splunk_path + '/etc/apps/pivt/default/data/ui/views/'

    def test_pivt_local(self):
        with tempfile.TemporaryDirectory() as splunk_path:
            os.makedirs(splunk_path + '/etc/apps/pivt/local/data/ui/views/')
            assert util._get_dashboards_path(splunk_path, None) == splunk_path + '/etc/apps/pivt/local/data/ui/views/'

    def test_both(self):
        with tempfile.TemporaryDirectory() as splunk_path:
            os.makedirs(splunk_path + '/etc/apps/pivt/default/data/ui/views/')
            os.makedirs(splunk_path + '/etc/apps/pivt/local/data/ui/views/')
            assert util._get_dashboards_path(splunk_path, None) == splunk_path + '/etc/apps/pivt/default/data/ui/views/'


class TestUpdateLastPullDate(unittest.TestCase):
    @classmethod
    def tearDownClass(cls):
        util.teardown()

    def test_no_file(self):
        util._update_last_pull_date('derp', 'path/to/dashboard', None, None)

    def test_trailing_backslash_in_dashboards_path(self):
        if not os.path.exists('dashboards'):
            os.makedirs('dashboards')

        with open('dashboards/derp.xml', 'w') as file:
            file.write('<dashboard>\n')
            file.write('\t<description>old_desc</description>\n')
            file.write('\t<something>else</something>\n')
            file.write('</dashboard>\n')

        util._update_last_pull_date('derp.xml', 'dashboards/', '<description>new_desc</description>\n', None)

        expected = '<dashboard>\n\t<description>new_desc</description>\n\t<something>else</something>\n</dashboard>\n'

        with open('dashboards/derp.xml', 'r') as file:
            assert file.read() == expected

        util.rmtree('dashboards')

    def test_no_trailing_backslash_in_dashboards_path(self):
        if not os.path.exists('dashboards'):
            os.makedirs('dashboards')

        with open('dashboards/derp.xml', 'w') as file:
            file.write('<dashboard>\n')
            file.write('\t<description>old_desc</description>\n')
            file.write('\t<something>else</something>\n')
            file.write('</dashboard>\n')

        util._update_last_pull_date('derp.xml', 'dashboards', '<description>new_desc</description>\n', None)

        expected = '<dashboard>\n\t<description>new_desc</description>\n\t<something>else</something>\n</dashboard>\n'

        with open('dashboards/derp.xml', 'r') as file:
            assert file.read() == expected

        util.rmtree('dashboards')


class TestGetNewDashboardDescription(unittest.TestCase):
    def setUp(self):
        util.setup()
        util.etc_dir.mkdir(parents=True)
        self.version = '2.3.1'
        self.pull_date = '04/9/16 @ 7:07:00 Pacific Daylight Time'
        with util.version_file.open('w') as file:
            file.write('CURRENT=' + self.version + '\n')

    def tearDown(self):
        util.rmtree(util.etc_dir)
        util.teardown()

    def test_get_new_date_false(self):
        expected = '<description>PIVT Version: {0} --- Last pull date: {1}</description>\n'.format(self.version, self.pull_date)

        with patch.object(ConfManager, 'get', return_value=self.pull_date):
            actual = util._get_new_dashboard_description(get_new_date=False)

        self.assertEqual(actual, expected)

    @patch('pivt.util.util.get_normalized_now_date_time')
    def test_get_new_date_true(self, mock_normalized_date_time):
        mock_normalized_date_time.return_value = '10/31/18 @ 7:07:00'
        expected = '<description>PIVT Version: {0} --- Last pull date: 10/31/18 @ 7:07:00</description>\n'.format(self.version)

        with patch.object(ConfManager, 'set'):
            actual = util._get_new_dashboard_description(get_new_date=True)

        self.assertEqual(actual, expected)


class TestGetNormalizedNowDateTime(unittest.TestCase):
    def test(self):
        import datetime
        date_time = datetime.datetime(2018, 5, 11, hour=21, minute=32, second=0, tzinfo=datetime.timezone.utc).astimezone()

        expected1 = '05/11/18 @ 14:32:00 Pacific Daylight Time'
        expected2 = '05/11/18 @ 14:32:00 PDT'
        actual = util.get_normalized_now_date_time(date_time)

        assert (actual == expected1 or actual == expected2)


class TestReadKvFile(unittest.TestCase):
    def setUp(self):
        util.setup()
        util.etc_dir.mkdir(parents=True)
        self.version = '2.3.1'
        self.prev_version = '2.3.0'
        with util.version_file.open('w') as file:
            file.write('CURRENT=' + self.version + '\n')
            file.write('PREVIOUS=' + self.prev_version + '\n')

    def tearDown(self):
        util.rmtree(util.etc_dir)
        util.teardown()

    def test_parse_version(self):
        version = util.read_value_from_kv_file(util.version_file, 'CURRENT')
        self.assertEqual(version, self.version)

    def test_parse_prev_version(self):
        version = util.read_value_from_kv_file(util.version_file, 'PREVIOUS')
        self.assertEqual(version, self.prev_version)

    def test_parse_missing_data(self):
        missing = util.read_value_from_kv_file(util.version_file, 'CATS')
        self.assertEqual(missing, None)


class TestUpdateKvFile(unittest.TestCase):
    def setUp(self):
        util.setup()
        util.etc_dir.mkdir(parents=True)
        util.version_file.open('w').close()

    def tearDown(self):
        util.rmtree(util.etc_dir)
        util.teardown()

    def test_no_file(self):
        util.version_file.unlink()
        util.update_value_in_kv_file(util.version_file, None, None)

    def test_new_time(self):
        with util.version_file.open('w') as file:
            file.write('derp=herp\n')
            file.write('LAST_PULL_DATE=old_time\n')

        util.update_value_in_kv_file(util.version_file, 'LAST_PULL_DATE', 'new_time')

        with util.version_file.open() as file:
            match = re.search(r'LAST_PULL_DATE=(.*)\n', file.read())
            assert match.group(1) == 'new_time'


class TestGetBasename(unittest.TestCase):
    def test_str(self):
        self.assertEqual('hi.txt', util.basename('/path/omg/hi.txt'))

    def test_path(self):
        self.assertEqual('hi.txt', util.basename(Path('/path/omg/hi.txt')))


class TestInnerStringify(unittest.TestCase):
    def test_number(self):
        value = 5
        expected = '5'

        self.assertEqual(expected, util.inner_stringify(value))

    def test_str(self):
        value = 'hi'
        expected = 'hi'

        self.assertEqual(expected, util.inner_stringify(value))

    def test_simple_list(self):
        value = [1, 6.5, 'derp']
        expected = ['1', '6.5', 'derp']

        self.assertEqual(expected, util.inner_stringify(value))

    def test_simple_dict(self):
        value = {
            5: 7.5,
            'id': 1,
            'derp': 'herp'
        }
        expected = {
            '5': '7.5',
            'id': '1',
            'derp': 'herp'
        }

        self.assertEqual(expected, util.inner_stringify(value))

    def test_complex_list(self):
        value = [
            1,
            6.5,
            'derp',
            [3, 4, 5],
            {
                1: 'wow',
                'neat': 2
            }
        ]

        expected = [
            '1',
            '6.5',
            'derp',
            ['3', '4', '5'],
            {
                '1': 'wow',
                'neat': '2'
            }
        ]

        self.assertEqual(expected, util.inner_stringify(value))

    def test_complex_dict(self):
        value = {
            5: 7.5,
            'id': 1,
            'derp': 'herp',
            'list': [1, 2.3, 'hi'],
            'dict': {
                0: 'cool',
                'omg': 5
            }
        }

        expected = {
            '5': '7.5',
            'id': '1',
            'derp': 'herp',
            'list': ['1', '2.3', 'hi'],
            'dict': {
                '0': 'cool',
                'omg': '5'
            }
        }

        self.assertEqual(expected, util.inner_stringify(value))
