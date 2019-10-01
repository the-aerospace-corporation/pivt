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
Utility functions
"""

import logging
import logging.handlers
import os
import sys
import time
import datetime
import re
import shutil
from urllib.request import urlopen
from collections import abc
from pathlib import Path
import ssl
import pivt.conf_manager as cm


class Utility:
    """Utility class to hold common values and functions."""
    def __init__(self):
        # Paths
        self.pivt_home = Path()

        self.etc_dir = Path()
        self.var_dir = Path()

        # config files
        self.version_file = Path()
        self.sources_file = Path()
        self.sources_file_ins = Path()
        self.sources_file_vic = Path()
        self.metadata_file = Path()
        self.unpulled_builds_file = Path()

        self.log_dir = Path()

        # data directories
        self.data_dir = Path()
        self.archive_dir = Path()
        self.collected_dir = Path()
        self.db_dir = Path()
        self.new_data_dir = Path()

        self.jenkins_data_dir = Path()
        self.jenkins_ft_data_dir = Path()
        self.ins_data_dir = Path()
        self.vic_data_dir = Path()
        self.cq_data_dir = Path()
        self.cq_data_path_old = Path()
        self.cq_changed_files_path = Path()
        self.cq_data_path = Path()
        self.cq_events_path = Path()
        self.vic_status_data_dir = Path()

        # Logging
        self.file_handler = None

        self.logger_formatter = logging.Formatter('%(asctime)s [%(name)s] %(levelname)s - %(message)s')

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self.logger_formatter)

        root_logger = logging.getLogger('')
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(console_handler)

        self.logger = self.get_logger(self)

        self.splunk_url = ''

        # any Jenkins file pulled after this date without an instance field
        # in its data will have its instance set to "Production". else, it is "Development"
        self.first_default_prod_date = datetime.datetime(2018, 1, 23)

        self.ci_to_ss = Utility.setup_ci_to_ss()

        self.conf_manager = None

        self.initialized = False

    def setup(self):
        """
        Initialize
        """
        if self.initialized:
            return

        self.setup_env()

        self.file_handler = self.get_logger_file_handler('pivt')
        logging.getLogger('').addHandler(self.file_handler)

        self.splunk_url = 'https://{0}:8089'.format(os.environ.get('SPLUNK_HOST', 'localhost'))

        self.conf_manager = cm.ConfManager(self.etc_dir)
        self.conf_manager.load()

        self.initialized = True

    def setup_env(self):
        """Initialize environment."""
        if 'PIVT_HOME' not in os.environ:
            sys.exit('No PIVT_HOME in environment. Exiting.')

        self.pivt_home = Path(os.environ['PIVT_HOME'])

        if not self.pivt_home.exists():
            sys.exit('PIVT_PATH {0} does not exist. Exiting.'.format(self.pivt_home))

        self.etc_dir = self.pivt_home / 'etc'
        self.var_dir = self.pivt_home / 'var'

        self.version_file = self.etc_dir / 'pivt.version'  # file containing current and previous version info
        self.sources_file = self.etc_dir / 'product.sources'
        self.sources_file_ins = self.etc_dir / 'ins.sources'
        self.sources_file_vic = self.etc_dir / 'vic.sources'
        self.metadata_file = self.etc_dir / 'job_pull_times.ini'
        self.unpulled_builds_file = self.etc_dir / 'unpulled.json'

        self.log_dir = self.var_dir / 'log'

        self.data_dir = self.var_dir / 'data'  # path to directory with files monitored by Splunk
        self.archive_dir = self.data_dir / 'archive'  # path to archive directory
        self.collected_dir = self.data_dir / 'collected'  # path to collected directory
        self.db_dir = self.data_dir / 'data'
        self.new_data_dir = self.data_dir / 'newdata'

        self.jenkins_data_dir = self.db_dir / 'jenkins'
        self.jenkins_ft_data_dir = self.jenkins_data_dir / 'ft'

        self.ins_data_dir = self.db_dir / 'ins'

        self.vic_data_dir = self.db_dir / 'vic'

        self.cq_data_dir = self.db_dir / 'cq'
        self.cq_data_path_old = self.cq_data_dir / 'CQ_Data.csv'
        self.cq_changed_files_path = self.cq_data_dir / 'CQ_Changed_Files.csv'

        self.cq_data_path = self.cq_data_dir / 'drs.csv'
        self.cq_events_path = self.cq_data_dir / 'events.json'

        self.vic_status_data_dir = self.db_dir / 'vic_status'

        self.log_dir.mkdir(parents=True, exist_ok=True)

    def teardown(self):
        """Tear down the util instance. Mainly used for unit tests."""
        if self.file_handler is not None:
            self.file_handler.close()

        util.rmtree(self.log_dir, no_exist_ok=True)

        self.__init__()

    @staticmethod
    def setup_ci_to_ss():
        """
        Set up CI to subsystem map.
        """
        ss_to_ci = {
            '%%ci31%%': ['%%ci16%%', '%%ci17%%'],
            '%%ci32%%': ['%%ci18%%', '%%ci19%%', '%%ci15%%', '%%ci20%%', '%%ci12%%'],
            '%%ci21%%': ['%%ci21%%'],
            '%%ci22%%': ['%%ci22%%', '%%ci23%%', '%%ci24%%', '%%ci25%%', '%%ci9%%', '%%ci7%%', '%%ci8%%', '%%ci10%%'],
            '%%ci33%%': ['%%ci26%%'],
            '%%ci34%%': ['%%ci27%%'],
            '%%ci35%%': ['%%ci28%%', '%%ci11%%', '%%ci29%%'],
            '%%ci36%%': ['%%ci30%%', '%%ci13%%', '%%ci14%%']
        }

        ci_to_ss = {}

        for ss, cis in ss_to_ci.items():
            for ci in cis:
                ci_to_ss[ci] = ss

        return ci_to_ss

    @staticmethod
    def get_logger(obj, file_handler=None):
        """
        Create a logger.
        :param obj: the name of the logger or class that is requesting it
        :param file_handler: an optional file handler to add to the logger
        :return: the logger
        """
        if isinstance(obj, str):
            name = obj
        else:
            name = str(obj.__class__.__name__)

        logger = logging.getLogger(name)

        if file_handler is not None:
            logger.addHandler(file_handler)

        return logger

    def get_logger_file_handler(self, title, when='W6', backup_count=5):
        """
        Create a logger file handler.
        :param title: the name of the file
        :param when: frequency to rotate the log file
        :param backup_count: number of log files to keep
        :return: the file handler
        """
        file_handler = logging.handlers.TimedRotatingFileHandler(str((self.log_dir / (title + '.log'))), when=when, backupCount=backup_count)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(self.logger_formatter)

        return file_handler

    @staticmethod
    def gen_jenkins_event_key(event, time_field='timestamp'):
        """
        Generate Jenkins event key.
        :param event: Jenkins event
        :param time_field: event timestamp field
        :return: Jenkins event key
        """
        return '{0}:{1}:{2}:{3}'.format(event['ci'], event['stage'], event['number'], event[time_field])

    @staticmethod
    def gen_ins_event_key(event, time_field='timestamp'):
        """
        Generate %%ci33%% event key.
        :param event: %%ci33%% event
        :param time_field: event timestamp field
        :return: %%ci33%% event key
        """
        return '{0}:{1}:{2}'.format(event['core'], event['id'], event[time_field])

    @staticmethod
    def gen_jenkins_project_key(project, number):
        """
        Returns a unique key for an event instance

        :param project: The project the event instance belongs to
        :param number:  The build number of the project
        :returns: A key that uniquely identifies an event instance
        """
        return '{0}:{1}'.format(project, number)

    @staticmethod
    def get_project_name(event):
        """
        Get a Jenkins event project name.
        :param event: the Jenkins event
        :return: the project name
        """
        try:
            full_display_name = event['fullDisplayName']
            return full_display_name.split(' ')[0]
        except KeyError:
            pass

        try:
            url = event['url']
            return url.split('/')[-3]
        except KeyError:
            return None

    def update_dashboards(self, splunk_home, logger, get_new_date=False):
        """
        Update Splunk dashboards with current version and pull date.
        :param splunk_home: path to Splunk installation
        :param logger: logger to use for logging
        :param get_new_date: if True, generate a new pull date using current time; else, load from file
        """
        new_description = self._get_new_dashboard_description(get_new_date)
        path = self._get_dashboards_path(splunk_home, logger)
        dashboard_names = os.listdir(path)
        for dashboard_name in dashboard_names:
            self._update_last_pull_date(dashboard_name, path, new_description, logger)

    def _get_dashboards_path(self, path_to_splunk, logger):
        """
        Get path to PIVT Splunk app dashboards.
        :param path_to_splunk:
        :param logger: the logger to use for logging
        :return: path to dashboards
        """
        if not logger:
            logger = self.logger

        dashboards_path = path_to_splunk + '/etc/apps/pivt/default/data/ui/views/'
        if not os.path.exists(dashboards_path):
            logger.info('Could not find pivt/default; using pivt/local')
            dashboards_path = path_to_splunk + '/etc/apps/pivt/local/data/ui/views/'
            if not os.path.exists(dashboards_path):
                raise FileNotFoundError('Could not find pivt/local')

        return dashboards_path

    def _update_last_pull_date(self, dashboard_name, dashboards_path, new_dashboard_description, logger):
        """
        Update description for a Splunk dashboard.
        :param dashboard_name: name of dashboard to update
        :param dashboards_path: path to dashboards in Splunk installation
        :param new_dashboard_description: description to update dashboard with
        :param logger: logger to use for logging
        """
        if not logger:
            logger = self.logger

        logger.info('Updating last pull date on %s dashboard', dashboard_name)

        path = dashboards_path + '/' + dashboard_name

        try:
            with open(path, 'r') as file:
                dashboard = file.read()

            dashboard = re.sub(r'<description>.*</description>\n', new_dashboard_description, dashboard)

            with open(path, 'w') as file:
                file.write(dashboard)
        except FileNotFoundError:
            logger.error('File does not exist: %s', path)

    def _get_new_dashboard_description(self, get_new_date=False):
        """
        Get a new dashboard description.
        :param get_new_date: if True, generate a new pull date using current time; else, load from file
        :return new description
        """
        version_string = self.read_value_from_kv_file(self.version_file, 'CURRENT')

        if not get_new_date:
            last_pull_date = self.conf_manager.get('pivt', 'general', 'last_pull')
        else:
            now_date_time = datetime.datetime.now(datetime.timezone.utc).astimezone()
            last_pull_date = self.get_normalized_now_date_time(now_date_time)
            self.conf_manager.set('pivt', 'general', 'last_pull', last_pull_date, create=True)

        return '<description>PIVT Version: {0} --- Last pull date: {1}</description>\n'.format(version_string, last_pull_date)

    @staticmethod
    def get_normalized_now_date_time(now_date_time):
        """
        Produce a normalized date/time string for Splunk dashboards.
        :param now_date_time: the current time in a datetime object
        :return: formatted date/time string
        """
        return '{0} {1}'.format(now_date_time.strftime('%x @ %X'), now_date_time.tzname())

    @staticmethod
    def read_value_from_kv_file(file_path, key):
        """
        Read the value of a key in a file. The file should have the following form:
            key1=value1
            key2=value2
            ...
        :param file_path: path to file to read from
        :param key: key to look up
        :return the value associated with key
        """
        if file_path.exists():
            with file_path.open() as file:
                for line in file:
                    line = line.strip()
                    pull_date_match = re.match(key + '=(.*)', line)
                    if pull_date_match:
                        return pull_date_match.group(1)

        return None

    @staticmethod
    def update_value_in_kv_file(file_path, key, value):
        """
        Update the value of the key in the file to be the value given as an argument.
        :param file_path: path to file to write to
        :param key: key of new value
        :param value: new value associated with key
        """
        new_kv = '{0}={1}\n'.format(key, value)

        if file_path.exists():
            with file_path.open() as file:
                file_data = file.read()

            new_file_data = re.sub(r'{0}=.*\n'.format(key), new_kv, file_data)
        else:
            new_file_data = new_kv

        with file_path.open('w') as file:
            file.write(new_file_data)

    @staticmethod
    def rmtree(path, no_exist_ok=False):
        """
        Safely remove a directory.
        :param path: path to directory to remove
        :param no_exist_ok: if True, don't error if the directory doesn't exist
        """
        if isinstance(path, Path):
            path = str(path)

        if str(path) == '.':
            return

        for i in range(0, 5):
            try:
                shutil.rmtree(path)
                break
            except FileNotFoundError:
                if not no_exist_ok:
                    raise
            except (OSError, PermissionError):
                if i >= 9:
                    raise
                time.sleep(0.2)

    @staticmethod
    def listdir(path):
        """
        Wrapper around os.listdir enabling it on Path objects
        :param path: path to list
        :return: result of listdir
        """
        return os.listdir(str(path))

    @staticmethod
    def basename(path):
        """
        Wrapper around os.path.basename enabling it on Path objects
        :param path: path to get basename from
        :return: basename
        """
        if isinstance(path, str):
            return os.path.basename(path)
        if isinstance(path, Path):
            return path.name

        raise Exception('path must be of type str or Path! path: ' + path)

    @staticmethod
    def inner_stringify(value):
        """
        Stringify inner elements of a dict or string
        :param value: object to stringify
        :return: stringified object
        """
        if isinstance(value, abc.Mapping):
            new_dictionary = {}
            for k, v in value.items():
                new_dictionary[str(k)] = Utility.inner_stringify(v)
            return new_dictionary

        if isinstance(value, abc.Sequence) and not isinstance(value, str):
            new_list = []
            for v in value:
                new_list.append(Utility.inner_stringify(v))
            return new_list

        return str(value)

    @staticmethod
    def get(url):
        """Read data from a URL"""
        return urlopen(url, context=ssl._create_unverified_context()).read()


class Constants:
    """Common constants"""
    SOLVED = 'solved'
    UNSOLVED = 'unsolved'
    CAUSE_NOT_ASSIGNED = 'Not Assigned'
    VERSION_NOT_ASSIGNED = 'Not Assigned'
    ITERATION_NOT_ASSIGNED = 'Not Assigned'
    ROOT_CAUSES = ['user', 'nightly', 'self-service', 'weekly']
    UNKNOWN_VERSION = 'N/A'
    UNIT_TEST = 'UnitTest'
    FUNCTIONAL_TEST = 'FunctionalTest'
    PRODUCTION = 'Production'
    DEVELOPMENT = 'Development'


util = Utility()
