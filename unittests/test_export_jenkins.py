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

from pivt import export_jenkins as export
import unittest
from unittest.mock import patch
from unittest.mock import call
from unittest.mock import MagicMock
import json
import configparser
import os
import tempfile
from collections import OrderedDict
from copy import deepcopy
import yaml
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


class TestMain(unittest.TestCase):
    def setUp(self):
        self.exporter = export.JenkinsExporter()

        util.rmtree(util.data_dir, no_exist_ok=True)

        if util.unpulled_builds_file.exists():
            util.unpulled_builds_file.unlink()

        if util.metadata_file.exists():
            util.metadata_file.unlink()

    def tearDown(self):
        util.rmtree(util.data_dir, no_exist_ok=True)
        util.rmtree(util.etc_dir, no_exist_ok=True)

        if util.unpulled_builds_file.exists():
            util.unpulled_builds_file.unlink()

        if util.metadata_file.exists():
            util.metadata_file.unlink()

    @patch('pivt.export_jenkins.JenkinsExporter.load_all_cores_commits')
    @patch('pivt.export_jenkins.JenkinsExporter.pull')
    @patch('pivt.export_jenkins.JenkinsExporter.load_config')
    @patch('pivt.export_jenkins.JenkinsExporter.load_ins_sources')
    @patch('pivt.export_jenkins.JenkinsExporter.load_sources')
    @patch('pivt.export_jenkins.urlopen')
    def test_no_jenkins_dir(self, mock_urlopen, mock_load_sources, mock_load_ins_sources, mock_load_config, mock_pull, mock_load_commits):
        mock_urlopen.return_value = None
        mock_load_sources.return_value = [], [], [], []
        mock_load_ins_sources.return_value = []
        mock_load_config.return_value = configparser.ConfigParser({'lastJobPulledTime': '0'})
        mock_pull.return_value = None

        util.rmtree(self.exporter.jenkins_dir, no_exist_ok=True)
        self.exporter.ins_dir.mkdir(parents=True, exist_ok=True)

        self.exporter.main()

        assert self.exporter.jenkins_dir.exists()
        assert self.exporter.ins_dir.exists()

    @patch('pivt.export_jenkins.JenkinsExporter.load_all_cores_commits')
    @patch('pivt.export_jenkins.JenkinsExporter.pull')
    @patch('pivt.export_jenkins.JenkinsExporter.load_config')
    @patch('pivt.export_jenkins.JenkinsExporter.load_ins_sources')
    @patch('pivt.export_jenkins.JenkinsExporter.load_sources')
    @patch('pivt.export_jenkins.urlopen')
    def test_existing_jenkins_dir(self, mock_urlopen, mock_load_sources, mock_load_ins_sources, mock_load_config, mock_pull, mock_load_commits):
        mock_urlopen.return_value = None
        mock_load_sources.return_value = [], [], [], []
        mock_load_ins_sources.return_value = []
        mock_load_config.return_value = configparser.ConfigParser({'lastJobPulledTime': '0'})
        mock_pull.return_value = None

        self.exporter.jenkins_dir.mkdir(parents=True)

        self.exporter.main()

        assert self.exporter.jenkins_dir.exists()

    @patch('pivt.export_jenkins.JenkinsExporter.load_all_cores_commits')
    @patch('pivt.export_jenkins.JenkinsExporter.pull')
    @patch('pivt.export_jenkins.JenkinsExporter.load_config')
    @patch('pivt.export_jenkins.JenkinsExporter.load_ins_sources')
    @patch('pivt.export_jenkins.JenkinsExporter.load_sources')
    @patch('pivt.export_jenkins.urlopen')
    def test_existing_unpulled_builds_file(self, mock_urlopen, mock_load_sources, mock_load_ins_sources, mock_load_config, mock_pull, mock_load_commits):
        mock_urlopen.return_value = None
        mock_load_sources.return_value = [], [], [], []
        mock_load_ins_sources.return_value = []
        mock_load_config.return_value = configparser.ConfigParser({'lastJobPulledTime': '0'})
        mock_pull.return_value = None

        util.etc_dir.mkdir(parents=True)
        with util.unpulled_builds_file.open('w') as file:
            file.write(json.dumps({'derp': 'herp'}))

        self.exporter.main()

        assert self.exporter.unpulled_builds_last == {'derp': 'herp'}

    @patch('pivt.export_jenkins.JenkinsExporter.load_all_cores_commits')
    @patch('pivt.export_jenkins.JenkinsExporter.pull')
    @patch('pivt.export_jenkins.JenkinsExporter.load_config')
    @patch('pivt.export_jenkins.JenkinsExporter.load_ins_sources')
    @patch('pivt.export_jenkins.JenkinsExporter.load_sources')
    @patch('pivt.export_jenkins.urlopen')
    def test_no_unpulled_builds_file(self, mock_urlopen, mock_load_sources, mock_load_ins_sources, mock_load_config, mock_pull, mock_load_commits):
        mock_urlopen.return_value = None
        mock_load_sources.return_value = [], [], [], []
        mock_load_ins_sources.return_value = []
        mock_load_config.return_value = configparser.ConfigParser({'lastJobPulledTime': '0'})
        mock_pull.return_value = None

        self.exporter.main()

        assert self.exporter.unpulled_builds_last == {}

    @patch('pivt.export_jenkins.JenkinsExporter.load_all_cores_commits')
    @patch('pivt.export_jenkins.JenkinsExporter.pull')
    @patch('pivt.export_jenkins.JenkinsExporter.load_config')
    @patch('pivt.export_jenkins.JenkinsExporter.load_ins_sources')
    @patch('pivt.export_jenkins.JenkinsExporter.load_sources')
    @patch('pivt.export_jenkins.urlopen')
    def test_new_unpulled_builds(self, mock_urlopen, mock_load_sources, mock_load_ins_sources, mock_load_config, mock_pull, mock_load_commits):
        mock_urlopen.return_value = None
        mock_load_sources.return_value = [], [], [], []
        mock_load_ins_sources.return_value = []
        mock_load_config.return_value = configparser.ConfigParser({'lastJobPulledTime': '0'})
        mock_pull.return_value = None

        self.exporter.unpulled_builds = {'derp': 'herp'}
        self.exporter.main()

        with util.unpulled_builds_file.open() as file:
            assert json.loads(file.read()) == {'derp': 'herp'}

    @patch('pivt.export_jenkins.JenkinsExporter.load_all_cores_commits')
    @patch('pivt.export_jenkins.JenkinsExporter.pull')
    @patch('pivt.export_jenkins.JenkinsExporter.load_config')
    @patch('pivt.export_jenkins.JenkinsExporter.load_ins_sources')
    @patch('pivt.export_jenkins.JenkinsExporter.load_sources')
    @patch('pivt.export_jenkins.urlopen')
    def test_config(self, mock_urlopen, mock_load_sources, mock_load_ins_sources, mock_load_config, mock_pull, mock_load_commits):
        mock_urlopen.return_value = None
        mock_load_sources.return_value = [], [], [], []
        mock_load_ins_sources.return_value = []
        mock_load_config.return_value = configparser.ConfigParser({'lastJobPulledTime': '0'})
        mock_pull.return_value = None

        self.exporter.main()

        with util.metadata_file.open() as file:
            assert file.read().strip() == '[DEFAULT]\nlastjobpulledtime = 0'


class TestLoadSources(unittest.TestCase):
    def setUp(self):
        self.exporter = export.JenkinsExporter()
        util.etc_dir.mkdir(parents=True)

    def tearDown(self):
        util.rmtree(util.etc_dir)

    def test(self):
        with util.sources_file.open('w') as file:
            file.write('ci          stage               job_name                            instance    tags\n')
            file.write('ci1         Build               ci1-Build\n')
            file.write('ci1         UnitTest            ci1-UnitTest                        Production\n')
            file.write('ci2         Build               ci4-build                           Production\n')
            file.write('ci2         Build               ci4-Build                           Development\n')
            file.write('ci2         UnitTest            ci4-unittest                        Development derp,herp\n')
            file.write('ci3         AWS_Deploy          ci3-Deploy                          Production\n')
            file.write('ci3         AWS_Deploy          ci3-Deploy-P-Release                            p-release\n')
            file.write('ci3         AWS_FunctionalTest  ci3-FuncTest                        Production\n')

        with util.sources_file_vic.open('w') as file:
            file.write('job_name\n')
            file.write('job1\n')
            file.write('job2\n')

        prod_sources, dev_sources, vic_prod_sources, vic_dev_sources = self.exporter.load_sources()

        expected_prod_sources = [
            {'job_name': 'ci1-Build', 'ci': 'ci1', 'stage': 'Build', 'instance': 'Production', 'tags': None},
            {'job_name': 'ci1-UnitTest', 'ci': 'ci1', 'stage': 'UnitTest', 'instance': 'Production', 'tags': None},
            {'job_name': 'ci4-build', 'ci': 'ci2', 'stage': 'Build', 'instance': 'Production', 'tags': None},
            {'job_name': 'ci3-Deploy', 'ci': 'ci3', 'stage': 'AWS_Deploy', 'instance': 'Production', 'tags': None},
            {'job_name': 'ci3-Deploy-P-Release', 'ci': 'ci3', 'stage': 'AWS_Deploy', 'instance': 'Production', 'tags': 'p-release'},
            {'job_name': 'ci3-FuncTest', 'ci': 'ci3', 'stage': 'AWS_FunctionalTest', 'instance': 'Production', 'tags': None}
        ]

        expected_dev_sources = [
            {'job_name': 'ci1-Build', 'ci': 'ci1', 'stage': 'Build', 'instance': 'Development', 'tags': None},
            {'job_name': 'ci4-Build', 'ci': 'ci2', 'stage': 'Build', 'instance': 'Development', 'tags': None},
            {'job_name': 'ci4-unittest', 'ci': 'ci2', 'stage': 'UnitTest', 'instance': 'Development', 'tags': 'derp,herp'},
            {'job_name': 'ci3-Deploy-P-Release', 'ci': 'ci3', 'stage': 'AWS_Deploy', 'instance': 'Development', 'tags': 'p-release'}
        ]

        expected_vic_prod_sources = [
            {'job_name': 'job1', 'instance': 'Production'},
            {'job_name': 'job2', 'instance': 'Production'}
        ]

        expected_vic_dev_sources = [
            {'job_name': 'job1', 'instance': 'Development'},
            {'job_name': 'job2', 'instance': 'Development'}
        ]

        self.assertEqual(expected_prod_sources, prod_sources)
        self.assertEqual(expected_dev_sources, dev_sources)
        self.assertEqual(expected_vic_prod_sources, vic_prod_sources)
        self.assertEqual(expected_vic_dev_sources, vic_dev_sources)

        util.sources_file.unlink()
        util.sources_file_vic.unlink()


class TestLoadInsSources(unittest.TestCase):
    def setUp(self):
        self.exporter = export.JenkinsExporter()

    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    def test_no_text(self, mock_get):
        mock_get.return_value = None
        with self.assertRaises(Exception):
            self.exporter.load_ins_sources()

    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    def test(self, mock_get):
        mock_get.return_value = json.dumps({
            '_class': 'hudson.model.ListView',
            'jobs': [
                {
                    '_class': 'hudson.model.FreeStyleProject',
                    'name': 'Platform-Generate-Seeds'
                },
                {
                    '_class': 'hudson.model.FreeStyleProject',
                    'name': 'Platform-Patch-A-Seed-Job'
                },
                {
                    '_class': 'org.jenkinsci.plugins.workflow.job.WorkflowJob',
                    'name': 'Platform-Patch-Pipeline-develop'
                },
                {
                    '_class': 'org.jenkinsci.plugins.workflow.job.WorkflowJob',
                    'name': 'Platform-Patch-Pipeline-aws-deploy'
                },
                {
                    '_class': 'hudson.model.FreeStyleProject',
                    'name': 'Platform-Template-A-Seed-Job'
                },
                {
                    '_class': 'org.jenkinsci.plugins.workflow.job.WorkflowJob',
                    'name': 'Platform-Template-AllCores-Pipeline-develop'
                },
                {
                    '_class': 'org.jenkinsci.plugins.workflow.job.WorkflowJob',
                    'name': 'Platform-Template-AllCores-Pipeline-pipeline_corrections'
                }
            ]
        })

        expected = [
            {
                'pipeline': 'Patch',
                'branch': 'develop',
                'job_name': 'Platform-Patch-Pipeline-develop'
            },
            {
                'pipeline': 'Patch',
                'branch': 'aws-deploy',
                'job_name': 'Platform-Patch-Pipeline-aws-deploy'
            },
            {
                'pipeline': 'AllCores',
                'branch': 'develop',
                'job_name': 'Platform-Template-AllCores-Pipeline-develop'
            },
            {
                'pipeline': 'AllCores',
                'branch': 'pipeline_corrections',
                'job_name': 'Platform-Template-AllCores-Pipeline-pipeline_corrections'
            }
        ]

        actual = self.exporter.load_ins_sources()

        self.assertEqual(expected, actual)


class TestLoadConfig(unittest.TestCase):
    def setUp(self):
        self.exporter = export.JenkinsExporter()
        util.etc_dir.mkdir(parents=True)

    def tearDown(self):
        util.rmtree(util.etc_dir)

    @patch('configparser.ConfigParser.read')
    def test_no_config(self, mock_config_read):
        self.exporter.load_config()
        mock_config_read.assert_not_called()

    def test_config(self):
        self.exporter.config.add_section('Development_ci5_Build')
        self.exporter.config.add_section('Production_ci1_Build')
        self.exporter.config.set('Production_ci1_Build', 'lastjobpulledtime', '1234')
        self.exporter.config.add_section('Production_ci6_Deploy')
        self.exporter.config.set('Production_ci6_Deploy', 'lastjobpulledtime', '1230')

        with util.metadata_file.open('w') as config_file:
            self.exporter.config.write(config_file)

        self.exporter.load_config()

        assert self.exporter.config.has_section('Production_ci1_Build')
        assert self.exporter.config.has_section('Production_ci6_Deploy')
        assert self.exporter.config.has_section('Development_ci5_Build')

        assert int(self.exporter.config.get('Production_ci1_Build', 'lastjobpulledtime')) == 1234
        assert int(self.exporter.config.get('Production_ci6_Deploy', 'lastjobpulledtime')) == 1230
        assert int(self.exporter.config.get('Development_ci5_Build', 'lastjobpulledtime')) == 0


class TestLoadAllCoresCommits(unittest.TestCase):
    def setUp(self):
        self.exporter = export.JenkinsExporter()

        self.commits_str = None

        self.expected_all_cores_commits = None

        self.expected_get_calls = []

    def do_it(self):
        with patch.object(export.JenkinsExporter, 'get_text_from_request') as mock_get:
            mock_get.return_value = self.commits_str
            self.exporter.load_all_cores_commits()
            self.assertEqual(self.expected_all_cores_commits, self.exporter.all_cores_commits)
            self.assertEqual(self.expected_get_calls, mock_get.call_args_list)

    def test_no_commits_str(self):
        self.expected_get_calls = [call(self.exporter.ins_all_cores_repo_commits_url, True)]
        self.do_it()

    def test_no_values(self):
        self.commits_str = json.dumps({
            'derp': 'herp'
        })

        self.expected_get_calls = [call(self.exporter.ins_all_cores_repo_commits_url, True)]

        self.do_it()

    def test(self):
        self.commits_str = json.dumps({
            'derp': 'herp',
            'values': 'hello'
        })

        self.expected_all_cores_commits = 'hello'

        self.expected_get_calls = [call(self.exporter.ins_all_cores_repo_commits_url, True)]

        self.do_it()


class TestPull(unittest.TestCase):
    base_url = 'burl'
    pull_title = 'ptitle'
    request_url = 'rurl'
    pull_build_func = 'pbf'
    get_source_fields_func = 'gsff'
    data_dir = 'dir'
    source_filename = 'sfname'

    def setUp(self):
        self.exporter = export.JenkinsExporter()
        self.get_file_name = lambda source, y: self.source_filename + str(source)

    def set_mocks(self, mock_get_file_name, mock_pull_source):
        mock_get_file_name.side_effect = self.get_file_name
        mock_pull_source.return_value = 1, 1000

    def make_asserts(self, sources, requests, bytes_pulled, mock_get_file_name, mock_pull_source):
        expected_requests = len(sources)
        expected_bytes_pulled = len(sources) * 1000
        self.assertEqual(expected_requests, requests)
        self.assertEqual(expected_bytes_pulled, bytes_pulled)

        if not sources:
            mock_get_file_name.assert_not_called()
            mock_pull_source.assert_not_called()

        get_file_name_calls = [call(source, self.get_source_fields_func) for source in sources]
        self.assertEqual(len(sources), mock_get_file_name.call_count)
        mock_get_file_name.assert_has_calls(get_file_name_calls)

        pull_source_calls = [call(source, self.source_filename + str(source), self.data_dir, self.base_url, self.request_url, self.pull_build_func) for source in sources]
        self.assertEqual(len(sources), mock_pull_source.call_count)
        mock_pull_source.assert_has_calls(pull_source_calls)

    def do_it(self, sources, mock_get_file_name, mock_pull_source):
        self.set_mocks(mock_get_file_name, mock_pull_source)
        requests, bytes_pulled = self.exporter.pull(sources, self.base_url, self.pull_title, self.request_url, self.pull_build_func, self.get_source_fields_func, self.data_dir)
        self.make_asserts(sources, requests, bytes_pulled, mock_get_file_name, mock_pull_source)

    @patch('pivt.export_jenkins.JenkinsExporter.pull_source')
    @patch('pivt.export_jenkins.JenkinsExporter.get_file_name')
    def test_no_sources(self, mock_get_file_name, mock_pull_source):
        sources = []
        self.do_it(sources, mock_get_file_name, mock_pull_source)

    @patch('pivt.export_jenkins.JenkinsExporter.pull_source')
    @patch('pivt.export_jenkins.JenkinsExporter.get_file_name')
    def test_some_sources(self, mock_get_file_name, mock_pull_source):
        sources = [1, 2, 3]
        self.do_it(sources, mock_get_file_name, mock_pull_source)


