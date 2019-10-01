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

from pivt import collect
import unittest
import os
import tempfile
import re
from unittest.mock import MagicMock

from pivt.util import util
from pivt.conf_manager import ConfManager

orig_conf_load = ConfManager.load


def setUpModule():
    os.environ['PIVT_HOME'] = tempfile.mkdtemp().replace('\\', '/')

    ConfManager.load = MagicMock()

    util.setup()


def tearDownModule():
    util.teardown()
    util.rmtree(os.environ['PIVT_HOME'], no_exist_ok=True)
    if 'PIVT_HOME' in os.environ:
        del(os.environ['PIVT_HOME'])

    ConfManager.load = orig_conf_load


if __name__ == '__main__':
    unittest.main()


def make_files():
    new_data_dir = util.new_data_dir

    dirs = ['dir1', 'dir2', 'dir3']
    for path in dirs:
        whole_path = new_data_dir / path
        whole_path.mkdir(parents=True)
        inner_dummy_file = whole_path / 'file.txt'
        inner_dummy_file.open('w').close()

    outer_dummy_file = new_data_dir / 'file.txt'
    outer_dummy_file.open('w').close()


class TestMain(unittest.TestCase):
    def setUp(self):
        self.collector = collect.Collector()
        util.rmtree(util.data_dir, no_exist_ok=True)

    def tearDown(self):
        util.rmtree(util.data_dir, no_exist_ok=True)

    def test_new_data_dir_dne(self):
        with self.assertRaises(SystemExit):
            self.collector.main()

    def test(self):
        make_files()

        self.assertFalse(util.archive_dir.exists())
        self.assertFalse(util.collected_dir.exists())

        self.collector.main()

        self.assertTrue(util.archive_dir.exists())
        self.assertTrue(util.collected_dir.exists())

        collected_dir_fixed_path = str(util.collected_dir.as_posix())
        self.assertEqual(len(os.listdir(collected_dir_fixed_path)), 1)
        collected_dir_contents = list(util.collected_dir.glob('*'))
        collect_archive_path = str(collected_dir_contents[0].as_posix())
        collect_pattern = re.compile(collected_dir_fixed_path + r'/\d\d-\d\d-\d\dT\d\d-\d\d-\d\d_NewData\.zip')
        self.assertTrue(collect_pattern.fullmatch(collect_archive_path))

        archive_dir_fixed_path = str(util.archive_dir.as_posix())
        self.assertEqual(len(os.listdir(archive_dir_fixed_path)), 1)
        archive_dir_contents = list(util.archive_dir.glob('*'))
        archive_archive_path = str(archive_dir_contents[0].as_posix())
        archive_pattern = re.compile(archive_dir_fixed_path + r'/\d\d-\d\d-\d\dT\d\d-\d\d-\d\d_NewData\.zip')
        self.assertTrue(archive_pattern.fullmatch(archive_archive_path))

        self.assertFalse(os.listdir(str(util.new_data_dir)))


class TestSetup(unittest.TestCase):
    def setUp(self):
        self.collector = collect.Collector()
        util.rmtree(util.data_dir, no_exist_ok=True)

    def tearDown(self):
        util.rmtree(util.data_dir, no_exist_ok=True)

    def test_not_exists(self):
        self.collector.setup()
        self.assertTrue(util.archive_dir.exists())
        self.assertTrue(util.collected_dir.exists())

    def test_exists(self):
        util.archive_dir.mkdir(parents=True)
        util.collected_dir.mkdir(parents=True)
        self.collector.setup()
        self.assertTrue(util.archive_dir.exists())
        self.assertTrue(util.collected_dir.exists())


class TestGetPullDirs(unittest.TestCase):
    def setUp(self):
        self.collector = collect.Collector()
        util.rmtree(util.data_dir, no_exist_ok=True)

    def tearDown(self):
        util.rmtree(util.data_dir, no_exist_ok=True)

    def test(self):
        make_files()

        pull_dirs = self.collector.get_pull_dirs()

        self.assertEqual(len(pull_dirs), 3)
        self.assertIn(util.new_data_dir / 'dir1', pull_dirs)
        self.assertIn(util.new_data_dir / 'dir2', pull_dirs)
        self.assertIn(util.new_data_dir / 'dir3', pull_dirs)


class TestZipData(unittest.TestCase):
    def setUp(self):
        self.collector = collect.Collector()
        util.rmtree(util.data_dir, no_exist_ok=True)

    def tearDown(self):
        util.rmtree(util.data_dir, no_exist_ok=True)

    def test(self):
        make_files()

        archive_path = str(self.collector.zip_data()).replace('\\', '/')

        self.assertTrue(os.path.exists(archive_path))
        self.assertEqual(len(os.listdir(str(util.collected_dir))), 1)

        pattern = re.compile('(.*/)?' + str(util.collected_dir).replace('\\', '/') + r'/\d\d-\d\d-\d\dT\d\d-\d\d-\d\d_NewData\.zip')
        self.assertTrue(pattern.fullmatch(archive_path))


class TestCleanup(unittest.TestCase):
    def setUp(self):
        self.collector = collect.Collector()
        util.rmtree(util.data_dir, no_exist_ok=True)

    def tearDown(self):
        util.rmtree(util.data_dir, no_exist_ok=True)

    def test(self):
        make_files()
        self.collector.cleanup()
        self.assertFalse(os.listdir(str(util.new_data_dir)))
