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

from pivt.conf_manager import ConfManager
import unittest
from unittest.mock import patch
import os
import tempfile
import configparser
from pivt.util import util


if __name__ == '__main__':
    unittest.main()


def setUpModule():
    os.environ['PIVT_HOME'] = tempfile.mkdtemp().replace('\\', '/')

    with patch.object(ConfManager, 'load'):
        util.setup()


def tearDownModule():
    util.teardown()
    util.rmtree(os.environ['PIVT_HOME'], no_exist_ok=True)
    if 'PIVT_HOME' in os.environ:
        del os.environ['PIVT_HOME']


def configs_to_dict(configs):
    d = {}

    for filename, config in configs.items():
        d[filename] = {}
        for section in config.sections():
            d[filename][section] = {}
            for option in config.options(section):
                d[filename][section][option] = config.get(section, option)

    return d


def dict_to_configs(d):
    configs = {}

    for filename, stanzas in d.items():
        config = configparser.ConfigParser()

        for stanza, settings in stanzas.items():
            config[stanza] = settings

        configs[filename] = config

    return configs


class TestLoad(unittest.TestCase):
    def setUp(self):
        util.etc_dir.mkdir()
        self.conf_manager = ConfManager(util.etc_dir)

    def tearDown(self):
        util.rmtree(util.etc_dir)

    def test_no_files(self):
        self.assertEqual({}, self.conf_manager.configs)

        self.conf_manager.load()

        self.assertEqual({}, self.conf_manager.configs)

    def test(self):
        self.assertEqual({}, self.conf_manager.configs)

        self.conf_manager.default_dir.mkdir(parents=True)
        self.conf_manager.local_dir.mkdir(parents=True)

        config = configparser.ConfigParser()
        config['section1'] = {'setting11': 'hi', 'setting12': 'hello'}
        config['section2'] = {'setting21': 'hola'}
        with (self.conf_manager.default_dir / 'just_default.conf').open('w') as file:
            config.write(file)

        config = configparser.ConfigParser()
        config['section1'] = {'setting11': '10'}
        config['section2'] = {'setting21': 'False', 'setting22': 'yay'}
        with (self.conf_manager.local_dir / 'just_local.conf').open('w') as file:
            config.write(file)

        config = configparser.ConfigParser()
        config['section1'] = {'setting11': '13', 'setting12': 'True'}
        config['section2'] = {'setting21': 'hola', 'setting22': 'True'}
        with (self.conf_manager.default_dir / 'shared.conf').open('w') as file:
            config.write(file)

        config = configparser.ConfigParser()
        config['section1'] = {'setting11': '17'}
        config['section2'] = {'setting22': 'False', 'setting23': 'cool'}
        with (self.conf_manager.local_dir / 'shared.conf').open('w') as file:
            config.write(file)

        self.conf_manager.load()

        expected_just_default_config = configparser.ConfigParser()
        expected_just_default_config['section1'] = {'setting11': 'hi', 'setting12': 'hello'}
        expected_just_default_config['section2'] = {'setting21': 'hola'}

        expected = {
            'just_default': {
                'section1': {'setting11': 'hi', 'setting12': 'hello'},
                'section2': {'setting21': 'hola'}
            },
            'just_local': {
                'section1': {'setting11': '10'},
                'section2': {'setting21': 'False', 'setting22': 'yay'}
            },
            'shared': {
                'section1': {'setting11': '17', 'setting12': 'True'},
                'section2': {'setting21': 'hola', 'setting22': 'False', 'setting23': 'cool'}
            }
        }

        actual = configs_to_dict(self.conf_manager.configs)

        self.assertEqual(expected, actual)


class TestGet(unittest.TestCase):
    def setUp(self):
        util.etc_dir.mkdir()
        self.conf_manager = ConfManager(util.etc_dir)

    def tearDown(self):
        util.rmtree(util.etc_dir)

    def test_not_initialized(self):
        with self.assertRaises(Exception):
            self.conf_manager.get('', '', '')

    def test_no_file(self):
        with self.assertRaises(Exception):
            self.conf_manager.get('test_file', 'test_stanza', 'test_setting')

    def test_no_stanza_in_file(self):
        self.conf_manager.configs['test_file'] = configparser.ConfigParser()

        with self.assertRaises(Exception):
            self.conf_manager.get('test_file', 'test_stanza', 'test_setting')

    def test_no_setting_in_stanza_in_file(self):
        config = configparser.ConfigParser()
        config['test_stanza'] = {}

        self.conf_manager.configs['test_file'] = config

        with self.assertRaises(Exception):
            self.conf_manager.get('test_file', 'test_stanza', 'test_setting')

    def test(self):
        config1 = configparser.ConfigParser()
        config1['test_stanza'] = {'test_setting': 'test_value', 'other_setting': 'other_value'}
        config1['other_stanza'] = {'derp': 'herp'}

        config2 = configparser.ConfigParser()
        config2['hi'] = {'hello': 'hola'}

        self.conf_manager.configs['test_file'] = config1
        self.conf_manager.configs['test_file_2'] = config2

        self.assertEqual('test_value', self.conf_manager.get('test_file', 'test_stanza', 'test_setting'))