class TestPullSource(unittest.TestCase):
    source_filename1 = 'sfname1'
    base_url = 'burl'
    request_url = '{0}/job/{1}/api/json'
    instance = 'Production'
    job_class = 'class'
    pull_build_func = 'pbf'

    def setUp(self):
        self.exporter = export.JenkinsExporter()
        self.source_data_dir = self.exporter.jenkins_dir
        self.filename1 = '{0}/{1}.json'.format(self.source_data_dir, self.source_filename1)
        self.source_data_dir.mkdir(parents=True)

    def tearDown(self):
        util.rmtree(util.data_dir)

    def pull_builds(*args, **kwargs):
        builds = args[1]
        file_json = []
        for build in builds:
            file_json.append(build)
        args[3]['requests'] += len(file_json)
        args[3]['bytes_pulled'] += len(file_json) * 1000
        return file_json, len(file_json)

    def set_mocks(self, builds, mock_get, mock_pull_builds):
        if builds is not None:
            builds_json = {'_class': self.job_class, 'builds': builds}
            mock_get.return_value = json.dumps(builds_json)
        else:
            mock_get.return_value = None

        mock_pull_builds.side_effect = self.pull_builds

    def make_asserts(self, builds, actual_requests, actual_bytes_pulled, expected_dir_len):
        self.assertEqual(len(builds), actual_requests)
        self.assertEqual(len(builds) * 1000, actual_bytes_pulled)
        self.assertEqual(expected_dir_len, len(util.listdir(self.source_data_dir)))

        if expected_dir_len > 0:
            with open(self.filename1) as file:
                actual_builds = json.loads('[' + ','.join(file.readlines()) + ']')
            self.assertEqual(len(builds), len(actual_builds))
            for build in actual_builds:
                self.assertIn(build, builds)

    def do_it(self, source, builds, expected_dir_len, mock_get, mock_pull_builds):
        self.set_mocks(builds, mock_get, mock_pull_builds)
        requests, bytes_pulled = self.exporter.pull_source(source, self.source_filename1, self.source_data_dir, self.base_url, self.request_url, self.pull_build_func, instance=self.instance)
        if builds is None:
            builds = []
        self.make_asserts(builds, requests, bytes_pulled, expected_dir_len)

    @patch('pivt.export_jenkins.JenkinsExporter.pull_builds')
    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    def test_no_builds(self, mock_get, mock_pull_builds):
        builds = None
        source = {'ci': 'ci1', 'stage': 'Build', 'job_name': 'ci1-Build'}
        self.do_it(source, builds, 0, mock_get, mock_pull_builds)

    @patch('pivt.export_jenkins.JenkinsExporter.pull_builds')
    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    def test_some_builds(self, mock_get, mock_pull_builds):
        builds = [
            {'timestamp': 1, 'url': 'ci1-Build/1'},
            {'timestamp': 3, 'url': 'ci1-Build/3'},
            {'timestamp': 2, 'url': 'ci1-Build/2'}
        ]

        source = {'ci': 'ci1', 'stage': 'Build', 'job_name': 'ci1-Build'}

        self.do_it(source, builds, 1, mock_get, mock_pull_builds)

    @patch('pivt.export_jenkins.JenkinsExporter.pull_builds')
    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    def test_empty_file_json(self, mock_get, mock_pull_builds):
        builds = []
        source = {'ci': 'ci1', 'stage': 'Build', 'job_name': 'ci1-Build'}
        self.do_it(source, builds, 0, mock_get, mock_pull_builds)


class TestPullBuilds(unittest.TestCase):
    def setUp(self):
        self.exporter = export.JenkinsExporter()
        self.actual_builds = {}
        self.file_name = 'Production_ci1_Build'
        self.last_job_pulled_time = 0

    def set_mocks(self, mock_get_last_job_pulled_time):
        mock_get_last_job_pulled_time.return_value = self.last_job_pulled_time

    def make_asserts(self, builds, file_json, pulled_builds, expected_pulled_builds, mock_config):
        expected_file_json = []
        latest_pull_time = self.last_job_pulled_time

        for build in builds:
            try:
                actual_build = self.actual_builds[build['url']]
                timestamp = actual_build['timestamp']
                if timestamp > self.last_job_pulled_time:
                    expected_file_json.append(actual_build)
                if timestamp > latest_pull_time:
                    latest_pull_time = timestamp
            except KeyError:
                pass

        try:
            for build_url in set(self.exporter.unpulled_builds_last[self.file_name]):
                try:
                    actual_build = self.actual_builds[build_url]
                    if actual_build in expected_file_json:
                        continue
                    expected_file_json.append(actual_build)
                except KeyError:
                    continue
        except KeyError:
            pass

        expected_file_json.sort(key=lambda e: e['timestamp'])

        self.assertEqual(expected_file_json, sorted(file_json, key=lambda e: e['timestamp']))
        self.assertEqual(expected_pulled_builds, pulled_builds)
        mock_config.assert_called_once_with(self.file_name, 'lastJobPulledTime', str(latest_pull_time))

    def pull_build(self, *args, **kwargs):
        url = args[0]
        if url in self.actual_builds:
            return self.actual_builds[url]
        return None

    @patch('configparser.ConfigParser.set')
    @patch('pivt.export_jenkins.JenkinsExporter.get_last_job_pulled_time')
    def test_no_unpulled_one_missing(self, mock_get_last_job_pulled_time, mock_config):
        builds = [
            {'timestamp': 1, 'url': 'ci1-Build/1'},
            {'timestamp': 2, 'url': 'i/dont/exist'},
            {'timestamp': 3, 'url': 'ci1-Build/3'}
        ]

        self.actual_builds = {
            'ci1-Build/1': {'timestamp': 1, 'cause': 'Not Assigned'},
            'ci1-Build/3': {'timestamp': 3, 'cause': 'Not Assigned'}
        }

        self.last_job_pulled_time = 0
        expected_pulled_builds = 2

        self.set_mocks(mock_get_last_job_pulled_time)
        file_json, pulled_builds = self.exporter.pull_builds(builds, self.file_name, None, self.pull_build, instance='Production', ci='ci1', stage='Build')
        self.make_asserts(builds, file_json, pulled_builds, expected_pulled_builds, mock_config)

    @patch('configparser.ConfigParser.set')
    @patch('pivt.export_jenkins.JenkinsExporter.get_last_job_pulled_time')
    def test_no_unpulled_last_one_missing(self, mock_get_last_job_pulled_time, mock_config):
        builds = [
            {'timestamp': 1, 'url': 'ci1-Build/1'},
            {'timestamp': 2, 'url': 'ci1-Build/2'},
            {'timestamp': 3, 'url': 'i/dont/exist'}
        ]

        self.actual_builds = {
            'ci1-Build/1': {'timestamp': 1, 'cause': 'Not Assigned'},
            'ci1-Build/2': {'timestamp': 2, 'cause': 'Not Assigned'}
        }

        self.last_job_pulled_time = 0
        expected_pulled_builds = 2

        self.set_mocks(mock_get_last_job_pulled_time)
        file_json, pulled_builds = self.exporter.pull_builds(builds, self.file_name, None, self.pull_build, instance='Production', ci='ci1', stage='Build')
        self.make_asserts(builds, file_json, pulled_builds, expected_pulled_builds, mock_config)

    @patch('configparser.ConfigParser.set')
    @patch('pivt.export_jenkins.JenkinsExporter.get_last_job_pulled_time')
    def test_no_unpulled(self, mock_get_last_job_pulled_time, mock_config):
        builds = [
            {'timestamp': 1, 'url': 'ci1-Build/1'},
            {'timestamp': 2, 'url': 'ci1-Build/2'},
            {'timestamp': 3, 'url': 'ci1-Build/3'}
        ]

        self.actual_builds = {
            'ci1-Build/1': {'timestamp': 1, 'cause': 'Not Assigned'},
            'ci1-Build/2': {'timestamp': 2, 'cause': 'Not Assigned'},
            'ci1-Build/3': {'timestamp': 3, 'cause': 'Not Assigned'}
        }

        self.last_job_pulled_time = 0
        expected_pulled_builds = 3

        self.set_mocks(mock_get_last_job_pulled_time)
        file_json, pulled_builds = self.exporter.pull_builds(builds, self.file_name, None, self.pull_build, instance='Production', ci='ci1', stage='Build')
        self.make_asserts(builds, file_json, pulled_builds, expected_pulled_builds, mock_config)

    @patch('configparser.ConfigParser.set')
    @patch('pivt.export_jenkins.JenkinsExporter.get_last_job_pulled_time')
    def test_no_unpulled_one_old(self, mock_get_last_job_pulled_time, mock_config):
        builds = [
            {'timestamp': 1, 'url': 'ci1-Build/1'},
            {'timestamp': 2, 'url': 'ci1-Build/2'},
            {'timestamp': 3, 'url': 'ci1-Build/3'}
        ]

        self.actual_builds = {
            'ci1-Build/1': {'timestamp': 1, 'cause': 'Not Assigned'},
            'ci1-Build/2': {'timestamp': 2, 'cause': 'Not Assigned'},
            'ci1-Build/3': {'timestamp': 3, 'cause': 'Not Assigned'}
        }

        self.last_job_pulled_time = 1
        expected_pulled_builds = 2

        self.set_mocks(mock_get_last_job_pulled_time)
        file_json, pulled_builds = self.exporter.pull_builds(builds, self.file_name, None, self.pull_build, instance='Production', ci='ci1', stage='Build')
        self.make_asserts(builds, file_json, pulled_builds, expected_pulled_builds, mock_config)

    @patch('configparser.ConfigParser.set')
    @patch('pivt.export_jenkins.JenkinsExporter.get_last_job_pulled_time')
    def test_two_unpulled_one_missing(self, mock_get_last_job_pulled_time, mock_config):
        builds = [
            {'timestamp': 3, 'url': 'ci1-Build/3'},
            {'timestamp': 4, 'url': 'ci1-Build/4'}
        ]

        self.exporter.unpulled_builds_last = {
            self.file_name: ['ci1-Build/1', 'i/dont/exist']
        }

        self.actual_builds = {
            'ci1-Build/1': {'timestamp': 1, 'cause': 'Not Assigned'},
            'ci1-Build/2': {'timestamp': 2, 'cause': 'Not Assigned'},
            'ci1-Build/3': {'timestamp': 3, 'cause': 'Not Assigned'},
            'ci1-Build/4': {'timestamp': 4, 'cause': 'Not Assigned'}
        }

        self.last_job_pulled_time = 1
        expected_pulled_builds = 3

        self.set_mocks(mock_get_last_job_pulled_time)
        file_json, pulled_builds = self.exporter.pull_builds(builds, self.file_name, None, self.pull_build, instance='Production', ci='ci1', stage='Build')
        self.make_asserts(builds, file_json, pulled_builds, expected_pulled_builds, mock_config)

    @patch('configparser.ConfigParser.set')
    @patch('pivt.export_jenkins.JenkinsExporter.get_last_job_pulled_time')
    def test_three_unpulled_two_identical(self, mock_get_last_job_pulled_time,  mock_config):
        builds = []

        self.exporter.unpulled_builds_last = {
            self.file_name: ['ci1-Build/1', 'ci1-Build/1', 'ci1-Build/2']
        }

        self.actual_builds = {
            'ci1-Build/1': {'timestamp': 1, 'cause': 'Not Assigned'},
            'ci1-Build/2': {'timestamp': 2, 'cause': 'Not Assigned'}
        }

        self.last_job_pulled_time = 1
        expected_pulled_builds = 2

        self.set_mocks(mock_get_last_job_pulled_time)
        file_json, pulled_builds = self.exporter.pull_builds(builds, self.file_name, None, self.pull_build, instance='Production', ci='ci1', stage='Build')
        self.make_asserts(builds, file_json, pulled_builds, expected_pulled_builds, mock_config)

    @patch('configparser.ConfigParser.set')
    @patch('pivt.export_jenkins.JenkinsExporter.get_last_job_pulled_time')
    def test_two_unpulled_one_new_same(self, mock_get_last_job_pulled_time, mock_config):
        builds = [
            {'timestamp': 2, 'url': 'ci1-Build/2'},
            {'timestamp': 3, 'url': 'ci1-Build/3'}
        ]

        self.exporter.unpulled_builds_last = {
            self.file_name: ['ci1-Build/1', 'ci1-Build/2']
        }

        self.actual_builds = {
            'ci1-Build/1': {'timestamp': 1, 'cause': 'Not Assigned'},
            'ci1-Build/2': {'timestamp': 2, 'cause': 'Not Assigned'},
            'ci1-Build/3': {'timestamp': 3, 'cause': 'Not Assigned'}
        }

        self.last_job_pulled_time = 1
        expected_pulled_builds = 3

        self.set_mocks(mock_get_last_job_pulled_time)
        file_json, pulled_builds = self.exporter.pull_builds(builds, self.file_name, None, self.pull_build, instance='Production', ci='ci1', stage='Build')
        self.make_asserts(builds, file_json, pulled_builds, expected_pulled_builds, mock_config)

    @patch('configparser.ConfigParser.set')
    @patch('pivt.export_jenkins.JenkinsExporter.get_last_job_pulled_time')
    def test_unordered(self, mock_get_last_job_pulled_time, mock_config):
        builds = [
            {'timestamp': 3, 'url': 'ci1-Build/3'},
            {'timestamp': 1, 'url': 'ci1-Build/1'},
            {'timestamp': 2, 'url': 'ci1-Build/2'}
        ]

        self.actual_builds = {
            'ci1-Build/1': {'timestamp': 1, 'cause': 'Not Assigned'},
            'ci1-Build/2': {'timestamp': 2, 'cause': 'Not Assigned'},
            'ci1-Build/3': {'timestamp': 3, 'cause': 'Not Assigned'}
        }

        self.last_job_pulled_time = 0
        expected_pulled_builds = 3

        self.set_mocks(mock_get_last_job_pulled_time)
        file_json, pulled_builds = self.exporter.pull_builds(builds, self.file_name, None, self.pull_build, instance='Production', ci='ci1', stage='Build')
        self.make_asserts(builds, file_json, pulled_builds, expected_pulled_builds, mock_config)

    @patch('configparser.ConfigParser.set')
    @patch('pivt.export_jenkins.JenkinsExporter.get_last_job_pulled_time')
    def test_unordered_one_old(self, mock_get_last_job_pulled_time, mock_config):
        builds = [
            {'timestamp': 3, 'url': 'ci1-Build/3'},
            {'timestamp': 1, 'url': 'ci1-Build/1'},
            {'timestamp': 2, 'url': 'ci1-Build/2'}
        ]

        self.actual_builds = {
            'ci1-Build/1': {'timestamp': 1, 'cause': 'Not Assigned'},
            'ci1-Build/2': {'timestamp': 2, 'cause': 'Not Assigned'},
            'ci1-Build/3': {'timestamp': 3, 'cause': 'Not Assigned'}
        }

        self.last_job_pulled_time = 1
        expected_pulled_builds = 2

        self.set_mocks(mock_get_last_job_pulled_time)
        file_json, pulled_builds = self.exporter.pull_builds(builds, self.file_name, None, self.pull_build, instance='Production', ci='ci1', stage='Build')
        self.make_asserts(builds, file_json, pulled_builds, expected_pulled_builds, mock_config)

    @patch('configparser.ConfigParser.set')
    @patch('pivt.export_jenkins.JenkinsExporter.get_last_job_pulled_time')
    def test_all_old(self, mock_get_last_job_pulled_time, mock_config):
        builds = [
            {'timestamp': 1, 'url': 'ci1-Build/1'},
            {'timestamp': 2, 'url': 'ci1-Build/2'},
            {'timestamp': 3, 'url': 'ci1-Build/3'}
        ]

        self.actual_builds = {
            'ci1-Build/1': {'timestamp': 1, 'cause': 'Not Assigned'},
            'ci1-Build/2': {'timestamp': 2, 'cause': 'Not Assigned'},
            'ci1-Build/3': {'timestamp': 3, 'cause': 'Not Assigned'}
        }

        self.last_job_pulled_time = 3
        expected_pulled_builds = 0

        self.set_mocks(mock_get_last_job_pulled_time)
        file_json, pulled_builds = self.exporter.pull_builds(builds, self.file_name, None, self.pull_build, instance='Production', ci='ci1', stage='Build')
        self.make_asserts(builds, file_json, pulled_builds, expected_pulled_builds, mock_config)


class TestPullBuildProduct(unittest.TestCase):
    build_url = 'burl'
    cause = 'nightly'
    base_url = 'derp'

    def setUp(self):
        self.exporter = export.JenkinsExporter()

        self.build = None
        self.building = False
        self.source_filename = None
        self.pipeline_url = None
        self.pipeline_props = None
        self.pipeline_json = None
        self.pipeline_building = False
        self.parsed_pipeline_props = None
        self.ut_report = None
        self.ft_reports = None

        self.pull_file_return_vals = []

        self.expected_build_json = None

        self.expected_pull_fs_build_calls = []
        self.expected_is_building_calls = []
        self.expected_add_unpulled_calls = []
        self.expected_get_parameter_calls = []
        self.expected_get_pipeline_files_calls = []
        self.expected_pull_file_calls = []
        self.expected_parse_pipeline_props_calls = []
        self.expected_get_cause_calls = []
        self.expected_pull_ft_calls = []
        self.expected_pull_ut_calls = []
        self.expected_pipeline_files = {}

        self.old_ci_to_ss = deepcopy(util.ci_to_ss)

        util.ci_to_ss = {
            'ci3': 'ss1'
        }

    def tearDown(self):
        util.ci_to_ss = self.old_ci_to_ss

    def set_source_filename(self, instance, ci, stage):
        self.source_filename = instance + '_' + ci + '_' + stage

    def do_it(self, **kwargs):
        with patch.object(export.JenkinsExporter, 'pull_freestyle_build') as mock_pull_fs_build, \
                patch.object(export.JenkinsExporter, 'is_building') as mock_is_building, \
                patch.object(export.JenkinsExporter, 'add_to_unpulled') as mock_add_to_unpulled, \
                patch.object(export.JenkinsExporter, 'get_parameter') as mock_get_parameter, \
                patch.object(export.JenkinsExporter, 'get_pipeline_files') as mock_get_pipeline_files, \
                patch.object(export.JenkinsExporter, 'pull_one_file') as mock_pull_file, \
                patch.object(export.JenkinsExporter, 'parse_pipeline_properties') as mock_parse_pipeline_props, \
                patch.object(export.JenkinsExporter, 'get_cause') as mock_get_cause, \
                patch.object(export.JenkinsExporter, 'pull_ft') as mock_pull_ft, \
                patch.object(export.JenkinsExporter, 'pull_ut') as mock_pull_ut:
            self.set_mocks(mock_pull_fs_build, mock_is_building, mock_add_to_unpulled, mock_get_parameter,
                           mock_get_pipeline_files, mock_pull_file, mock_parse_pipeline_props, mock_get_cause,
                           mock_pull_ft, mock_pull_ut)

            def really_do_it():
                build_json = self.exporter.pull_build_product(self.build_url, self.source_filename, None, **kwargs)
                self.make_asserts(build_json, mock_pull_fs_build, mock_is_building, mock_add_to_unpulled,
                                  mock_get_parameter, mock_get_pipeline_files, mock_pull_file,
                                  mock_parse_pipeline_props, mock_get_cause, mock_pull_ft, mock_pull_ut)

            if not kwargs:
                with self.assertRaises(KeyError):
                    really_do_it()
            else:
                really_do_it()

    def set_mocks(self, mock_pull_fs_build, mock_is_building, mock_add_to_unpulled, mock_get_parameter,
                  mock_get_pipeline_files, mock_pull_file, mock_parse_pipeline_props, mock_get_cause, mock_pull_ft, mock_pull_ut):
        mock_pull_fs_build.return_value = self.build
        mock_is_building.return_value = self.building
        mock_get_parameter.return_value = self.pipeline_url

        if self.pipeline_building:
            mock_get_pipeline_files.return_value = 'pipeline_building'
        elif self.pipeline_props is None and self.pipeline_json is None:
            mock_get_pipeline_files.return_value = None
        else:
            mock_get_pipeline_files.return_value = {'props': self.pipeline_props, 'json': self.pipeline_json}

        mock_parse_pipeline_props.return_value = self.parsed_pipeline_props
        mock_get_cause.return_value = self.cause
        mock_pull_file.side_effect = self.pull_file_return_vals
        mock_pull_ut.return_value = self.ut_report
        mock_pull_ft.return_value = self.ft_reports

    def make_asserts(self, build_json, mock_pull_fs_build, mock_is_building, mock_add_to_unpulled, mock_get_parameter,
                     mock_get_pipeline_files, mock_pull_file, mock_parse_pipeline_props, mock_get_cause, mock_pull_ft,
                     mock_pull_ut):
        self.assertEqual(self.expected_build_json, build_json)

        self.assertEqual(self.expected_pull_fs_build_calls, mock_pull_fs_build.call_args_list)
        self.assertEqual(self.expected_is_building_calls, mock_is_building.call_args_list)
        self.assertEqual(self.expected_add_unpulled_calls, mock_add_to_unpulled.call_args_list)
        self.assertEqual(self.expected_get_parameter_calls, mock_get_parameter.call_args_list)
        self.assertEqual(self.expected_get_pipeline_files_calls, mock_get_pipeline_files.call_args_list)
        self.assertEqual(self.expected_pull_file_calls, mock_pull_file.call_args_list)
        self.assertEqual(self.expected_parse_pipeline_props_calls, mock_parse_pipeline_props.call_args_list)
        self.assertEqual(self.expected_get_cause_calls, mock_get_cause.call_args_list)
        self.assertEqual(self.expected_pull_ft_calls, mock_pull_ft.call_args_list)
        self.assertEqual(self.expected_pull_ut_calls, mock_pull_ut.call_args_list)
        self.assertEqual(self.expected_pipeline_files, self.exporter.pipeline_files)

    def test_no_build(self):
        self.expected_pull_fs_build_calls = [call(self.build_url, None)]
        self.do_it(base_url=self.base_url)

    def test_no_kwargs(self):
        self.do_it()

    def test_build_building(self):
        self.build = {'derp': 'herp'}
        self.building = True

        self.expected_pull_fs_build_calls = [call(self.build_url, None)]
        self.expected_is_building_calls = [call(self.build, 'building', True)]
        self.expected_add_unpulled_calls = [call(self.source_filename, self.build_url)]

        self.do_it(base_url=self.base_url)

    def test_pipeline_build(self):
        self.build = {'derp': 'herp'}
        self.set_source_filename('Production', 'ci3', 'Pipeline')
        self.pipeline_props = 'props'
        self.pipeline_json = '{}'
        self.pull_file_return_vals = [self.pipeline_props, self.pipeline_json]
        self.parsed_pipeline_props = 'derp'

        self.expected_build_json = {
            'derp': 'herp',
            'pipeline_properties': 'derp',
            'ci': 'ci3',
            'stage': 'Pipeline',
            'instance': 'Production',
            'ss': 'ss1',
            'cause': 'nightly',
            'pipeline_json': {}
        }

        self.expected_pull_fs_build_calls = [call(self.build_url, None)]
        self.expected_is_building_calls = [call(self.build, 'building', True)]
        self.expected_pull_file_calls = [
            call('pipeline.properties', self.build, self.build_url, None, str()),
            call('pipeline.json', self.build, self.build_url, None, '{}')
        ]
        self.expected_parse_pipeline_props_calls = [call('props', self.build)]
        self.expected_get_cause_calls = [call(self.build, 'Production', self.base_url, None)]
        self.expected_pipeline_files = {
            self.build_url: {
                'props': 'derp',
                'json': {}
            }
        }

        self.do_it(base_url=self.base_url)

    def test_pipeline_build_props_exist(self):
        self.build = {'derp': 'herp'}
        self.set_source_filename('Production', 'ci3', 'Pipeline')
        self.exporter.pipeline_files = {
            self.build_url: {
                'props': 'derp',
                'json': {}
            }
        }

        self.expected_build_json = {
            'derp': 'herp',
            'pipeline_properties': 'derp',
            'ci': 'ci3',
            'stage': 'Pipeline',
            'instance': 'Production',
            'ss': 'ss1',
            'cause': 'nightly',
            'pipeline_json': {}
        }

        self.expected_pull_fs_build_calls = [call(self.build_url, None)]
        self.expected_is_building_calls = [call(self.build, 'building', True)]
        self.expected_get_cause_calls = [call(self.build, 'Production', self.base_url, None)]

        self.expected_pipeline_files = {
            self.build_url: {
                'props': 'derp',
                'json': {}
            }
        }

        self.do_it(base_url=self.base_url)

    def test_non_pipeline_no_pipeline_url(self):
        self.build = {'derp': 'herp'}
        self.set_source_filename('Production', 'ci3', 'Deploy')
        self.pipeline_props = None
        self.pipeline_json = None

        self.expected_build_json = {
            'derp': 'herp',
            'ci': 'ci3',
            'stage': 'Deploy',
            'instance': 'Production',
            'ss': 'ss1',
            'cause': 'nightly'
        }

        self.expected_pull_fs_build_calls = [call(self.build_url, None)]
        self.expected_is_building_calls = [call(self.build, 'building', True)]
        self.expected_get_parameter_calls = [call(self.build, 'PIPELINE_URL')]
        self.expected_get_pipeline_files_calls = [call(None, None)]
        self.expected_get_cause_calls = [call(self.build, 'Production', self.base_url, None)]

        self.do_it(base_url=self.base_url)

    def test_non_pipeline_pipeline_building(self):
        self.build = {'derp': 'herp'}
        self.set_source_filename('Production', 'ci3', 'Deploy')
        self.pipeline_props = 'pipeline_building'
        self.pipeline_url = 'my-pipeline/12'
        self.pipeline_building = True

        self.expected_pull_fs_build_calls = [call(self.build_url, None)]
        self.expected_is_building_calls = [call(self.build, 'building', True)]
        self.expected_get_parameter_calls = [call(self.build, 'PIPELINE_URL')]
        self.expected_get_pipeline_files_calls = [call('my-pipeline/12', None)]
        self.expected_add_unpulled_calls = [call(self.source_filename, self.build_url)]

        self.do_it(base_url=self.base_url)

    def test_non_pipeline(self):
        self.build = {'derp': 'herp'}
        self.set_source_filename('Production', 'ci3', 'Deploy')
        self.pipeline_props = 'props'
        self.pipeline_url = 'my-pipeline/12'
        self.pipeline_json = {}

        self.expected_build_json = {
            'derp': 'herp',
            'pipeline_properties': 'props',
            'ci': 'ci3',
            'stage': 'Deploy',
            'instance': 'Production',
            'ss': 'ss1',
            'cause': 'nightly',
            'pipeline_json': {}
        }

        self.expected_pull_fs_build_calls = [call(self.build_url, None)]
        self.expected_is_building_calls = [call(self.build, 'building', True)]
        self.expected_get_parameter_calls = [call(self.build, 'PIPELINE_URL')]
        self.expected_get_pipeline_files_calls = [call('my-pipeline/12', None)]
        self.expected_get_cause_calls = [call(self.build, 'Production', self.base_url, None)]

        self.do_it(base_url=self.base_url)

    def test_ut(self):
        self.build = {'derp': 'herp'}
        self.set_source_filename('Production', 'ci3', 'UnitTest')
        self.ut_report = 'ut_report'
        self.pipeline_json = {}

        self.expected_build_json = {
            'derp': 'herp',
            'pipeline_properties': None,
            'ci': 'ci3',
            'stage': 'UnitTest',
            'instance': 'Production',
            'ss': 'ss1',
            'cause': 'nightly',
            'pipeline_json': {},
            'report': self.ut_report
        }

        self.expected_pull_fs_build_calls = [call(self.build_url, None)]
        self.expected_is_building_calls = [call(self.build, 'building', True)]
        self.expected_get_parameter_calls = [call(self.build, 'PIPELINE_URL')]
        self.expected_get_pipeline_files_calls = [call(self.pipeline_url, None)]
        self.expected_get_cause_calls = [call(self.build, 'Production', self.base_url, None)]
        self.expected_pull_ut_calls = [call(self.build_url, self.base_url, None)]

        self.do_it(base_url=self.base_url)

    def test_ut_no_report(self):
        self.build = {'derp': 'herp'}
        self.set_source_filename('Production', 'ci3', 'UnitTest')
        self.pipeline_json = {}

        self.expected_build_json = {
            'derp': 'herp',
            'pipeline_properties': None,
            'ci': 'ci3',
            'stage': 'UnitTest',
            'instance': 'Production',
            'ss': 'ss1',
            'cause': 'nightly',
            'pipeline_json': {}
        }

        self.expected_pull_fs_build_calls = [call(self.build_url, None)]
        self.expected_is_building_calls = [call(self.build, 'building', True)]
        self.expected_get_parameter_calls = [call(self.build, 'PIPELINE_URL')]
        self.expected_get_pipeline_files_calls = [call(self.pipeline_url, None)]
        self.expected_get_cause_calls = [call(self.build, 'Production', self.base_url, None)]
        self.expected_pull_ut_calls = [call(self.build_url, self.base_url, None)]

        self.do_it(base_url=self.base_url)

    def test_ft(self):
        self.build = {'derp': 'herp'}
        self.set_source_filename('Production', 'ci3', 'AWS-FunctionalTest')
        self.ft_reports = 'ft_reports'
        self.pipeline_json = {}

        self.expected_build_json = {
            'derp': 'herp',
            'pipeline_properties': None,
            'ci': 'ci3',
            'stage': 'AWS_FunctionalTest',
            'instance': 'Production',
            'ss': 'ss1',
            'cause': 'nightly',
            'pipeline_json': {},
            'reports': self.ft_reports
        }

        self.expected_pull_fs_build_calls = [call(self.build_url, None)]
        self.expected_is_building_calls = [call(self.build, 'building', True)]
        self.expected_get_parameter_calls = [call(self.build, 'PIPELINE_URL')]
        self.expected_get_pipeline_files_calls = [call(self.pipeline_url, None)]
        self.expected_get_cause_calls = [call(self.build, 'Production', self.base_url, None)]
        self.expected_pull_ft_calls = [call(self.build, self.build_url, None)]

        self.do_it(base_url=self.base_url)


class TestGetPipelineFiles(unittest.TestCase):
    def setUp(self):
        self.exporter = export.JenkinsExporter()

        self.pipeline_url = None

        self.build_json = None
        self.building = False
        self.props = None
        self.parsed_props = None
        self.pipeline_json = None

        self.expected_pull_fs_build_calls = []
        self.expected_is_building_calls = []
        self.expected_pull_file_calls = []
        self.expected_parse_props_calls = []

        self.expected_files = None
        self.expected_files_dict = {}

    def do_it(self):
        with patch.object(export.JenkinsExporter, 'pull_freestyle_build') as mock_pull_fs_build, \
                patch.object(export.JenkinsExporter, 'is_building') as mock_is_building, \
                patch.object(export.JenkinsExporter, 'pull_one_file') as mock_pull_file, \
                patch.object(export.JenkinsExporter, 'parse_pipeline_properties') as mock_parse_props:
            self.set_mocks(mock_pull_fs_build, mock_is_building, mock_pull_file, mock_parse_props)
            actual_files = self.exporter.get_pipeline_files(self.pipeline_url, None)
            self.make_asserts(actual_files, mock_pull_fs_build, mock_is_building, mock_pull_file, mock_parse_props)

    def set_mocks(self, mock_pull_fs_build, mock_is_building, mock_pull_file, mock_parse_props):
        mock_pull_fs_build.return_value = self.build_json
        mock_is_building.return_value = self.building
        mock_pull_file.side_effect = [self.props, self.pipeline_json]
        mock_parse_props.return_value = self.parsed_props

    def make_asserts(self, actual_files, mock_pull_fs_build, mock_is_building, mock_pull_file, mock_parse_props):
        self.assertEqual(self.expected_pull_fs_build_calls, mock_pull_fs_build.call_args_list)
        self.assertEqual(self.expected_is_building_calls, mock_is_building.call_args_list)
        self.assertEqual(self.expected_pull_file_calls, mock_pull_file.call_args_list)
        self.assertEqual(self.expected_parse_props_calls, mock_parse_props.call_args_list)

        self.assertEqual(self.expected_files, actual_files)
        self.assertEqual(self.expected_files_dict, self.exporter.pipeline_files)

    def test_no_pipeline_url(self):
        self.do_it()

    def test_props_exist(self):
        self.pipeline_url = 'url'
        self.exporter.pipeline_files = {
            'url': {
                'props': 'derp',
                'json': 'herp'
            }
        }

        self.expected_files = {'props': 'derp', 'json': 'herp'}
        self.expected_files_dict = {
            'url': {
                'props': 'derp',
                'json': 'herp'
            }
        }

        self.do_it()

    def test_no_build_json(self):
        self.pipeline_url = 'url'

        self.expected_pull_fs_build_calls = [call('url', None)]

        self.do_it()

    def test_building(self):
        self.pipeline_url = 'url'
        self.build_json = 'build_json'
        self.building = True

        self.expected_pull_fs_build_calls = [call('url', None)]
        self.expected_is_building_calls = [call('build_json', 'building', True)]

        self.expected_files = 'pipeline_building'

        self.do_it()

    def test(self):
        self.pipeline_url = 'url'
        self.build_json = 'build_json'
        self.props = 'props'
        self.parsed_props = 'parsed_props'
        self.pipeline_json = '{"derp": "herp"}'

        self.expected_pull_fs_build_calls = [call('url', None)]
        self.expected_is_building_calls = [call('build_json', 'building', True)]
        self.expected_pull_file_calls = [
            call('pipeline.properties', 'build_json', 'url', None, str()),
            call('pipeline.json', 'build_json', 'url', None, '{}')
        ]
        self.expected_parse_props_calls = [call('props', 'build_json')]

        self.expected_files = {'props': 'parsed_props', 'json': {'derp': 'herp'}}
        self.expected_files_dict = {
            'url': {
                'props': 'parsed_props',
                'json': {'derp': 'herp'}
            }
        }

        self.do_it()