class TestSet(unittest.TestCase):
    def setUp(self):
        util.etc_dir.mkdir()
        self.conf_manager = ConfManager(util.etc_dir)

        self.create = False

        self.file = 'test_file'
        self.stanza = 'test_stanza'
        self.setting = 'test_setting'
        self.value = 'test_value'

        self.configs = {}

        self.raises = False

        self.expected_configs = {}
        self.expected_local_configs = {}

    def tearDown(self):
        util.rmtree(util.etc_dir)

    def do_it(self):
        self.conf_manager.configs = dict_to_configs(self.configs)

        def set_func():
            self.conf_manager.set(self.file, self.stanza, self.setting, self.value, create=self.create)

        if self.raises:
            with self.assertRaises(Exception):
                set_func()
        else:
            set_func()
            self.make_asserts()

    def make_asserts(self):
        actual_configs = configs_to_dict(self.conf_manager.configs)

        self.assertEqual(self.expected_configs, actual_configs)

        config_new = configparser.ConfigParser()
        config_new.read(str(self.conf_manager.local_dir / 'test_file.conf'))
        actual_local_configs = configs_to_dict({'test_file': config_new})

        self.assertEqual(self.expected_local_configs, actual_local_configs)

    def test_not_initialized(self):
        self.raises = True

        self.do_it()

    def test_no_file_create_false(self):
        self.raises = True
        self.do_it()

    def test_no_stanza_in_file_create_false(self):
        self.raises = True

        self.configs = {
            'test_file': {}
        }
        self.do_it()

    def test_create_false_no_local_dir(self):
        self.configs = {
            'test_file': {
                'test_stanza': {}
            }
        }

        self.expected_configs = {
            'test_file': {'test_stanza': {'test_setting': 'test_value'}}
        }

        self.expected_local_configs = {
            'test_file': {'test_stanza': {'test_setting': 'test_value'}}
        }

        self.assertFalse(self.conf_manager.local_dir.exists())

        self.do_it()

    def test_create_false_local_dir_exists(self):
        self.configs = {
            'test_file': {
                'test_stanza': {}
            }
        }

        self.expected_configs = {
            'test_file': {'test_stanza': {'test_setting': 'test_value'}}
        }

        self.expected_local_configs = {
            'test_file': {'test_stanza': {'test_setting': 'test_value'}}
        }

        self.conf_manager.local_dir.mkdir(parents=True)

        self.do_it()

    def test_create_false_file_exists_no_stanza(self):
        self.configs = {
            'test_file': {
                'test_stanza': {}
            }
        }

        self.expected_configs = {
            'test_file': {'test_stanza': {'test_setting': 'test_value'}}
        }

        self.expected_local_configs = {
            'test_file': {
                'test_stanza': {'test_setting': 'test_value'},
                'other_stanza': {'other_setting': 'other_value'}
            }
        }

        self.conf_manager.local_dir.mkdir(parents=True)

        config = configparser.ConfigParser()
        config['other_stanza'] = {'other_setting': 'other_value'}
        with (self.conf_manager.local_dir / 'test_file.conf').open('w') as file:
            config.write(file)

        self.do_it()

    def test_create_false_file_and_stanza_exist(self):
        self.configs = {
            'test_file': {
                'test_stanza': {}
            }
        }

        self.expected_configs = {
            'test_file': {'test_stanza': {'test_setting': 'test_value'}}
        }

        self.expected_local_configs = {
            'test_file': {
                'test_stanza': {'derp': 'herp', 'test_setting': 'test_value'},
                'other_stanza': {'other_setting': 'other_value'}
            }
        }

        self.conf_manager.local_dir.mkdir(parents=True)

        config = configparser.ConfigParser()
        config['test_stanza'] = {'derp': 'herp'}
        config['other_stanza'] = {'other_setting': 'other_value'}
        with (self.conf_manager.local_dir / 'test_file.conf').open('w') as file:
            config.write(file)

        self.do_it()

    def test_create_true_file_and_stanza_exist(self):
        self.create = True

        self.expected_configs = {
            'test_file': {'test_stanza': {'test_setting': 'test_value'}}
        }

        self.expected_local_configs = {
            'test_file': {
                'test_stanza': {'test_setting': 'test_value'},
                'other_stanza': {'other_setting': 'other_value'}
            }
        }

        self.conf_manager.local_dir.mkdir(parents=True)

        config = configparser.ConfigParser()
        config['test_stanza'] = {'test_setting': 'derp_value'}
        config['other_stanza'] = {'other_setting': 'other_value'}
        with (self.conf_manager.local_dir / 'test_file.conf').open('w') as file:
            config.write(file)

        self.do_it()