class TestPullBuildIns(unittest.TestCase):
    build_url = 'burl'

    def setUp(self):
        self.exporter = export.JenkinsExporter()

        self.source_filename = 'Core1_master'
        self.pull_wf_build_value = None
        self.all_cores = None
        self.pull_fs_build_value = None
        self.params = None

        self.expected_build_json = None

        self.expected_pull_wf_build_calls = []
        self.expected_pull_all_cores_file_calls = []
        self.expected_insert_core_info_calls = []
        self.expected_pull_fs_build_calls = []
        self.expected_get_all_params_calls = []

    def do_it(self):
        with patch.object(export.JenkinsExporter, 'pull_workflow_build') as mock_pull_wf_build, \
                patch.object(export.JenkinsExporter, 'pull_ins_all_cores_file') as mock_pull_all_cores_file, \
                patch.object(export.JenkinsExporter, 'insert_core_info_into_build_json') as mock_insert_core_info, \
                patch.object(export.JenkinsExporter, 'pull_freestyle_build') as mock_pull_fs_build, \
                patch.object(export.JenkinsExporter, 'get_all_parameters') as mock_get_all_params:
            self.set_mocks(mock_pull_wf_build, mock_pull_all_cores_file, mock_insert_core_info, mock_pull_fs_build, mock_get_all_params)
            build_json = self.exporter.pull_build_ins(self.build_url, self.source_filename, None)
            self.make_asserts(build_json, mock_pull_wf_build, mock_pull_all_cores_file, mock_insert_core_info, mock_pull_fs_build, mock_get_all_params)

    def set_mocks(self, mock_pull_wf_build, mock_pull_all_cores_file, mock_insert_core_info, mock_pull_fs_build, mock_get_all_params):
        mock_pull_wf_build.return_value = self.pull_wf_build_value
        mock_pull_all_cores_file.return_value = self.all_cores
        mock_pull_fs_build.return_value = self.pull_fs_build_value
        mock_get_all_params.return_value = self.params

    def make_asserts(self, actual_build_json, mock_pull_wf_build, mock_pull_all_cores_file, mock_insert_core_info, mock_pull_fs_build, mock_get_all_params):
        self.assertEqual(self.expected_build_json, actual_build_json)

        self.assertEqual(self.expected_pull_wf_build_calls, mock_pull_wf_build.call_args_list)
        self.assertEqual(self.expected_pull_all_cores_file_calls, mock_pull_all_cores_file.call_args_list)
        self.assertEqual(self.expected_insert_core_info_calls, mock_insert_core_info.call_args_list)
        self.assertEqual(self.expected_pull_fs_build_calls, mock_pull_fs_build.call_args_list)
        self.assertEqual(self.expected_get_all_params_calls, mock_get_all_params.call_args_list)

    def test_no_build(self):
        self.expected_pull_wf_build_calls = [call(self.build_url, self.source_filename, self.exporter.dev_url, None)]
        self.do_it()

    def test_no_all_cores(self):
        build = {'derp': 'herp', 'timestamp': 5}

        self.pull_wf_build_value = build

        self.expected_build_json = {**deepcopy(build), **{'pipeline': 'Core1', 'branch': 'master'}}

        self.expected_pull_wf_build_calls = [call(self.build_url, self.source_filename, self.exporter.dev_url, None)]
        self.expected_pull_fs_build_calls = [call(self.build_url, None, depth=0)]

        self.do_it()

    def test_all_cores_not_all_cores_filename(self):
        build = {'derp': 'herp', 'timestamp': 5}

        self.pull_wf_build_value = build
        self.all_cores = 'derp'

        self.expected_build_json = {**deepcopy(build), **{'pipeline': 'Core1', 'branch': 'master'}}

        self.expected_pull_wf_build_calls = [call(self.build_url, self.source_filename, self.exporter.dev_url, None)]
        self.expected_pull_fs_build_calls = [call(self.build_url, None, depth=0)]

        self.do_it()

    def test_all_cores_no_traditional_build(self):
        build = {'derp': 'herp', 'timestamp': 5}

        self.source_filename = 'AllCores_develop'
        self.pull_wf_build_value = build
        self.all_cores = 'derp'

        self.expected_build_json = {**deepcopy(build), **{'pipeline': 'AllCores', 'branch': 'develop'}}

        self.expected_pull_wf_build_calls = [call(self.build_url, self.source_filename, self.exporter.dev_url, None)]
        self.expected_pull_all_cores_file_calls = [call(5, None)]
        self.expected_insert_core_info_calls = [call(self.expected_build_json, 'derp')]
        self.expected_pull_fs_build_calls = [call(self.build_url, None, depth=0)]

        self.do_it()

    def test_all_cores(self):
        build = {'derp': 'herp', 'timestamp': 5}

        self.source_filename = 'AllCores_develop'
        self.pull_wf_build_value = build
        self.all_cores = 'derp'
        self.pull_fs_build_value = 'omg'
        self.params = 'params'

        self.expected_build_json = {**deepcopy(build), **{'pipeline': 'AllCores', 'branch': 'develop', 'params': 'params'}}

        self.expected_pull_wf_build_calls = [call(self.build_url, self.source_filename, self.exporter.dev_url, None)]
        self.expected_pull_all_cores_file_calls = [call(5, None)]
        self.expected_insert_core_info_calls = [call(self.expected_build_json, 'derp')]
        self.expected_pull_fs_build_calls = [call(self.build_url, None, depth=0)]
        self.expected_get_all_params_calls = [call(self.pull_fs_build_value)]

        self.do_it()


class TestPullInsAllCoresFile(unittest.TestCase):
    build_timestamp = 5

    def setUp(self):
        self.exporter = export.JenkinsExporter()

        self.file_str = None
        self.safe_load_value = 'all cores'

        self.expected_all_cores = None

        self.expected_get_calls = []
        self.expected_safe_load_calls = []
        self.expected_all_cores_files = {}

    def do_it(self):
        with patch.object(export.JenkinsExporter, 'get_text_from_request') as mock_get, \
                patch.object(yaml, 'safe_load') as mock_safe_load:
            self.set_mocks(mock_get, mock_safe_load)
            self.expected_all_cores_files = {**self.expected_all_cores_files, **deepcopy(self.exporter.all_cores_files)}
            all_cores = self.exporter.pull_ins_all_cores_file(self.build_timestamp, None)
            self.make_asserts(all_cores, mock_get, mock_safe_load)

    def set_mocks(self, mock_get, mock_safe_load):
        mock_get.return_value = self.file_str
        mock_safe_load.return_value = self.safe_load_value

    def make_asserts(self, actual_all_cores, mock_get, mock_safe_load):
        self.assertEqual(self.expected_all_cores, actual_all_cores)

        self.assertEqual(self.expected_get_calls, mock_get.call_args_list)
        self.assertEqual(self.expected_safe_load_calls, mock_safe_load.call_args_list)

        self.assertEqual(self.expected_all_cores_files, self.exporter.all_cores_files)

    def test_no_commits(self):
        self.do_it()

    def test_no_commit_before_time(self):
        self.exporter.all_cores_commits = [
            {
                'committerTimestamp': 7,
                'id': 'commit1'
            },
            {
                'committerTimestamp': 6,
                'id': 'commit2'
            }
        ]

        self.do_it()

    def test_existing_file(self):
        self.exporter.all_cores_commits = [
            {
                'committerTimestamp': 7,
                'id': 'commit1'
            },
            {
                'committerTimestamp': 5,
                'id': 'commit2'
            }
        ]

        self.exporter.all_cores_files = {
            'commit2': 'all cores'
        }

        self.expected_all_cores = 'all cores'

        self.do_it()

    def test_no_existing_files_dict_no_file_str(self):
        self.exporter.all_cores_commits = [
            {
                'committerTimestamp': 7,
                'id': 'commit1'
            },
            {
                'committerTimestamp': 5,
                'id': 'commit2'
            }
        ]

        self.expected_get_calls = [call(self.exporter.ins_all_cores_file_url + 'commit2', True, None)]

        self.do_it()

    def test_no_existing_files_no_file_str(self):
        self.exporter.all_cores_commits = [
            {
                'committerTimestamp': 7,
                'id': 'commit1'
            },
            {
                'committerTimestamp': 5,
                'id': 'commit2'
            }
        ]

        self.exporter.all_cores_files = {
            'commit1': 'all cores'
        }

        self.expected_get_calls = [call(self.exporter.ins_all_cores_file_url + 'commit2', True, None)]

        self.do_it()

    def test(self):
        self.exporter.all_cores_commits = [
            {
                'committerTimestamp': 7,
                'id': 'commit1'
            },
            {
                'committerTimestamp': 4,
                'id': 'commit2'
            }
        ]

        self.exporter.all_cores_files = {
            'commit1': 'all cores'
        }

        self.file_str = 'some yaml'

        self.expected_all_cores = 'all cores'

        self.expected_get_calls = [call(self.exporter.ins_all_cores_file_url + 'commit2', True, None)]
        self.expected_safe_load_calls = [call('some yaml')]

        self.expected_all_cores_files['commit2'] = 'all cores'

        self.do_it()


class TestInsertCoreInfoIntoBuildJson(unittest.TestCase):
    def setUp(self):
        self.exporter = export.JenkinsExporter()

        self.build_json = {
            '_links': {
                'self': {
                    'href': 'build_link'
                }
            }
        }

        self.all_cores = None

        self.expected_build_json = deepcopy(self.build_json)

    def do_it(self):
        self.exporter.insert_core_info_into_build_json(self.build_json, self.all_cores)
        self.make_asserts()

    def make_asserts(self):
        self.assertEqual(self.expected_build_json, self.build_json)

    def test_no_all_cores(self):
        self.do_it()

    def test_no_allcores_in_all_cores(self):
        self.all_cores = {
            'derp': 'herp'
        }

        self.do_it()

    def test_all_cores(self):
        self.build_json['stages'] = [
            {
                'name': 'stage1',
                'status': 'SUCCESS'
            },
            {
                'name': 'stage2',
                'status': 'FAILED'
            }
        ]

        self.all_cores = {
            'AllCores': [
                {
                    'name': 'stage1',
                    'core': 'all'
                },
                {
                    'stage2': None,
                    'name': 'stage2',
                    'core': 'core1'
                },
                {
                    'stage3': None,
                    'name': 'stage3',
                    'core': 'core2'
                }
            ],
            'derp': 'herp'
        }

        self.expected_build_json['stages'] = [
            {
                'name': 'stage1',
                'status': 'SUCCESS',
                'truth': {
                    'name': 'stage1',
                    'core': 'all'
                }
            },
            {
                'name': 'stage2',
                'status': 'FAILED',
                'truth': {
                    'name': 'stage2',
                    'core': 'core1'
                }
            },
            {
                'truth': {
                    'name': 'stage3',
                    'core': 'core2'
                }
            }
        ]

        self.do_it()


class TestPullBuildVic(unittest.TestCase):
    def setUp(self):
        self.exporter = export.JenkinsExporter()

        self.build = None
        self.build_url = 'derp'
        self.job_name = 'job1'
        self.building = False
        self.instance = 'Production'
        self.job_class = 'workflow'
        self.base_url = self.exporter.prod_url
        self.action = ''

        self.console_text = None

        self.expected_build_json = None
        self.expected_pull_wf_build_called = False
        self.expected_pull_fs_build_called = False
        self.expected_is_building_called = False
        self.expected_add_to_unpulled_called = False

    def do_it(self):
        source_filename = self.instance + '_' + self.job_name

        with patch.object(export.JenkinsExporter, 'pull_workflow_build') as mock_pull_wf_build, \
                patch.object(export.JenkinsExporter, 'pull_freestyle_build') as mock_pull_fs_build, \
                patch.object(export.JenkinsExporter, 'is_building') as mock_is_building, \
                patch.object(export.JenkinsExporter, 'add_to_unpulled') as mock_add_to_unpulled, \
                patch.object(export.JenkinsExporter, 'get_parameter') as mock_get_parameter, \
                patch.object(export.JenkinsExporter, 'get_text_from_request') as mock_get:
            self.set_mocks(mock_pull_wf_build, mock_pull_fs_build, mock_is_building, mock_get_parameter, mock_get)

            kwargs = {}
            if self.job_class is not None:
                kwargs['job_class'] = self.job_class
            if self.base_url is not None:
                kwargs['base_url'] = self.base_url

            build_json = self.exporter.pull_build_vic(self.build_url, source_filename, None, **kwargs)
            self.make_asserts(build_json, mock_pull_wf_build, mock_pull_fs_build, mock_is_building, mock_add_to_unpulled)

    def set_mocks(self, mock_pull_wf_build, mock_pull_fs_build, mock_is_building, mock_get_parameter, mock_get):
        mock_pull_wf_build.return_value = self.build
        mock_pull_fs_build.return_value = self.build
        mock_is_building.return_value = self.building
        mock_get_parameter.return_value = self.action
        mock_get.return_value = self.console_text

    def make_asserts(self, build_json, mock_pull_wf_build, mock_pull_fs_build, mock_is_building, mock_add_to_unpulled):
        self.assertEqual(self.expected_build_json, build_json)
        self.assertEqual(self.expected_pull_wf_build_called, mock_pull_wf_build.called)
        self.assertEqual(self.expected_pull_fs_build_called, mock_pull_fs_build.called)
        self.assertEqual(self.expected_is_building_called, mock_is_building.called)
        self.assertEqual(self.expected_add_to_unpulled_called, mock_add_to_unpulled.called)

    def test_no_kwargs(self):
        self.job_class = None
        self.base_url = None

        with self.assertRaises(KeyError):
            self.do_it()

    def test_workflow_no_build(self):
        self.expected_pull_wf_build_called = True

        self.do_it()

    def test_workflow(self):
        self.build = {'derp': 'herp'}

        self.expected_build_json = {'derp': 'herp', 'instance': self.instance}
        self.expected_pull_wf_build_called = True

        self.do_it()

    def test_freestyle(self):
        self.build = {'derp': 'herp'}
        self.job_class = 'something_else'

        self.expected_build_json = {'derp': 'herp', 'instance': self.instance}
        self.expected_pull_fs_build_called = True
        self.expected_is_building_called = True

        self.do_it()

    def test_freestyle_building(self):
        self.build = {'derp': 'herp'}
        self.job_class = 'something_else'
        self.building = True

        self.expected_build_json = None
        self.expected_pull_fs_build_called = True
        self.expected_is_building_called = True
        self.expected_add_to_unpulled_called = True

        self.do_it()

    def test_vic_number_no_action(self):
        self.build = {'derp': 'herp'}
        self.job_name = 'AWS-VIC-Manager'
        self.job_class = 'something_else'

        self.expected_build_json = {'derp': 'herp', 'instance': self.instance}
        self.expected_pull_fs_build_called = True
        self.expected_is_building_called = True

        self.do_it()

    def test_no_console_text(self):
        self.build = {
            'derp': 'herp',
            'actions': [
                {
                    'name': 'derp',
                    'value': 'herp'
                }
            ]
        }
        self.job_name = 'AWS-VIC-Manager'
        self.job_class = 'something_else'
        self.action = 'start-instance'

        self.expected_build_json = {**deepcopy(self.build), 'instance': 'Production'}

        self.expected_pull_fs_build_called = True
        self.expected_is_building_called = True

        self.do_it()

    def test_action_start_instance_no_vic_ci_match(self):
        self.build = {
            'derp': 'herp',
            'actions': [
                {
                    'name': 'derp',
                    'value': 'herp'
                }
            ]
        }
        self.job_name = 'AWS-VIC-Manager'
        self.job_class = 'something_else'
        self.console_text = 'derp\n' \
                            'herp\n' \
                            '. Created AWS VIC \'43\' under IP 5...\n' \
                            'hi\n'
        self.action = 'start-instance'

        self.expected_build_json = {**deepcopy(self.build), 'instance': 'Production'}

        self.expected_pull_fs_build_called = True
        self.expected_is_building_called = True

        self.do_it()

    def test_action_start_instance(self):
        self.build = {
            'derp': 'herp',
            'actions': [
                {
                    'name': 'derp',
                    'value': 'herp'
                }
            ]
        }
        self.job_name = 'AWS-VIC-Manager'
        self.job_class = 'something_else'
        self.console_text = 'derp\n' \
                            'herp\n' \
                            'CI: cool ci\n' \
                            '. Created AWS VIC \'43\' under IP 5...\n' \
                            'hi\n'
        self.action = 'start-instance'

        self.expected_build_json = {**deepcopy(self.build), 'instance': 'Production', 'vic_ci': 'cool ci'}

        self.expected_pull_fs_build_called = True
        self.expected_is_building_called = True

        self.do_it()

    def test_action_create_vic_no_vic_number_match(self):
        self.build = {
            'derp': 'herp',
            'actions': [
                {
                    'name': 'derp',
                    'value': 'herp'
                }
            ]
        }
        self.job_name = 'AWS-VIC-Manager'
        self.job_class = 'something_else'
        self.console_text = 'derp\n' \
                            'herp\n' \
                            'CI: cool ci\n' \
                            'hi\n'
        self.action = 'create-vic'

        self.expected_build_json = {**deepcopy(self.build), 'instance': 'Production'}
        self.expected_pull_fs_build_called = True
        self.expected_is_building_called = True

        self.do_it()

    def test_action_create_vic(self):
        self.build = {
            'derp': 'herp',
            'actions': [
                {
                    'name': 'derp',
                    'value': 'herp'
                }
            ]
        }
        self.job_name = 'AWS-VIC-Manager'
        self.job_class = 'something_else'
        self.console_text = 'derp\n' \
                            'herp\n' \
                            'CI: cool ci\n' \
                            '. Created AWS VIC \'43\' under IP 5...\n' \
                            'hi\n'
        self.action = 'create-vic'

        self.expected_build_json = {**deepcopy(self.build), 'instance': 'Production', 'vic_number': 43}
        self.expected_pull_fs_build_called = True
        self.expected_is_building_called = True

        self.do_it()


class TestGetCause(unittest.TestCase):
    def setUp(self):
        self.exporter = export.JenkinsExporter()

    def test_no_actions(self):
        event = {
            'number': 5,
            'result': 'SUCCESS'
        }

        assert self.exporter.get_cause(event, None, None, None) == 'Not Assigned'

    @patch('pivt.export_jenkins.JenkinsExporter.get_causes_event_key')
    @patch('pivt.export_jenkins.JenkinsExporter.get_project_name')
    def test_no_cause_action(self, mock_get_project, mock_get_key):
        project = 'my-project'
        number = 5

        mock_get_project.return_value = project
        mock_get_key.return_value = project + ':' + str(number)

        instance = 'Production'

        event = {
            'number': number,
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

        assert self.exporter.get_cause(event, instance, None, None) == 'Not Assigned'

    @patch('pivt.export_jenkins.JenkinsExporter.get_causes_event_key')
    @patch('pivt.export_jenkins.JenkinsExporter.get_project_name')
    def test_unknown_cause(self, mock_get_project, mock_get_key):
        project = 'my-project'
        number = 5

        mock_get_project.return_value = project
        mock_get_key.return_value = project + ':' + str(number)

        instance = 'Production'

        event = {
            'number': number,
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

        assert self.exporter.get_cause(event, instance, None, None) == 'Not Assigned'

    @patch('pivt.export_jenkins.JenkinsExporter.save_cause')
    @patch('pivt.export_jenkins.JenkinsExporter.get_causes_event_key')
    @patch('pivt.export_jenkins.JenkinsExporter.get_project_name')
    def test_event_solved(self, mock_get_project, mock_get_key, mock_save_cause):
        project = 'my-project'
        number = 5
        event_key = project + ':' + str(number)

        mock_get_project.return_value = project
        mock_get_key.return_value = event_key

        instance = 'Production'

        self.exporter.solved_causes = {
            instance: {
                event_key: 'my_cause'
            }
        }

        event = {
            'number': number,
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

        expected_cause = 'my_cause'

        assert self.exporter.get_cause(event, instance, None, None) == expected_cause
        assert mock_save_cause.called_with(event_key, expected_cause, instance)

    @patch('pivt.export_jenkins.JenkinsExporter.save_cause')
    @patch('pivt.export_jenkins.JenkinsExporter.get_causes_event_key')
    @patch('pivt.export_jenkins.JenkinsExporter.get_project_name')
    def test_user_cause(self, mock_get_project, mock_get_key, mock_save_cause):
        project = 'my-project'
        number = 5
        event_key = project + ':' + str(number)

        mock_get_project.return_value = project
        mock_get_key.return_value = event_key

        instance = 'Production'

        event = {
            'number': number,
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

        expected_cause = 'user'

        assert self.exporter.get_cause(event, instance, None, None) == expected_cause
        assert mock_save_cause.called_with(event_key, expected_cause, instance)

    @patch('pivt.export_jenkins.JenkinsExporter.save_cause')
    @patch('pivt.export_jenkins.JenkinsExporter.get_causes_event_key')
    @patch('pivt.export_jenkins.JenkinsExporter.get_project_name')
    def test_rebuild_user_cause(self, mock_get_project, mock_get_key, mock_save_cause):
        project = 'my-project'
        number = 5
        event_key = project + ':' + str(number)

        mock_get_project.return_value = project
        mock_get_key.return_value = event_key

        instance = 'Production'

        event = {
            'number': number,
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

        expected_cause = 'user'

        assert self.exporter.get_cause(event, instance, None, None) == expected_cause
        assert mock_save_cause.called_with(event_key, expected_cause, instance)

    @patch('pivt.export_jenkins.JenkinsExporter.save_cause')
    @patch('pivt.export_jenkins.JenkinsExporter.get_causes_event_key')
    @patch('pivt.export_jenkins.JenkinsExporter.get_project_name')
    def test_self_service_cause(self, mock_get_project, mock_get_key, mock_save_cause):
        project = 'my-project'
        number = 5
        event_key = project + ':' + str(number)

        mock_get_project.return_value = project
        mock_get_key.return_value = event_key

        instance = 'Production'

        event = {
            'number': number,
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

        expected_cause = 'Self-Service-Pipeline'

        assert self.exporter.get_cause(event, instance, None, None) == expected_cause
        assert mock_save_cause.called_with(event_key, expected_cause, instance)

    @patch('pivt.export_jenkins.JenkinsExporter.save_cause')
    @patch('pivt.export_jenkins.JenkinsExporter.get_causes_event_key')
    @patch('pivt.export_jenkins.JenkinsExporter.get_project_name')
    def test_nightly_cause(self, mock_get_project, mock_get_key, mock_save_cause):
        project = 'my-project'
        number = 5
        event_key = project + ':' + str(number)

        mock_get_project.return_value = project
        mock_get_key.return_value = event_key

        instance = 'Production'

        event = {
            'number': number,
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

        expected_cause = 'Nightly-Builds'

        assert self.exporter.get_cause(event, instance, None, None) == expected_cause
        assert mock_save_cause.called_with(event_key, expected_cause, instance)

    @patch('pivt.export_jenkins.JenkinsExporter.save_cause')
    @patch('pivt.export_jenkins.JenkinsExporter.get_causes_event_key')
    @patch('pivt.export_jenkins.JenkinsExporter.get_project_name')
    def test_weekly_cause(self, mock_get_project, mock_get_key, mock_save_cause):
        project = 'my-project'
        number = 5
        event_key = project + ':' + str(number)

        mock_get_project.return_value = project
        mock_get_key.return_value = event_key

        instance = 'Production'

        event = {
            'number': number,
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

        expected_cause = 'Weekly-Builds'

        assert self.exporter.get_cause(event, instance, None, None) == expected_cause
        assert mock_save_cause.called_with(event_key, expected_cause, instance)

    @patch('pivt.export_jenkins.JenkinsExporter.save_cause')
    @patch('pivt.export_jenkins.JenkinsExporter.get_causes_event_key')
    @patch('pivt.export_jenkins.JenkinsExporter.get_project_name')
    def test_upstream_cause_in_solved(self, mock_get_project, mock_get_key, mock_save_cause):
        project = 'my-project'
        number = 5
        event_key = project + ':' + str(number)

        instance = 'Production'

        upstream_project = 'ci6-Pipeline'
        upstream_build = 73
        upstream_key = upstream_project + ':' + str(upstream_build)

        self.exporter.solved_causes = {
            instance: {
                upstream_key: 'my_cause'
            }
        }

        mock_get_project.return_value = project

        def get_causes_event_key(project_name, build_number):
            return project_name + ':' + str(build_number)

        mock_get_key.side_effect = get_causes_event_key

        event = {
            'number': number,
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
                            'upstreamProject': upstream_project,
                            'upstreamBuild': upstream_build
                        }
                    ]
                },
                {
                    '_class': 'another action',
                }
            ],
            'result': 'SUCCESS'
        }

        expected_cause = 'my_cause'

        assert self.exporter.get_cause(event, instance, None, None) == expected_cause
        assert mock_save_cause.called_with(event_key, expected_cause, instance)

    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    @patch('pivt.export_jenkins.JenkinsExporter.save_cause')
    @patch('pivt.export_jenkins.JenkinsExporter.get_causes_event_key')
    @patch('pivt.export_jenkins.JenkinsExporter.get_project_name')
    def test_upstream_cause(self, mock_get_project, mock_get_key, mock_save_cause, mock_get):
        project = 'my-project'
        number = 5
        event_key = project + ':' + str(number)

        instance = 'Production'

        upstream_project = 'ci6-Pipeline'
        upstream_build = 73

        mock_get_project.return_value = project

        def get_causes_event_key(project_name, build_number):
            return project_name + ':' + str(build_number)

        mock_get_key.side_effect = get_causes_event_key

        event = {
            'number': number,
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
                            'upstreamProject': upstream_project,
                            'upstreamBuild': upstream_build,
                            'upstreamUrl': 'job/' + upstream_project
                        }
                    ]
                },
                {
                    '_class': 'another action',
                }
            ],
            'result': 'SUCCESS'
        }

        upstream_event = {
            'number': upstream_build,
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

        mock_get.return_value = json.dumps(upstream_event)

        expected_cause = 'Weekly-Builds'

        assert self.exporter.get_cause(event, instance, 'baseUrl', None) == expected_cause
        assert mock_save_cause.called_with(event_key, expected_cause, instance)
        assert mock_get.called_with('baseUrl/job/ci6-Pipeline/73/api/json', True, None)

    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    @patch('pivt.export_jenkins.JenkinsExporter.save_cause')
    @patch('pivt.export_jenkins.JenkinsExporter.get_causes_event_key')
    @patch('pivt.export_jenkins.JenkinsExporter.get_project_name')
    def test_upstream_dne(self, mock_get_project, mock_get_key, mock_save_cause, mock_get):
        project = 'my-project'
        number = 5

        instance = 'Production'

        upstream_project = 'ci6-Pipeline'
        upstream_build = 73

        mock_get_project.return_value = project

        def get_causes_event_key(project_name, build_number):
            return project_name + ':' + str(build_number)

        mock_get_key.side_effect = get_causes_event_key

        event = {
            'number': number,
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
                            'upstreamProject': upstream_project,
                            'upstreamBuild': upstream_build,
                            'upstreamUrl': 'job/' + upstream_project
                        }
                    ]
                },
                {
                    '_class': 'another action',
                }
            ],
            'result': 'SUCCESS'
        }

        mock_get.return_value = None

        expected_cause = 'Not Assigned'

        assert self.exporter.get_cause(event, instance, None, None) == expected_cause
        assert not mock_save_cause.called

    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    @patch('pivt.export_jenkins.JenkinsExporter.save_cause')
    @patch('pivt.export_jenkins.JenkinsExporter.get_causes_event_key')
    @patch('pivt.export_jenkins.JenkinsExporter.get_project_name')
    def test_multiple_upstreams_cause(self, mock_get_project, mock_get_key, mock_save_cause, mock_get):
        project = 'my-project'
        number = 5
        event_key = project + ':' + str(number)

        instance = 'Production'

        upstream1_project = 'upstream-project'
        upstream1_build = 73
        upstream1_event_key = upstream1_project + ':' + str(upstream1_build)

        upstream2_project = 'Weekly-Builds'
        upstream2_build = 43

        mock_get_project.return_value = project

        def get_causes_event_key(project_name, build_number):
            return project_name + ':' + str(build_number)

        mock_get_key.side_effect = get_causes_event_key

        event = {
            'number': number,
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
                            'upstreamProject': upstream1_project,
                            'upstreamBuild': upstream1_build,
                            'upstreamUrl': 'job/' + upstream1_project
                        }
                    ]
                },
                {
                    '_class': 'another action',
                }
            ],
            'result': 'SUCCESS',
            'fullDisplayName': project + ' ' + str(number)
        }

        upstream_event = {
            'number': upstream1_build,
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
                            'upstreamProject': upstream2_project,
                            'upstreamBuild': upstream2_build
                        }
                    ]
                },
                {
                    '_class': 'another action',
                }
            ],
            'result': 'SUCCESS',
            'fullDisplayName': upstream1_project + ' ' + str(upstream1_build)
        }

        mock_get.return_value = json.dumps(upstream_event)

        expected_cause = 'Weekly-Builds'

        assert self.exporter.get_cause(event, instance, 'baseUrl', None) == expected_cause
        assert mock_save_cause.called_with(event_key, expected_cause, instance)
        assert mock_save_cause.called_with(upstream1_event_key, expected_cause, instance)
        assert mock_get.called_with('baseUrl/job/upstream-project/73/api/json', True, None)


class TestGetCauseInt(unittest.TestCase):
    def setUp(self):
        self.exporter = export.JenkinsExporter()

    def test_no_actions(self):
        event = {
            'number': 5,
            'result': 'SUCCESS'
        }

        assert self.exporter.get_cause(event, None, None, None) == 'Not Assigned'

    def test_no_cause_action(self):
        number = 5
        instance = 'Production'

        event = {
            'number': number,
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

        assert self.exporter.get_cause(event, instance, None, None) == 'Not Assigned'
        assert self.exporter.solved_causes == {}

    def test_unknown_cause(self):
        number = 5

        instance = 'Production'

        event = {
            'number': number,
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

        assert self.exporter.get_cause(event, instance, None, None) == 'Not Assigned'
        assert self.exporter.solved_causes == {}

    def test_event_solved(self):
        project = 'my-project'
        number = 5
        event_key = project + ':' + str(number)

        instance = 'Production'

        self.exporter.solved_causes = {
            instance: {
                event_key: 'my_cause'
            }
        }

        event = {
            'number': number,
            'actions': [],
            'result': 'SUCCESS',
            'fullDisplayName': project + ' ' + str(number)
        }

        expected_cause = 'my_cause'
        expected_solved_causes = {
            instance: {
                event_key: 'my_cause'
            }
        }

        self.assertEqual(self.exporter.get_cause(event, instance, None, None), expected_cause)
        self.assertEqual(self.exporter.solved_causes, expected_solved_causes)

    def test_user_cause(self):
        project = 'my-project'
        number = 5
        event_key = project + ':' + str(number)

        instance = 'Production'

        event = {
            'number': number,
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
            'result': 'SUCCESS',
            'fullDisplayName': project + ' ' + str(number)
        }

        expected_cause = 'user'
        expected_solved_causes = {
            instance: {
                event_key: 'user'
            }
        }

        assert self.exporter.get_cause(event, instance, None, None) == expected_cause
        self.assertEqual(self.exporter.solved_causes, expected_solved_causes)

    def test_rebuild_user_cause(self):
        project = 'my-project'
        number = 5
        event_key = project + ':' + str(number)

        instance = 'Production'

        event = {
            'number': number,
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
            'result': 'SUCCESS',
            'fullDisplayName': project + ' ' + str(number)
        }

        expected_cause = 'user'
        expected_solved_causes = {
            instance: {
                event_key: 'user'
            }
        }

        assert self.exporter.get_cause(event, instance, None, None) == expected_cause
        self.assertEqual(self.exporter.solved_causes, expected_solved_causes)

    def test_self_service_cause(self):
        project = 'my-project'
        number = 5
        event_key = project + ':' + str(number)

        instance = 'Production'

        event = {
            'number': number,
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
            'result': 'SUCCESS',
            'fullDisplayName': project + ' ' + str(number)
        }

        expected_cause = 'Self-Service-Pipeline'
        expected_solved_causes = {
            instance: {
                event_key: 'Self-Service-Pipeline'
            }
        }

        assert self.exporter.get_cause(event, instance, None, None) == expected_cause
        self.assertEqual(self.exporter.solved_causes, expected_solved_causes)

    def test_nightly_cause(self):
        project = 'my-project'
        number = 5
        event_key = project + ':' + str(number)

        instance = 'Production'

        event = {
            'number': number,
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
            'result': 'SUCCESS',
            'fullDisplayName': project + ' ' + str(number)
        }

        expected_cause = 'Nightly-Builds'
        expected_solved_causes = {
            instance: {
                event_key: 'Nightly-Builds'
            }
        }

        assert self.exporter.get_cause(event, instance, None, None) == expected_cause
        self.assertEqual(self.exporter.solved_causes, expected_solved_causes)

    def test_weekly_cause(self):
        project = 'my-project'
        number = 5
        event_key = project + ':' + str(number)

        instance = 'Production'

        event = {
            'number': number,
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
            'result': 'SUCCESS',
            'fullDisplayName': project + ' ' + str(number)
        }

        expected_cause = 'Weekly-Builds'
        expected_solved_causes = {
            instance: {
                event_key: 'Weekly-Builds'
            }
        }

        assert self.exporter.get_cause(event, instance, None, None) == expected_cause
        self.assertEqual(self.exporter.solved_causes, expected_solved_causes)

    def test_upstream_cause_in_solved(self):
        project = 'my-project'
        number = 5
        event_key = project + ':' + str(number)

        instance = 'Production'

        upstream_project = 'ci6-Pipeline'
        upstream_build = 73
        upstream_key = upstream_project + ':' + str(upstream_build)

        self.exporter.solved_causes = {
            instance: {
                upstream_key: 'my_cause'
            }
        }

        event = {
            'number': number,
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
                            'upstreamProject': upstream_project,
                            'upstreamBuild': upstream_build
                        }
                    ]
                },
                {
                    '_class': 'another action',
                }
            ],
            'result': 'SUCCESS',
            'fullDisplayName': project + ' ' + str(number)
        }

        expected_cause = 'my_cause'
        expected_solved_causes = {
            instance: {
                upstream_key: 'my_cause',
                event_key: 'my_cause'
            }
        }

        assert self.exporter.get_cause(event, instance, None, None) == expected_cause
        self.assertEqual(self.exporter.solved_causes, expected_solved_causes)

    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    def test_upstream_cause(self, mock_get):
        project = 'my-project'
        number = 5
        event_key = project + ':' + str(number)

        instance = 'Production'

        upstream_project = 'Weekly-Builds'
        upstream_build = 73

        event = {
            'number': number,
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
                            'upstreamProject': upstream_project,
                            'upstreamBuild': upstream_build,
                            'upstreamUrl': 'job/' + upstream_project
                        }
                    ]
                },
                {
                    '_class': 'another action',
                }
            ],
            'result': 'SUCCESS',
            'fullDisplayName': project + ' ' + str(number)
        }

        upstream_event = {
            'number': upstream_build,
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
                            'upstreamProject': upstream_project,
                            'upstreamBuild': upstream_build
                        }
                    ]
                },
                {
                    '_class': 'another action',
                }
            ],
            'result': 'SUCCESS',
            'fullDisplayName': upstream_project + ' ' + str(upstream_build)
        }

        mock_get.return_value = json.dumps(upstream_event)

        expected_cause = 'Weekly-Builds'
        expected_solved_causes = {
            instance: {
                event_key: 'Weekly-Builds'
            }
        }

        assert self.exporter.get_cause(event, instance, 'baseUrl', None) == expected_cause
        self.assertEqual(self.exporter.solved_causes, expected_solved_causes)
        assert mock_get.called_with('baseUrl/job/ci6-Pipeline/73/api/json', True, None)

    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    def test_upstream_dne(self, mock_get):
        project = 'my-project'
        number = 5

        instance = 'Production'

        upstream_project = 'ci6-Pipeline'
        upstream_build = 73

        event = {
            'number': number,
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
                            'upstreamProject': upstream_project,
                            'upstreamBuild': upstream_build,
                            'upstreamUrl': 'job/' + upstream_project
                        }
                    ]
                },
                {
                    '_class': 'another action',
                }
            ],
            'result': 'SUCCESS',
            'fullDisplayName': project + ' ' + str(number)
        }

        mock_get.return_value = None

        expected_cause = 'Not Assigned'

        assert self.exporter.get_cause(event, instance, None, None) == expected_cause
        self.assertEqual(self.exporter.solved_causes, {})

    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    def test_multiple_upstreams_cause(self, mock_get):
        project = 'my-project'
        number = 5
        event_key = project + ':' + str(number)

        instance = 'Production'

        upstream1_project = 'upstream-project'
        upstream1_build = 73
        upstream1_event_key = upstream1_project + ':' + str(upstream1_build)

        upstream2_project = 'Weekly-Builds'
        upstream2_build = 43

        event = {
            'number': number,
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
                            'upstreamProject': upstream1_project,
                            'upstreamBuild': upstream1_build,
                            'upstreamUrl': 'job/' + upstream1_project
                        }
                    ]
                },
                {
                    '_class': 'another action',
                }
            ],
            'result': 'SUCCESS',
            'fullDisplayName': project + ' ' + str(number)
        }

        upstream_event = {
            'number': upstream1_build,
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
                            'upstreamProject': upstream2_project,
                            'upstreamBuild': upstream2_build
                        }
                    ]
                },
                {
                    '_class': 'another action',
                }
            ],
            'result': 'SUCCESS',
            'fullDisplayName': upstream1_project + ' ' + str(upstream1_build)
        }

        mock_get.return_value = json.dumps(upstream_event)

        expected_cause = 'Weekly-Builds'
        expected_solved_causes = {
            instance: {
                upstream1_event_key: 'Weekly-Builds',
                event_key: 'Weekly-Builds'
            }
        }

        assert self.exporter.get_cause(event, instance, 'baseUrl', None) == expected_cause
        self.assertEqual(self.exporter.solved_causes, expected_solved_causes)
        assert mock_get.called_with('baseUrl/job/upstream-project/73/api/json', True, None)


class TestGetProjectName(unittest.TestCase):
    def setUp(self):
        self.exporter = export.JenkinsExporter()

    def test_no_display_name_no_url(self):
        event = {'derp': 'herp'}
        project_name = self.exporter.get_project_name(event)
        assert not project_name

    def test_display_name(self):
        event = {'derp': 'herp', 'fullDisplayName': 'hi 2'}
        project_name = self.exporter.get_project_name(event)
        assert project_name == 'hi'

    def test_just_url(self):
        event = {'derp': 'herp', 'url': 'this/is/my/cool/url'}
        project_name = self.exporter.get_project_name(event)
        assert project_name == 'my'

    def test_both(self):
        event = {'derp': 'herp', 'url': 'this/is/my/cool/url', 'fullDisplayName': 'hi 2'}
        project_name = self.exporter.get_project_name(event)
        assert project_name == 'hi'


class TestSaveCause(unittest.TestCase):
    def setUp(self):
        self.exporter = export.JenkinsExporter()

    def test_empty(self):
        self.assertEqual(self.exporter.solved_causes, {})

        self.exporter.save_cause('ci3-Build:5', 'Nightly', 'Production')

        expected = {
            'Production': {
                'ci3-Build:5': 'Nightly'
            }
        }
        self.assertEqual(self.exporter.solved_causes, expected)

    def test_not_empty_different_instance_different_project(self):
        self.exporter.solved_causes = {
            'Development': {
                'derp': 'herp'
            }
        }

        self.exporter.save_cause('ci3-Build:5', 'Nightly', 'Production')

        expected = {
            'Production': {
                'ci3-Build:5': 'Nightly'
            },
            'Development': {
                'derp': 'herp'
            }
        }
        self.assertEqual(self.exporter.solved_causes, expected)

    def test_not_empty_same_instance_different_project(self):
        self.exporter.solved_causes = {
            'Production': {
                'derp': 'herp'
            }
        }

        self.exporter.save_cause('ci3-Build:5', 'Nightly', 'Production')

        expected = {
            'Production': {
                'ci3-Build:5': 'Nightly',
                'derp': 'herp'
            }
        }
        self.assertEqual(self.exporter.solved_causes, expected)


class TestGetCausesEventKey(unittest.TestCase):
    def test(self):
        self.assertEqual(export.JenkinsExporter().get_causes_event_key('ci3-Build', 5), 'ci3-Build:5')


class TestParsePipelineProperties(unittest.TestCase):
    def setUp(self):
        self.exporter = export.JenkinsExporter()

        self.build_json = {'number': 5}
        self.properties = ''

        self.expected_props = {}

    def do_it(self):
        actual_props = self.exporter.parse_pipeline_properties(self.properties, self.build_json)
        self.assertEqual(self.expected_props, actual_props)

    def test_non_string_properties(self):
        self.properties = []

        self.expected_props = {}

        self.do_it()

    def test_empty_properties(self):
        self.expected_props = {}

        self.do_it()

    def test_duplicates(self):
        self.properties = """derp=herp\nhello=hola\nderp=lerp"""

        self.expected_props = {'derp': 'lerp', 'hello': 'hola'}

        self.do_it()

    def test(self):
        self.properties = """derp=herp\nhello=hola"""

        self.expected_props = {'derp': 'herp', 'hello': 'hola'}

        self.do_it()


class TestPullOneFile(unittest.TestCase):
    def setUp(self):
        self.exporter = export.JenkinsExporter()

        self.artifacts = None
        self.build_json = {}
        self.metrics = {'requests': 0, 'bytes_pulled': 0}
        self.filename = 'cool_file.txt'
        self.default = ''

        self.expected_content = ''
        self.expected_requests = 0
        self.expected_bytes_pulled = 0

    def pull_artifact(self, _, relative_path, metrics):
        assert isinstance(relative_path, str)
        if relative_path in self.artifacts:
            metrics['requests'] += 1
            metrics['bytes_pulled'] += 1000
            return self.artifacts[relative_path]['artifact']
        return None

    def build_build_json(self):
        if self.artifacts is None:
            return

        self.build_json['artifacts'] = []

        self.artifacts = OrderedDict(sorted(self.artifacts.items()))
        for relative_path, artifact in self.artifacts.items():
            item = artifact['attrs']
            item['relativePath'] = relative_path
            self.build_json['artifacts'].append(item)

    def do_it(self):
        self.build_build_json()
        with patch.object(export.JenkinsExporter, 'pull_artifact') as mock_pull_artifact:
            self.set_mocks(mock_pull_artifact)
            actual_content = self.exporter.pull_one_file(self.filename, self.build_json, '', self.metrics, self.default)
            self.make_asserts(actual_content)

    def set_mocks(self, mock_pull_artifact):
        mock_pull_artifact.side_effect = self.pull_artifact

    def make_asserts(self, actual_content):
        self.assertEqual(self.expected_content, actual_content)
        self.assertEqual(self.expected_requests, self.metrics['requests'])
        self.assertEqual(self.expected_bytes_pulled, self.metrics['bytes_pulled'])

    def test_no_artifacts(self):
        self.do_it()

    def test_empty_artifacts(self):
        self.artifacts = {}
        self.do_it()

    def test_no_file(self):
        self.artifacts = {
            'path/something.txt': {
                'artifact': 'something',
                'attrs': {
                    'derp': 'herp',
                    'fileName': 'something.txt'
                }
            },
            'path/something2.json': {
                'artifact': 'something2',
                'attrs': {
                    'herp': 'derp',
                    'fileName': 'something2.json'
                }
            }
        }

        self.do_it()

    def test_one_file(self):
        self.artifacts = {
            'path/something.txt': {
                'artifact': 'something',
                'attrs': {
                    'derp': 'herp',
                    'fileName': 'something.txt'
                }
            },
            'path/cool_file.txt': {
                'artifact': 'cool_stuff',
                'attrs': {
                    'herp': 'derp',
                    'fileName': 'cool_file.txt'
                }
            }
        }

        self.expected_content = 'cool_stuff'
        self.expected_requests = 1
        self.expected_bytes_pulled = 1000

        self.do_it()

    def test_multiple_files(self):
        self.artifacts = {
            'path/cool_file.txt': {
                'artifact': 'cool_stuff1',
                'attrs': {
                    'derp': 'herp',
                    'fileName': 'cool_file.txt'
                }
            },
            'path2/cool_file.txt': {
                'artifact': 'cool_stuff2',
                'attrs': {
                    'herp': 'derp',
                    'fileName': 'cool_file.txt'
                }
            }
        }

        self.expected_content = 'cool_stuff1'
        self.expected_requests = 1
        self.expected_bytes_pulled = 1000

        self.do_it()


class TestPullFt(unittest.TestCase):
    def setUp(self):
        self.exporter = export.JenkinsExporter()

        self.reports = {}
        self.triggered_builds = {}
        self.build_json = None
        self.metrics = {'requests': 0, 'bytes_pulled': 0}

        self.expected_reports = {}
        self.expected_requests = 0
        self.expected_bytes_pulled = 0

    def build_build_json(self):
        artifacts = []
        for relative_path, report in self.reports.items():
            artifacts.append({'report': report, 'relativePath': relative_path})
        triggered_builds = list(self.triggered_builds.keys())
        self.build_json = {
            'artifacts': artifacts,
            'actions': [{'triggeredBuilds': triggered_builds}]
        }

    def pull_artifact(self, _, relative_path, metrics):
        assert isinstance(relative_path, str)
        if relative_path in self.reports:
            metrics['requests'] += 1
            metrics['bytes_pulled'] += 1000
            return self.reports[relative_path]
        return None

    def pull_ft_triggered_build(self, triggered_build, metrics):
        reports = {}
        if triggered_build in self.triggered_builds:
            metrics['requests'] += 1
            metrics['bytes_pulled'] += 1000
            for report in self.triggered_builds[triggered_build]:
                reports[report['url']] = report['report']
        return reports

    def do_it(self):
        if self.build_json is None:
            self.build_build_json()
        with patch.object(export.JenkinsExporter, 'pull_ft_report_artifact') as mock_pull_artifact, \
                patch.object(export.JenkinsExporter, 'pull_ft_triggered_build') as mock_pull_ft_triggered_build:
            self.set_mocks(mock_pull_artifact, mock_pull_ft_triggered_build)
            actual_reports = self.exporter.pull_ft(self.build_json, '', self.metrics)
            self.make_asserts(actual_reports)

    def set_mocks(self, mock_pull_artifact, mock_pull_ft_triggered_build):
        mock_pull_artifact.side_effect = self.pull_artifact
        mock_pull_ft_triggered_build.side_effect = self.pull_ft_triggered_build

    def make_asserts(self, actual_reports):
        self.assertEqual(self.expected_reports, actual_reports)
        self.assertEqual(self.expected_requests, self.metrics['requests'])
        self.assertEqual(self.expected_bytes_pulled, self.metrics['bytes_pulled'])

    def test_empty(self):
        self.do_it()

    def test_one_artifact_non_report(self):
        self.build_json = {
            'artifacts': [
                {}
            ],
            'actions': []
        }

        self.do_it()

    def test_one_artifact(self):
        self.reports = {
            'relative/path': {'name': 'derp'}
        }

        self.expected_reports = {'relative/path': {'name': 'derp'}}
        self.expected_requests = 1
        self.expected_bytes_pulled = 1000

        self.do_it()

    def test_two_same_artifacts(self):
        self.reports = {
            'relative/path1': {'name': 'derp'}
        }

        self.build_json = {
            'artifacts': [
                {
                    'report': {'name': 'derp'},
                    'relativePath': 'relative/path1'
                },
                {
                    'report': {'name': 'derp'},
                    'relativePath': 'relative/path1'
                }
            ],
            'actions': []
        }

        self.expected_reports = {
            'relative/path1': {'name': 'derp'}
        }
        self.expected_requests = 2
        self.expected_bytes_pulled = 2000

        self.do_it()

    def test_two_artifacts(self):
        self.reports = {
            'relative/path1': {'name': 'derp'},
            'relative/path2': {'name': 'herp'}
        }

        self.expected_reports = {
            'relative/path1': {'name': 'derp'},
            'relative/path2': {'name': 'herp'}
        }
        self.expected_requests = 2
        self.expected_bytes_pulled = 2000

        self.do_it()

    def test_no_triggered_builds(self):
        self.build_json = {
            'artifacts': [],
            'actions': [{'derp': 'herp'}]
        }

        self.expected_reports = {}
        self.expected_requests = 0
        self.expected_bytes_pulled = 0

        self.do_it()

    def test_empty_triggered_builds(self):
        self.expected_reports = {}
        self.expected_requests = 0
        self.expected_bytes_pulled = 0

        self.do_it()

    def test_one_empty_triggered_build(self):
        self.triggered_builds = {
            1: []
        }

        self.expected_reports = {}
        self.expected_requests = 1
        self.expected_bytes_pulled = 1000

        self.do_it()

    def test_one_triggered_build(self):
        self.triggered_builds = {
            1: [
                {
                    'report': {'name': 'derp'},
                    'url': 'path/to/report'
                }
            ]
        }

        self.expected_reports = {'path/to/report': {'name': 'derp'}}
        self.expected_requests = 1
        self.expected_bytes_pulled = 1000

        self.do_it()

    def test_one_triggered_build_two_same_artifacts(self):
        self.triggered_builds = {
            1: [
                {
                    'report': {'name': 'derp'},
                    'url': 'path/to/report'
                },
                {
                    'report': {'name': 'derp'},
                    'url': 'path/to/report'
                }
            ]
        }

        self.expected_reports = {'path/to/report': {'name': 'derp'}}
        self.expected_requests = 1
        self.expected_bytes_pulled = 1000

        self.do_it()

    def test_one_triggered_build_two_artifacts(self):
        self.triggered_builds = {
            1: [
                {
                    'report': {'name': 'derp'},
                    'url': 'path/to/report1'
                },
                {
                    'report': {'name': 'herp'},
                    'url': 'path/to/report2'
                }
            ]
        }

        self.expected_reports = {
            'path/to/report1': {'name': 'derp'},
            'path/to/report2': {'name': 'herp'}
        }
        self.expected_requests = 1
        self.expected_bytes_pulled = 1000

        self.do_it()

    def test_two_same_triggered_builds(self):
        self.triggered_builds = {
            1: [
                {
                    'report': {'name': 'derp'},
                    'url': 'path/to/report'
                }
            ],
            2: [
                {
                    'report': {'name': 'derp'},
                    'url': 'path/to/report'
                }
            ]
        }

        self.expected_reports = {'path/to/report': {'name': 'derp'}}
        self.expected_requests = 2
        self.expected_bytes_pulled = 2000

        self.do_it()

    def test_two_triggered_builds(self):
        self.triggered_builds = {
            1: [
                {
                    'report': {'name': 'derp'},
                    'url': 'path/to/report1'
                }
            ],
            2: [
                {
                    'report': {'name': 'herp'},
                    'url': 'path/to/report2'
                }
            ]
        }

        self.expected_reports = {
            'path/to/report1': {'name': 'derp'},
            'path/to/report2': {'name': 'herp'}
        }
        self.expected_requests = 2
        self.expected_bytes_pulled = 2000

        self.do_it()

    def test_artifact_same_triggered_build(self):
        self.reports = {
            'path/to/report': {'name': 'derp'}
        }

        self.triggered_builds = {
            1: [
                {
                    'report': {'name': 'derp'},
                    'url': 'path/to/report'
                }
            ]
        }

        self.expected_reports = {'path/to/report': {'name': 'derp'}}
        self.expected_requests = 2
        self.expected_bytes_pulled = 2000

        self.do_it()

    def test_artifact_triggered_build(self):
        self.reports = {
            'path/to/report1': {'name': 'derp'}
        }

        self.triggered_builds = {
            1: [
                {
                    'report': {'name': 'herp'},
                    'url': 'path/to/report2'
                }
            ]
        }

        self.expected_reports = {
            'path/to/report1': {'name': 'derp'},
            'path/to/report2': {'name': 'herp'}
        }
        self.expected_requests = 2
        self.expected_bytes_pulled = 2000

        self.do_it()


# TODO: update with do_it
class TestPullFtReportArtifact(unittest.TestCase):
    def setUp(self):
        self.exporter = export.JenkinsExporter()

    @patch('pivt.export_jenkins.JenkinsExporter.pull_artifact')
    def test_no_report(self, mock_pull_artifact):
        relative_path = ''
        metrics = {'requests': 0, 'bytes_pulled': 0}

        mock_pull_artifact.return_value = None

        report = self.exporter.pull_ft_report_artifact('', relative_path, metrics)

        assert not report
        assert metrics['requests'] == 0
        assert metrics['bytes_pulled'] == 0

    @patch('pivt.export_jenkins.JenkinsExporter.pull_artifact')
    def test_no_report_2(self, mock_pull_artifact):
        relative_path = 'not-report.json'
        metrics = {'requests': 0, 'bytes_pulled': 0}

        mock_pull_artifact.return_value = None

        report = self.exporter.pull_ft_report_artifact('', relative_path, metrics)

        assert not report
        assert metrics['requests'] == 0
        assert metrics['bytes_pulled'] == 0

    @patch('pivt.export_jenkins.JenkinsExporter.pull_artifact')
    def test_not_report(self, mock_pull_artifact):
        relative_path = 'not-report.json'
        metrics = {'requests': 0, 'bytes_pulled': 0}

        def side_effect(*args):
            args[2]['requests'] += 1
            args[2]['bytes_pulled'] += 1000
            return 'not a report'

        mock_pull_artifact.side_effect = side_effect

        report = self.exporter.pull_ft_report_artifact('', relative_path, metrics)

        assert not report
        assert metrics['requests'] == 1
        assert metrics['bytes_pulled'] == 1000

    @patch('pivt.export_jenkins.JenkinsExporter.pull_artifact')
    def test_report(self, mock_pull_artifact):
        relative_path = 'reports/report.json'
        metrics = {'requests': 0, 'bytes_pulled': 0}

        def side_effect(*args):
            args[2]['requests'] += 1
            args[2]['bytes_pulled'] += 1000
            return json.dumps({'name': 'derp'})
        mock_pull_artifact.side_effect = side_effect

        report = self.exporter.pull_ft_report_artifact('build', relative_path, metrics)

        assert report == {'name': 'derp'}
        assert metrics['requests'] == 1
        assert metrics['bytes_pulled'] == 1000


class TestPullArtifact(unittest.TestCase):
    def test(self):
        build_url = 'build/url'
        relative_path = 'relative/path'

        def get(*args):
            return args[0]

        with patch.object(export.JenkinsExporter, 'get_text_from_request') as mock_get:
            mock_get.side_effect = get
            actual = export.JenkinsExporter().pull_artifact(build_url, relative_path, None)

        expected = build_url + '/artifact/' + relative_path

        self.assertEqual(expected, actual)


class TestPullFtTriggeredBuild(unittest.TestCase):
    def setUp(self):
        self.exporter = export.JenkinsExporter()

        self.triggered_build = None
        self.metrics = {'requests': 0, 'bytes_pulled': 0}
        self.artifacts = None
        self.reports = {}

        self.expected_reports = {}
        self.expected_requests = 0
        self.expected_bytes_pulled = 0

    def get_text_from_request(self, request, show_warning, metrics):
        if self.artifacts is None:
            return None
        metrics['requests'] += 1
        metrics['bytes_pulled'] += 1000
        return json.dumps({'artifacts': self.artifacts})

    def pull_artifact(self, _, relative_path, metrics):
        assert isinstance(relative_path, str)
        if relative_path in self.reports:
            metrics['requests'] += 1
            metrics['bytes_pulled'] += 1000
            return self.reports[relative_path]
        return None

    def do_it(self):
        if self.artifacts is not None:
            for artifact in self.artifacts:
                self.reports[artifact['relativePath']] = artifact['report']
        with patch.object(export.JenkinsExporter, 'get_text_from_request') as mock_get, \
                patch.object(export.JenkinsExporter, 'pull_ft_report_artifact') as mock_pul_artifact:
            self.set_mocks(mock_get, mock_pul_artifact)
            actual_reports = self.exporter.pull_ft_triggered_build(self.triggered_build, self.metrics)
            self.make_asserts(actual_reports)

    def set_mocks(self, mock_get, mock_pull_artifact):
        mock_get.side_effect = self.get_text_from_request
        mock_pull_artifact.side_effect = self.pull_artifact

    def make_asserts(self, actual_reports):
        self.assertEqual(self.expected_reports, actual_reports)
        self.assertEqual(self.expected_requests, self.metrics['requests'])
        self.assertEqual(self.expected_bytes_pulled, self.metrics['bytes_pulled'])

    def test_no_build(self):
        self.do_it()

    def test_empty_build(self):
        self.triggered_build = {}

        self.do_it()

    def test_no_url(self):
        self.triggered_build = {'derp': 'herp'}

        self.do_it()

    def test_no_text(self):
        self.triggered_build = {'url': 'path/to/build'}

        self.do_it()

    def test_empty_artifacts(self):
        self.triggered_build = {'url': 'path/to/build'}

        self.artifacts = []

        self.expected_requests = 1
        self.expected_bytes_pulled = 1000

        self.do_it()

    def test_one_artifact(self):
        self.triggered_build = {'url': 'path/to/build'}

        self.artifacts = [
            {
                'report': {'name': 'derp'},
                'relativePath': 'path/to/report'
            }
        ]

        self.expected_reports = {'path/to/report': {'name': 'derp'}}
        self.expected_requests = 2
        self.expected_bytes_pulled = 2000

        self.do_it()

    def test_two_same_artifacts(self):
        self.triggered_build = {'url': 'path/to/build'}

        self.artifacts = [
            {
                'report': {'name': 'derp'},
                'relativePath': 'path/to/report'
            },
            {
                'report': {'name': 'derp'},
                'relativePath': 'path/to/report'
            }
        ]

        self.expected_reports = {'path/to/report': {'name': 'derp'}}
        self.expected_requests = 3
        self.expected_bytes_pulled = 3000

        self.do_it()

    def test_two_artifacts(self):
        self.triggered_build = {'url': 'path/to/build'}

        self.artifacts = [
            {
                'report': {'name': 'derp'},
                'relativePath': 'path/to/report1'
            },
            {
                'report': {'name': 'herp'},
                'relativePath': 'path/to/report2'
            }
        ]

        self.expected_reports = {
            'path/to/report1': {'name': 'derp'},
            'path/to/report2': {'name': 'herp'}
        }
        self.expected_requests = 3
        self.expected_bytes_pulled = 3000

        self.do_it()


class TestPullUt(unittest.TestCase):
    def setUp(self):
        self.exporter = export.JenkinsExporter()

    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    def test_report(self, mock_get_text_from_request):
        metrics = {'requests': 0, 'bytes_pulled': 0}

        pulled_report = {'name': 'derp'}

        def side_effect(*args):
            args[2]['requests'] += 1
            args[2]['bytes_pulled'] += 1000
            return json.dumps(pulled_report)
        mock_get_text_from_request.side_effect = side_effect

        report = self.exporter.pull_ut('', '', metrics)

        assert report == {'name': 'derp'}
        assert metrics['requests'] == 1
        assert metrics['bytes_pulled'] == 1000

    @patch('pivt.export_jenkins.JenkinsExporter.pull_ut_subprojects')
    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    def test_no_report(self, mock_get_text_from_request, mock_pull_ut_subprojects):
        metrics = {'requests': 0, 'bytes_pulled': 0}

        mock_get_text_from_request.return_value = None

        pulled_report = {'name': 'derp'}

        def side_effect(*args):
            args[2]['requests'] += 1
            args[2]['bytes_pulled'] += 1000
            return pulled_report
        mock_pull_ut_subprojects.side_effect = side_effect

        report = self.exporter.pull_ut('', '', metrics)

        assert report == {'name': 'derp'}
        assert metrics['requests'] == 1
        assert metrics['bytes_pulled'] == 1000


class TestPullUtSubprojects(unittest.TestCase):
    def setUp(self):
        self.exporter = export.JenkinsExporter()

    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    def test_no_console_text(self, mock_get_text_from_request):
        metrics = {'requests': 0, 'bytes_pulled': 0}
        mock_get_text_from_request.return_value = None

        report = self.exporter.pull_ut_subprojects('', '', metrics)

        assert not report
        assert metrics['requests'] == 0
        assert metrics['bytes_pulled'] == 0

    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    def test_no_subprojects(self, mock_get_text_from_request):
        metrics = {'requests': 0, 'bytes_pulled': 0}
        mock_get_text_from_request.return_value = ''

        report = self.exporter.pull_ut_subprojects('', '', metrics)

        assert not report
        assert metrics['requests'] == 0
        assert metrics['bytes_pulled'] == 0

    @patch('pivt.export_jenkins.JenkinsExporter.pull_ut_report_from_subproject')
    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    def test_report_no_duration(self, mock_get_text_from_request, mock_pull_ut_report_from_subproject):
        metrics = {'requests': 0, 'bytes_pulled': 0}

        def side_effect_get(*args):
            args[2]['requests'] += 1
            args[2]['bytes_pulled'] += 1000
            text = '\nsubp #1 completed.'
            return text

        mock_get_text_from_request.side_effect = side_effect_get

        def side_effect_report(*args):
            args[3]['requests'] += 1
            args[3]['bytes_pulled'] += 1000

        mock_pull_ut_report_from_subproject.side_effect = side_effect_report

        report = self.exporter.pull_ut_subprojects('', '', metrics)

        assert not report
        assert metrics['requests'] == 2
        assert metrics['bytes_pulled'] == 2000

    @patch('pivt.export_jenkins.JenkinsExporter.pull_ut_report_from_subproject')
    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    def test_report(self, mock_get_text_from_request, mock_pull_ut_report_from_subproject):
        metrics = {'requests': 0, 'bytes_pulled': 0}

        subprojects = [
            {
                'name': 'subp',
                'number': 1
            },
            {
                'name': 'subp',
                'number': 2
            }
        ]

        reports = {
            'subp1': {
                'duration': 5
            },
            'subp2': {
                'duration': 6
            }
        }

        def side_effect_get(*args):
            args[2]['requests'] += 1
            args[2]['bytes_pulled'] += 1000
            text = ''
            for subproject in subprojects:
                text += '\n{0} #{1} completed.'.format(subproject['name'], subproject['number'])
            return text

        mock_get_text_from_request.side_effect = side_effect_get

        def side_effect_report(*args):
            args[3]['requests'] += 1
            args[3]['bytes_pulled'] += 1000
            subproject = args[0]
            name = subproject[0]
            number = subproject[1]
            my_report = reports['{0}{1}'.format(name, number)]
            args[1]['duration'] += my_report['duration']

        mock_pull_ut_report_from_subproject.side_effect = side_effect_report

        report = self.exporter.pull_ut_subprojects('', '', metrics)

        assert report['duration'] == 11
        assert metrics['requests'] == 3
        assert metrics['bytes_pulled'] == 3000


class TestPullUtReportFromSubproject(unittest.TestCase):
    def setUp(self):
        self.exporter = export.JenkinsExporter()

    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    def test_no_sub_report(self, mock_get_text_from_request):
        report = {'duration': 0, 'failCount': 0, 'passCount': 0, 'skipCount': 0, 'suites': []}
        metrics = {'requests': 0, 'bytes_pulled': 0}

        mock_get_text_from_request.return_value = None

        self.exporter.pull_ut_report_from_subproject(['', ''], report, '', metrics)

        assert report == {'duration': 0, 'failCount': 0, 'passCount': 0, 'skipCount': 0, 'suites': []}
        assert metrics['requests'] == 0
        assert metrics['bytes_pulled'] == 0

    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    def test_first_sub_report(self, mock_get_text_from_request):
        report = {'duration': 0, 'failCount': 0, 'passCount': 0, 'skipCount': 0, 'suites': []}
        metrics = {'requests': 0, 'bytes_pulled': 0}

        sub_report = {'duration': 1, 'failCount': 2, 'passCount': 3, 'skipCount': 4, 'suites': ['derp', 'herp']}

        def side_effect(*args):
            args[2]['requests'] += 1
            args[2]['bytes_pulled'] += 1000
            return json.dumps(sub_report)

        mock_get_text_from_request.side_effect = side_effect

        self.exporter.pull_ut_report_from_subproject(['', ''], report, '', metrics)

        assert report == sub_report
        assert metrics['requests'] == 1
        assert metrics['bytes_pulled'] == 1000

    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    def test_second_sub_report(self, mock_get_text_from_request):
        report = {'duration': 10, 'failCount': 9, 'passCount': 8, 'skipCount': 7, 'suites': ['hi', 'hello']}
        metrics = {'requests': 0, 'bytes_pulled': 0}

        sub_report = {'duration': 1, 'failCount': 2, 'passCount': 3, 'skipCount': 4, 'suites': ['derp', 'herp']}

        def side_effect(*args):
            args[2]['requests'] += 1
            args[2]['bytes_pulled'] += 1000
            return json.dumps(sub_report)

        mock_get_text_from_request.side_effect = side_effect

        self.exporter.pull_ut_report_from_subproject(['', ''], report, '', metrics)

        assert report == {'duration': 11, 'failCount': 11, 'passCount': 11, 'skipCount': 11, 'suites': ['hi', 'hello', 'derp', 'herp']}
        assert metrics['requests'] == 1
        assert metrics['bytes_pulled'] == 1000


class TestPullFreestyleBuild(unittest.TestCase):
    build_url = 'url'
    request = build_url + '/api/json?depth=1'

    def setUp(self):
        self.exporter = export.JenkinsExporter()

        self.build = None

        self.expected_build_json = None

    def do_it(self):
        with patch.object(export.JenkinsExporter, 'get_text_from_request') as mock_get:
            self.set_mocks(mock_get)
            build_json = self.exporter.pull_freestyle_build(self.build_url, None)
            self.make_asserts(build_json, mock_get)

    def set_mocks(self, mock_get):
        build_text = None
        if self.build:
            build_text = json.dumps(self.build)
        mock_get.return_value = build_text

    def make_asserts(self, build_json, mock_get):
        self.assertEqual(self.expected_build_json, build_json)
        mock_get.assert_called_once_with(self.request, True, None)

    def test_no_build_text(self):
        self.do_it()

    def test(self):
        self.build = {
            'derp': 'herp',
        }

        self.expected_build_json = {
            'derp': 'herp'
        }

        self.do_it()


class TestPullWorkflowBuild(unittest.TestCase):
    build_url = 'url'
    file_name = 'fname'
    base_url = 'burl'
    request = build_url + '/wfapi'

    def setUp(self):
        self.exporter = export.JenkinsExporter()

        self.build = None
        self.building = False
        self.new_stages = {}

        self.expected_build_json = None
        self.expected_is_building_called = False
        self.expected_add_to_unpulled_called = False
        self.expected_pull_stage_call_count = 0

    def pull_stage(self, *args):
        stage = args[0]
        return self.new_stages[stage]

    def do_it(self):
        with patch.object(export.JenkinsExporter, 'get_text_from_request') as mock_get, \
                patch.object(export.JenkinsExporter, 'is_building') as mock_is_building, \
                patch.object(export.JenkinsExporter, 'add_to_unpulled') as mock_add_to_unpulled, \
                patch.object(export.JenkinsExporter, 'pull_workflow_build_stage') as mock_pull_stage:
            self.set_mocks(mock_get, mock_is_building, mock_pull_stage)
            build_json = self.exporter.pull_workflow_build(self.build_url, self.file_name, self.base_url, None)
            self.make_asserts(build_json, mock_get, mock_is_building, mock_add_to_unpulled, mock_pull_stage)

    def set_mocks(self, mock_get, mock_is_building, mock_pull_stage):
        build_text = None
        if self.build:
            build_text = json.dumps(self.build)
        mock_get.return_value = build_text

        mock_is_building.return_value = self.building
        mock_pull_stage.side_effect = self.pull_stage

    def make_asserts(self, build_json, mock_get, mock_is_building, mock_add_to_unpulled, mock_pull_stage):
        self.assertEqual(self.expected_build_json, build_json)
        mock_get.assert_called_once_with(self.request, True, None)
        self.assertEqual(self.expected_is_building_called, mock_is_building.called)
        self.assertEqual(self.expected_add_to_unpulled_called, mock_add_to_unpulled.called)
        self.assertEqual(self.expected_pull_stage_call_count, mock_pull_stage.call_count)

    def test_no_build_text(self):
        self.do_it()

    def test_building(self):
        self.build = {'derp': 'herp'}
        self.building = True

        self.expected_is_building_called = True
        self.expected_add_to_unpulled_called = True

        self.do_it()

    def test(self):
        self.build = {
            'derp': 'herp',
            'startTimeMillis': 5,
            'stages': [
                'stage1',
                'stage2'
            ]
        }

        self.new_stages = {
            'stage1': 'new_stage1',
            'stage2': 'new_stage2'
        }

        self.expected_build_json = {
            'derp': 'herp',
            'startTimeMillis': 5,
            'stages': [
                'new_stage1',
                'new_stage2'
            ],
            'timestamp': 5
        }

        self.expected_is_building_called = True
        self.expected_pull_stage_call_count = 2

        self.do_it()


class TestPullWorkflowBuildStage(unittest.TestCase):
    base_url = 'burl'
    stage_url = 'surl'
    request = base_url + '/' + stage_url

    def setUp(self):
        self.exporter = export.JenkinsExporter()

    @staticmethod
    def set_mocks(new_stage, mock_get):
        stage_text = None
        if new_stage:
            stage_text = json.dumps(new_stage)
        mock_get.return_value = stage_text

    def make_asserts(self, expected_stage, stage, mock_get=None):
        self.assertEqual(expected_stage, stage)

        if mock_get:
            mock_get.assert_called_once_with(self.request, True, None)

    def test_no_link(self):
        old_stage = {}
        stage = self.exporter.pull_workflow_build_stage(old_stage, self.base_url, None)
        self.make_asserts(old_stage, stage)

    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    def test_no_stage_text(self, mock_get):
        old_stage = {'_links': {'self': {'href': self.stage_url}}}
        new_stage = None

        self.set_mocks(new_stage, mock_get)

        stage = self.exporter.pull_workflow_build_stage(old_stage, self.base_url, None)

        self.make_asserts(old_stage, stage, mock_get=mock_get)

    @patch('pivt.export_jenkins.JenkinsExporter.pull_stage_flow_node')
    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    def test(self, mock_get, mock_pull_node):
        old_stage = {'_links': {'self': {'href': self.stage_url}}}
        new_stage = {
            **old_stage,
            **{
                'stageFlowNodes': ['1', '2']
            }
        }

        self.set_mocks(new_stage, mock_get)

        stage = self.exporter.pull_workflow_build_stage(old_stage, self.base_url, None)

        self.make_asserts(new_stage, stage, mock_get=mock_get)
        mock_pull_node.assert_has_calls([call('1', self.base_url, None), call('2', self.base_url, None)])


class TestPullStageFlowNode(unittest.TestCase):
    base_url = 'burl'
    log_url = 'lurl'
    request = base_url + '/' + log_url
    log_text = 'some text'

    def setUp(self):
        self.exporter = export.JenkinsExporter()

    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    def test_no_url(self, mock_get):
        original_node = {}
        expected_node = {}

        self.exporter.pull_stage_flow_node(original_node, self.base_url, None)

        self.assertEqual(expected_node, original_node)
        mock_get.assert_not_called()

    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    def test_no_log_text(self, mock_get):
        original_node = {'_links': {'log': {'href': self.log_url}}}
        expected_node = deepcopy(original_node)

        mock_get.return_value = None

        self.exporter.pull_stage_flow_node(original_node, self.base_url, None)

        self.assertEqual(expected_node, original_node)
        mock_get.assert_called_once_with(self.request, False, None)

    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    def test_no_text_in_node_log_json(self, mock_get):
        original_node = {'_links': {'log': {'href': self.log_url}}}
        expected_node = deepcopy(original_node)

        mock_get.return_value = json.dumps({
            'something': 'else'
        })

        self.exporter.pull_stage_flow_node(original_node, self.base_url, None)

        self.assertEqual(expected_node, original_node)
        mock_get.assert_called_once_with(self.request, False, None)

    @patch('pivt.export_jenkins.JenkinsExporter.get_text_from_request')
    def test(self, mock_get):
        original_node = {'_links': {'log': {'href': self.log_url}}}
        expected_node = {
            **deepcopy(original_node),
            **{'log': self.log_text}
        }

        mock_get.return_value = json.dumps({
            'text': self.log_text
        })

        self.exporter.pull_stage_flow_node(original_node, self.base_url, None)

        self.assertEqual(expected_node, original_node)
        mock_get.assert_called_once_with(self.request, False, None)


class TestIsBuilding(unittest.TestCase):
    def setUp(self):
        self.exporter = export.JenkinsExporter()

    def test_building_field_not_in_build(self):
        build = {'herp': 'derp'}
        building = self.exporter.is_building(build, 'building', True)
        self.assertFalse(building)

    def test_building_field_in_build_not_building(self):
        build = {'herp': 'derp', 'building': False}
        building = self.exporter.is_building(build, 'building', True)
        self.assertFalse(building)

    def test_building(self):
        build = {'herp': 'derp', 'building': True}

        building = self.exporter.is_building(build, 'building', True)
        self.assertTrue(building)

    def test_one_building_different_building_field(self):
        build = {'herp': 'derp', 'status': 'IN_PROGRESS'}

        building = self.exporter.is_building(build, 'status', 'IN_PROGRESS')
        self.assertTrue(building)


class TestAddToUnpulled(unittest.TestCase):
    build_url1 = 'burl1'
    file_name1 = 'fname1'
    build_url2 = 'burl2'
    file_name2 = 'fname2'

    def setUp(self):
        self.exporter = export.JenkinsExporter()

    def test_no_builds_exist(self):
        self.exporter.add_to_unpulled(self.file_name1, self.build_url1)

        expected_unpulled_builds = {
            self.file_name1: [self.build_url1]
        }

        self.assertEqual(expected_unpulled_builds, self.exporter.unpulled_builds)

    def test_one_building_build_already_exists(self):
        self.exporter.unpulled_builds = {
            self.file_name1: [self.build_url1]
        }

        self.exporter.add_to_unpulled(self.file_name1, self.build_url1)

        expected_unpulled_builds = {
            self.file_name1: [self.build_url1]
        }

        self.assertEqual(expected_unpulled_builds, self.exporter.unpulled_builds)

    def test_one_building_file_already_exists(self):
        self.exporter.unpulled_builds = {
            self.file_name1: [self.build_url1]
        }

        self.exporter.add_to_unpulled(self.file_name1, self.build_url2)

        expected_unpulled_builds = {
            self.file_name1: [self.build_url1, self.build_url2]
        }

        self.assertEqual(expected_unpulled_builds, self.exporter.unpulled_builds)

    def test_two_building_same_file(self):
        self.exporter.add_to_unpulled(self.file_name1, self.build_url1)
        self.exporter.add_to_unpulled(self.file_name1, self.build_url2)

        expected_unpulled_builds = {
            self.file_name1: [self.build_url1, self.build_url2]
        }

        self.assertEqual(expected_unpulled_builds, self.exporter.unpulled_builds)

    def test_two_building_different_file(self):
        self.exporter.add_to_unpulled(self.file_name1, self.build_url1)
        self.exporter.add_to_unpulled(self.file_name2, self.build_url2)

        expected_unpulled_builds = {
            self.file_name1: [self.build_url1],
            self.file_name2: [self.build_url2]
        }

        self.assertEqual(expected_unpulled_builds, self.exporter.unpulled_builds)

    def test_one_building_another_file_exist(self):
        self.exporter.unpulled_builds = {
            self.file_name1: [self.build_url1]
        }

        self.exporter.add_to_unpulled(self.file_name2, self.build_url2)

        expected_unpulled_builds = {
            self.file_name1: [self.build_url1],
            self.file_name2: [self.build_url2]
        }

        self.assertEqual(expected_unpulled_builds, self.exporter.unpulled_builds)


class TestGetSourceFilename(unittest.TestCase):
    def setUp(self):
        self.exporter = export.JenkinsExporter()
        self.get_fields_func = lambda source: (source['instance'], source['ci'], source['stage'])

    def test(self):
        source = {'derp': 'herp', 'instance': 'Production', 'ci': 'ci1', 'stage': 'Build'}
        self.assertEqual(self.exporter.get_file_name(source, self.get_fields_func), 'Production_ci1_Build')


class TestGetFileNameFieldsProduct(unittest.TestCase):
    def test_tags_none(self):
        source = {'instance': 'Production', 'ci': 'ci1', 'stage': 'Build', 'tags': None}
        expected = ['Production', 'ci1', 'Build']
        actual = export.JenkinsExporter.get_file_name_fields_product(source)
        self.assertEqual(expected, actual)

    def test_tags_one(self):
        source = {'instance': 'Production', 'ci': 'ci1', 'stage': 'Build', 'tags': 'derp'}
        expected = ['Production', 'ci1', 'Build', 'derp']
        actual = export.JenkinsExporter.get_file_name_fields_product(source)
        self.assertEqual(expected, actual)

    def test_tags_two(self):
        source = {'instance': 'Production', 'ci': 'ci1', 'stage': 'Build', 'tags': 'derp,herp'}
        expected = ['Production', 'ci1', 'Build', 'derp', 'herp']
        actual = export.JenkinsExporter.get_file_name_fields_product(source)
        self.assertEqual(expected, actual)


class TestGetFileNameFieldsIns(unittest.TestCase):
    def test(self):
        source = {'pipeline': 'AllCores', 'branch': 'pipeline_corrections'}
        expected = ['AllCores', 'pipeline-corrections']
        actual = export.JenkinsExporter().get_file_name_fields_ins(source)
        self.assertEqual(expected, actual)


class TestGetFileNameFieldsVic(unittest.TestCase):
    def test(self):
        source = {'job_name': 'job1', 'instance': 'Development'}
        expected = ['Development', 'job1']
        actual = export.JenkinsExporter().get_file_name_fields_vic(source)
        self.assertEqual(expected, actual)


class TestGetLastJobPulledTime(unittest.TestCase):
    def setUp(self):
        self.exporter = export.JenkinsExporter()

    def test_no_section(self):
        val = self.exporter.get_last_job_pulled_time('section')
        assert int(val) == 0

    def test_empty_section(self):
        self.exporter.config.add_section('section')
        val = self.exporter.get_last_job_pulled_time('section')
        assert int(val) == 0

    def test_section(self):
        self.exporter.config.add_section('section')
        self.exporter.config.set('section', 'lastjobpulledtime', '5')
        val = self.exporter.get_last_job_pulled_time('section')
        assert int(val) == 5


class TestGetParameter(unittest.TestCase):
    def setUp(self):
        self.build_json = {}
        self.parameter_name = None

        self.expected_value = None

    def do_it(self):
        actual_value = export.JenkinsExporter.get_parameter(self.build_json, self.parameter_name)
        self.assertEqual(self.expected_value, actual_value)

    def test_empty_build_json(self):
        self.do_it()

    def test_no_parameters_action(self):
        self.build_json = {
            'actions': [
                {
                    'derp': 'herp'
                },
                {
                    '_class': 'other_class',
                    'hello': 'hi'
                }
            ]
        }

        self.do_it()

    def test_no_matching_parameter(self):
        self.build_json = {
            'actions': [
                {
                    'derp': 'herp'
                },
                {
                    '_class': 'other_class',
                    'hello': 'hi'
                },
                {
                    '_class': 'hudson.model.ParametersAction',
                    'parameters': [
                        {
                            'name': 'something',
                            'value': 'else'
                        }
                    ]
                }
            ]
        }

        self.do_it()

    def test(self):
        self.build_json = {
            'actions': [
                {
                    'derp': 'herp'
                },
                {
                    '_class': 'other_class',
                    'hello': 'hi'
                },
                {
                    '_class': 'hudson.model.ParametersAction',
                    'parameters': [
                        {
                            'name': 'something',
                            'value': 'else'
                        },
                        {
                            'name': 'my_parameter',
                            'value': 5
                        }
                    ]
                }
            ]
        }

        self.parameter_name = 'my_parameter'
        self.expected_value = 5

        self.do_it()


class TestGetAllParameters(unittest.TestCase):
    def setUp(self):
        self.build_json = {}
        self.expected_params = {}

    def do_it(self):
        actual_params = export.JenkinsExporter.get_all_parameters(self.build_json)
        self.assertEqual(self.expected_params, actual_params)

    def test_empty_build_json(self):
        self.do_it()

    def test_no_parameters_action(self):
        self.build_json = {
            'actions': [
                {
                    'derp': 'herp'
                },
                {
                    '_class': 'other_class',
                    'hello': 'hi'
                }
            ]
        }

        self.do_it()

    def test_parameters_action_empty_params(self):
        self.build_json = {
            'actions': [
                {
                    'derp': 'herp'
                },
                {
                    '_class': 'other_class',
                    'hello': 'hi'
                },
                {
                    '_class': 'hudson.model.ParametersAction',
                    'parameters': []
                }
            ]
        }

        self.do_it()

    def test_one_parameters_action(self):
        self.build_json = {
            'actions': [
                {
                    'derp': 'herp'
                },
                {
                    '_class': 'other_class',
                    'hello': 'hi'
                },
                {
                    '_class': 'hudson.model.ParametersAction',
                    'parameters': [
                        {
                            'name': 'something',
                            'value': 'else'
                        },
                        {
                            'name': 'my_parameter',
                            'value': 5
                        }
                    ]
                }
            ]
        }

        self.expected_params = {
            'something': 'else',
            'my_parameter': 5
        }

        self.do_it()

    def test_multiple_parameters_actions(self):
        self.build_json = {
            'actions': [
                {
                    'derp': 'herp'
                },
                {
                    '_class': 'other_class',
                    'hello': 'hi'
                },
                {
                    '_class': 'hudson.model.ParametersAction',
                    'parameters': [
                        {
                            'name': 'something',
                            'value': 'else'
                        },
                        {
                            'name': 'my_parameter',
                            'value': 5
                        }
                    ]
                },
                {
                    '_class': 'hudson.model.ParametersAction',
                    'parameters': [
                        {
                            'name': 'my_parameter2',
                            'value': 'omg'
                        }
                    ]
                }
            ]
        }

        self.expected_params = {
            'something': 'else',
            'my_parameter': 5,
            'my_parameter2': 'omg'
        }

        self.do_it()


class TestGetTextFromRequest(unittest.TestCase):
    def setUp(self):
        self.exporter = export.JenkinsExporter()

    def test_not_found(self):
        content = self.exporter.get_text_from_request('https://derp', True, None)
        assert not content

    def test_not_found_with_no_warning(self):
        content = self.exporter.get_text_from_request('https://derp', False, None)
        assert not content

    @patch('pivt.util.util.get')
    def test_metrics(self, mock_get):
        build_json = {'building': False}
        build_str = json.dumps(build_json)
        build_text = bytes(build_str, 'utf-8')
        mock_get.return_value = build_text

        metrics = {'requests': 0, 'bytes_pulled': 0}
        content = self.exporter.get_text_from_request('http://derp', True, metrics)

        assert content == build_str
        assert metrics['requests'] == 1
        assert metrics['bytes_pulled'] == len(build_text)

    @patch('pivt.util.util.get')
    def test_no_metrics(self, mock_get):
        build_json = {'building': False}
        build_str = json.dumps(build_json)
        build_text = bytes(build_str, 'utf-8')
        mock_get.return_value = build_text

        metrics = {'requests': 0, 'bytes_pulled': 0}
        content = self.exporter.get_text_from_request('http://derp', True, None)

        assert content == build_str
        assert metrics['requests'] == 0
        assert metrics['bytes_pulled'] == 0

    @patch('pivt.util.util.get')
    def test_metrics_no_requests(self, mock_get):
        build_json = {'building': False}
        build_str = json.dumps(build_json)
        build_text = bytes(build_str, 'utf-8')
        mock_get.return_value = build_text

        metrics = {'bytes_pulled': 0}
        content = self.exporter.get_text_from_request('http://derp', True, metrics)

        assert content == build_str
        assert metrics['bytes_pulled'] == 0

    @patch('pivt.util.util.get')
    def test_metrics_no_bytes_pulled(self, mock_get):
        build_json = {'building': False}
        build_str = json.dumps(build_json)
        build_text = bytes(build_str, 'utf-8')
        mock_get.return_value = build_text

        metrics = {'requests': 0}
        content = self.exporter.get_text_from_request('http://derp', True, metrics)

        assert content == build_str
        assert metrics['requests'] == 0
