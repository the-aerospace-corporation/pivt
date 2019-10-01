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
Processes Jenkins and ClearQuest data for Splunk ingestion
"""

import sys
import os
import json
import datetime
import zipfile
import csv
import argparse
import re
import locale
import copy
import time
from functools import reduce
from collections import OrderedDict
import requests
from pivt.util import util
from pivt.util import Constants

requests.packages.urllib3.disable_warnings()

SPLUNK_PATH = '/opt/splunk'

# Jenkins stuff
# fields to pull out of raw Jenkins data
INTERESTING_JENK%%ci33%%_FIELDS = ['id', 'ci', 'ss', 'duration', 'result', 'number', 'timestamp', 'ttr', 'stage',
                              'instance', 'url', 'fullDisplayName', 'cause', 'pipeline_properties', 'pipeline_json']
INTERESTING_JENK%%ci33%%_PARAMETERS = ['BASELINE_VERSION', 'PIPELINE_VERSION', 'CLEARCASE_VIEW', 'TARGET_ENV']

# substitution map for CI names for legacy data
CI_SUBS = {
    '%%ci2%%': '%%ci23%%',
    '%%ci3%%': '%%ci24%%',
    '%%ci0%%': '%%ci7%%',
    '%%ci1%%': '%%ci8%%',
    '%%ci4%%': '%%ci13%%',
    '%%ci5%%': '%%ci14%%',
    '%%ci6%%': '%%ci15%%'
}

ITERATION_REX = re.compile(r'\d+\.\d+')

CQ_INDEX = 'pivt_cq'
PIVT_APP = 'pivt'

SPLUNK_USERNAME = "script_user"
SPLUNK_PASSWORD = "changeme"


class Processor:
    """
    Class to facilitate processing of data.
    """
    def __init__(self, args):
        util.setup()
        self.logger = util.get_logger(self)

        self.args = self.parse_args(args)

        self.sources = {
            'jenkins': ProductSource(),
            'ins': InsSource(),
            'vic': VicSource(),
            'cq': CqSource(),
            'cq_old': CqSourceOld(),
            'vic_status': VicStatusSource()
        }

    def main(self):
        """
        Process the data.
        :return:
        """
        # create archive directory if it doesn't exist
        util.archive_dir.mkdir(parents=True, exist_ok=True)

        # set locale for datetime things
        try:
            locale.setlocale(locale.LC_ALL, 'en_US.utf8')
        except locale.Error:
            self.logger.error('Could not set locale')

        self.logger.info('Splunk URL: %s', util.splunk_url)

        # get list of files in new data directory
        # archive_paths = sorted(glob.glob(util.collected_dir + '/*'))
        archive_paths = sorted(list(util.collected_dir.glob('*')), reverse=self.args.reverse)

        # SETUP
        for source in self.sources.values():
            source.setup()

        if archive_paths:
            self.sources['cq_old'].load_existing_data()

        # PROCESS
        # extract archives, pull out relevant data, and process jenkins and ins data
        # (we leave CQ processing until after)
        for archive_path in archive_paths:
            archive = Archive(archive_path, self.sources)
            archive.load(archive_paths, self.args.reverse)

        for source in self.sources.values():
            source.finish()

        util.update_dashboards(SPLUNK_PATH, self.logger, get_new_date=True)

        # REFRESH PIVT SPLUNK APP VIEWS
        self.logger.info('Refreshing %s app', PIVT_APP)
        Processor.refresh_app(PIVT_APP)

        self.logger.info('Done')

    @staticmethod
    def parse_args(args):
        """
        Parse command line arguments using argparse.
        :param args: command line arguments
        :return: parsed arguments
        """
        parser = argparse.ArgumentParser(description='Process Jenkins, ClearQuest, and %%ci33%% data for Splunk')
        # parser.add_argument('--no-jenkins', dest='process_jenkins', action='store_false')
        # parser.add_argument('--no-cq', dest='process_cq', action='store_false')
        # parser.add_argument('--no-ins', dest='process_ins', action='store_false')
        parser.add_argument('--reverse', dest='reverse', action='store_true')
        # parser.set_defaults(process_jenkins=True)
        # parser.set_defaults(process_ins=True)
        # parser.set_defaults(process_cq=True)
        parser.set_defaults(reverse=False)

        return parser.parse_args(args)

    @staticmethod
    def delete_index(index_name, app_name):
        """
        Delete a Splunk index.
        :param index_name:
        :param app_name: name of the Splunk app the index belongs to
        :param splunk_url:
        :return:
        """
        path = Processor._get_index_path(index_name, app_name)
        url = '{0}{1}'.format(util.splunk_url, path)

        requests.delete(url, auth=(SPLUNK_USERNAME, SPLUNK_PASSWORD), verify=False)

        i = 0
        while requests.get(url, auth=(SPLUNK_USERNAME, SPLUNK_PASSWORD), verify=False).status_code != 404:
            if i >= 10:
                util.get_logger(Processor).warning('Failed to delete index %s at %s. You may need to delete '
                                                   'and recreate it manually', index_name, url)
                break

            time.sleep(1)
            i += 1

    @staticmethod
    def create_index(index_name, app_name):
        """
        Create a Splunk index.
        :param index_name:
        :param app_name: name of the Splunk app the index belongs to
        :param splunk_url:
        :return:
        """
        path = Processor._get_indexes_path(app_name)
        url = '{0}{1}'.format(util.splunk_url, path)

        requests.post(url, auth=(SPLUNK_USERNAME, SPLUNK_PASSWORD), verify=False, data={'name': index_name})

    @staticmethod
    def refresh_app(app_name):
        """
        Refresh a Splunk app causing configs and dashboards to be reloaded.
        :param app_name:
        :param splunk_url:
        :return:
        """
        path = Processor._get_app_path(app_name)
        url = '{0}/{1}/data/ui/views/_reload'.format(util.splunk_url, path)
        requests.get(url, auth=(SPLUNK_USERNAME, SPLUNK_PASSWORD), verify=False)

    @staticmethod
    def _get_index_path(index_name, app_name):
        """
        Construct the REST endpoint URL to a Splunk index.
        :param index_name:
        :param app_name: name of the Splunk app the index belongs to
        :return: the URL
        """
        return '{0}/{1}'.format(Processor._get_indexes_path(app_name), index_name)

    @staticmethod
    def _get_indexes_path(app_name):
        """
        Construct the REST endpoint URL to the Splunk indexes for an app.
        :param app_name:
        :return: the URL
        """
        return '/servicesNS/nobody/{0}/data/indexes'.format(app_name)

    @staticmethod
    def _get_app_path(app_name):
        """
        Construct the REST endpoint URL to a Splunk app
        :param app_name:
        :return: the URL
        """
        return '/servicesNS/nobody/{0}'.format(app_name)


class Source:
    def __init__(self, name, data_dir):
        self.name = name
        self.data_dir = data_dir
        self.logger = util.get_logger(self)

    def setup(self):
        """
        Sets up this source. Called once before loading new data.
        """
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def load_new_data(self, pull_source_path, **kwargs):
        """
        Called once for each pull dir in each archive
        :param pull_source_path: the path to the new data in the pull dir
        :param kwargs: extra arguments
        """
        pass

    def finish(self):
        pass


class JenkinsSource(Source):
    def __init__(self, name, data_dir):
        super().__init__(name, data_dir)
        self.event_keys = {}
        self.file_stats = {}

    def setup(self):
        super().setup()

        files = self.data_dir.glob('*')
        files = list(filter(lambda file: file.is_file(), files))
        self._load_event_keys(files)

    def _load_event_keys(self, files):
        for file_path in files:
            basename = util.basename(file_path)
            self.event_keys[basename] = {'new': set()}
            self.event_keys[basename]['existing'] = self._load_db_file_event_keys(file_path)

    def _load_db_file_event_keys(self, db_file):
        db_file_event_keys = set()
        if db_file.exists():
            with db_file.open() as file:
                for line in file:
                    key = self._get_event_key(line)
                    db_file_event_keys.add(key)

        return db_file_event_keys

    @staticmethod
    def _get_event_key(raw_event):
        return None

    def load_new_data(self, pull_source_path, **kwargs):
        files = self._load_new_files(pull_source_path, **kwargs)

        total_events_added = 0
        total_events_skipped = 0

        for file in files:
            added, skipped = file.process(self.data_dir, self.file_stats, self.event_keys)
            total_events_added += added
            total_events_skipped += skipped

        self.logger.info('Added: %s, skipped: %s', total_events_added, total_events_skipped)

    def _load_new_files(self, files_path, **kwargs):
        """
        Extract events from a collection of files and organize them by filename
        :param files_path:       Path to the files to draw events from
        :param default_instance: The default instance for the archive associated with the files
        :param ft_info:          Functional test info for the given archive
        :return: A dictionary of events indexed by filename/event_key
        """
        file_paths = sorted(files_path.glob('*'))
        files_loaded = 0

        for file_path in file_paths:
            file = self._get_data_file(file_path, **kwargs)

            if file is None or 'ins.json' in file.name or file.is_empty():
                continue

            files_loaded += 1

            file.load_events(**kwargs)
            yield file

        self.logger.info('%s files: %s', self.name, files_loaded)

    @staticmethod
    def _get_data_file(file_path, **kwargs):
        return None

    def finish(self):
        self._print_file_stats()

    def _print_file_stats(self):
        file_names = sorted(list(self.file_stats.keys()))
        if not file_names:
            return

        self.logger.info('Source: %s', self.name)

        col_width = max(len(filename) for filename in file_names)
        for filename in file_names:
            stats = self.file_stats[filename]
            file_str = filename.ljust(col_width)
            self.logger.info('%s added: %s, skipped: %s', file_str, stats['added'], stats['skipped'])


class ProductSource(JenkinsSource):
    def __init__(self):
        super().__init__('jenkins', util.jenkins_data_dir)

    def setup(self):
        super().setup()
        util.jenkins_ft_data_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _get_event_key(raw_event):
        event = ProductCookedEvent(raw_event)
        return event.get_key()

    @staticmethod
    def _get_data_file(file_path, **kwargs):
        return ProductDataFile(file_path, kwargs['default_instance'])


class InsSource(JenkinsSource):
    def __init__(self):
        super().__init__('ins', util.ins_data_dir)

    @staticmethod
    def _get_event_key(raw_event):
        event = InsRawEvent(raw_event).cook()
        return event.get_key()

    @staticmethod
    def _get_data_file(file_path, **kwargs):
        return InsDataFile(file_path)


class VicSource(JenkinsSource):
    def __init__(self):
        super().__init__('vic', util.vic_data_dir)

    @staticmethod
    def _get_event_key(raw_event):
        event = VicCookedEvent(raw_event)
        return event.get_key()

    @staticmethod
    def _get_data_file(file_path, **kwargs):
        if 'AWS-VIC-Manager' in file_path.name:
            return VicDataFile(file_path)
        return None


class CqSource(Source):
    def __init__(self):
        super().__init__('cq', util.cq_data_dir)

        self.drs = {}
        self.dr_stats = {'added': 0, 'skipped': 0, 'modified_drs': set()}
        self.event_keys = {'new': set(), 'existing': set()}
        self.header_fields = set()

    def setup(self):
        super().setup()

        if util.cq_data_path.exists():
            with util.cq_data_path.open(newline='') as file:
                reader = csv.DictReader(file)
                self.header_fields = set(reader.fieldnames)
                for row in reader:
                    dr_id = row['id']
                    self.drs[dr_id] = row

        self._load_event_keys()

    def _load_event_keys(self):
        if util.cq_events_path.exists():
            with util.cq_events_path.open() as file:
                for line in file:
                    key = CqCookedEvent(line).get_key()
                    self.event_keys['existing'].add(key)

    def load_new_data(self, pull_source_path, **kwargs):
        added_modified_path = pull_source_path / 'added_modified.csv'

        events = []

        if added_modified_path.exists():
            with added_modified_path.open(newline='') as file:
                reader = csv.DictReader(file)
                for dr in reader:
                    self._load_dr(dr, events)

        self._write_events(events)

    def _load_dr(self, dr, events):
        """
        Load one DR and produce event(s) for it.
        :param dr:
        :param events: event(s) produced by this DR
        :param stats: added/modified/skipped stats
        """
        dr['last_changed'] = dr['history.action_timestamp']
        del dr['history.action_timestamp']

        dr_id = dr['id']
        timestamp = dr['last_changed']

        if dr_id in self.drs and 'last_changed' in self.drs[dr_id] and dr['last_changed'] < self.drs[dr_id]['last_changed']:
            self.dr_stats['skipped'] += 1
            return

        if dr_id not in self.drs:
            events.append({'type': 'add', 'dr_id': dr_id, 'timestamp': timestamp})
            self.dr_stats['added'] += 1
        else:
        # elif timestamp >= self.drs[dr_id]['last_changed']:
            changes = self._get_changes(self.drs[dr_id], dr)
            for change in changes:
                events.append({'type': 'modify', 'dr_id': dr_id, 'timestamp': timestamp, **change})

            if changes:
                self.dr_stats['modified_drs'].add(dr_id)

        self.drs[dr_id] = dr
        self.header_fields.update(set(dr.keys()))

    @staticmethod
    def _get_changes(old_dr, new_dr):
        """
        Get list of changes between two DRs.
        :param old_dr:
        :param new_dr:
        :return: the list of changes
        """
        changes = []

        old_dr_fields = set(old_dr.keys())
        new_dr_fields = set(new_dr.keys())

        common_fields = old_dr_fields & new_dr_fields

        # fields in old_dr but not in new_dr (before = not None, after = None)
        removed_fields = old_dr_fields - common_fields
        for field in removed_fields:
            if field == 'last_changed':
                continue

            changes.append({'change_field': field, 'before': old_dr[field], 'after': '%%NONE%%'})

        # fields in new_dr but not in old_dr (before = None, after = not None)
        added_fields = new_dr_fields - common_fields
        for field in added_fields:
            if field == 'last_changed':
                continue

            changes.append({'change_field': field, 'before': '%%NONE%%', 'after': new_dr[field]})

        # fields in both but that have changed (before = not None, after = not None)
        for field in common_fields:
            if field == 'last_changed':
                continue

            old_val = old_dr[field]
            new_val = new_dr[field]

            if old_val != new_val:
                changes.append({'change_field': field, 'before': old_val, 'after': new_val})

        return changes

    def _write_events(self, events):
        events_added = 0
        events_skipped = 0

        existing_key_set = self.event_keys['existing']
        new_key_set = self.event_keys['new']

        # open the db file for appending and iterate through events to append to the db file
        with util.cq_events_path.open('a') as file:
            for event in events:
                key = CqCookedEvent(event).get_key()

                # use the key to determine if this event should be added to the db file
                if key not in existing_key_set and key not in new_key_set:
                    file.write(json.dumps(event) + '\n')
                    new_key_set.add(key)
                    events_added += 1
                elif key in existing_key_set:
                    events_skipped += 1

        self.logger.info('%d added events', events_added)
        self.logger.info('%d skipped events', events_skipped)

    def finish(self):
        self._write_drs()

    def _write_drs(self):
        with util.cq_data_path.open('w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=self.header_fields)
            writer.writeheader()
            writer.writerows(self.drs.values())

        self.logger.info('%d updated rows', len(self.dr_stats['modified_drs']))
        self.logger.info('%d new rows', self.dr_stats['added'])
        self.logger.info('%d skipped rows', self.dr_stats['skipped'])

        # self.logger.info('Recreating index %s from app %s', CQ_INDEX, PIVT_APP)
        # Processor.delete_index(CQ_INDEX, PIVT_APP)
        # Processor.create_index(CQ_INDEX, PIVT_APP)


class CqSourceOld(Source):
    def __init__(self):
        super().__init__('cq_old', util.cq_data_dir)

        self.orig_data = {}
        self.orig_changed_files = {}

        self.new_data = {}
        self.new_changed_files = {}

    def load_existing_data(self):
        """
        Load existing CQ data from DB directory.
        """
        # load existing data from CQ_Data.csv
        if util.cq_data_path_old.exists():
            with util.cq_data_path_old.open(newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    dr_id = row['id']
                    self.orig_data[dr_id] = row

        # load existing data from CQ_Changed_Files.csv
        if util.cq_changed_files_path.exists():
            with util.cq_changed_files_path.open(newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    dr_id = row['id']
                    filename = row['file']

                    if dr_id not in self.orig_changed_files:
                        self.orig_changed_files[dr_id] = []

                    if filename not in self.orig_changed_files[dr_id]:
                        self.orig_changed_files[dr_id].append(filename)

    def load_new_data(self, pull_source_path, **kwargs):
        with pull_source_path.open(newline='', encoding='utf-8-sig') as file:
            reader = csv.DictReader(file)
            for row in reader:
                dr_id = row['id']

                if 'RTCC_ChangeSet.FileList.Filename' in row:
                    changed_file = row['RTCC_ChangeSet.FileList.Filename']

                    if changed_file != '':
                        if dr_id not in self.new_changed_files:
                            self.new_changed_files[dr_id] = []

                        if ((dr_id not in self.orig_changed_files or changed_file not in self.orig_changed_files[dr_id])
                                and changed_file not in self.new_changed_files[dr_id]):
                            self.new_changed_files[dr_id].append(changed_file)

                    del row['RTCC_ChangeSet.FileList.Filename']

                self.new_data[dr_id] = row

    def finish(self):
        self._process()

    def _process(self):
        # look for new/updated CQ data
        added_rows, updated_rows, skipped_rows, updated_data = self._get_updated_data()

        self.logger.info('Source: cq')
        if added_rows > 0 or updated_rows > 0:
            self.logger.info('Recreating index %s from app %s', CQ_INDEX, PIVT_APP)
            Processor.delete_index(CQ_INDEX, PIVT_APP)
            Processor.create_index(CQ_INDEX, PIVT_APP)

            self._write_data(list(updated_data.values()))

        self.logger.info('%s updated rows', updated_rows)
        self.logger.info('%s new rows', added_rows)
        self.logger.info('%s skipped rows', skipped_rows)

        files_changed = 0

        for files in self.new_changed_files.values():
            files_changed += len(files)

        self._write_changed_files_data()

        self.logger.info('%s files changed', files_changed)

    def _get_updated_data(self):
        added_rows = 0
        updated_rows = 0
        skipped_rows = 0

        updated_data = copy.deepcopy(self.orig_data)

        for dr_id, row in self.new_data.items():
            updated_data[dr_id] = row
            if dr_id in self.orig_data:  # this DR is in the existing data
                orig_row = self.orig_data[dr_id]
                # this DR differs from the one in the existing data, meaning it has been updated
                if not self._dict_compare(row, orig_row):
                    updated_rows += 1
                else:
                    skipped_rows += 1
            else:  # this DR is not in the existing data, meaning it is new
                added_rows += 1

        return added_rows, updated_rows, skipped_rows, updated_data

    @staticmethod
    def _dict_compare(dict1, dict2):
        return not set(dict1.items()) ^ set(dict2.items())

    @staticmethod
    def _write_data(events):
        # write the new and updated rows to CQ_Data.csv
        if util.cq_data_path_old.exists():
            with util.cq_data_path_old.open() as file:
                header = file.readline().strip()

            fields = set(header.split(','))

            for event in events:
                fields.update(set(event.keys()))
        else:
            fields = set()

            for event in events:
                fields.update(set(event.keys()))

        with util.cq_data_path_old.open('w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerows(events)

    def _write_changed_files_data(self):
        # if CQ_Changed_Files.csv does not exist, open it and write the CSV header
        if not util.cq_changed_files_path.exists():
            with util.cq_changed_files_path.open('w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=['id', 'file'])
                writer.writeheader()

        # write the new and updated rows to CQ_Changed_Files.csv
        with util.cq_changed_files_path.open('a', newline='') as file:
            writer = csv.writer(file)
            for dr_id, files in self.new_changed_files.items():
                for filename in files:
                    writer.writerow([dr_id, filename])


class VicStatusSource(JenkinsSource):
    def __init__(self):
        super().__init__('vic_status', util.vic_status_data_dir)

    @staticmethod
    def _get_event_key(raw_event):
        event = VicStatusCookedEvent(raw_event)
        return event.get_key()

    @staticmethod
    def _get_data_file(file_path, **kwargs):
        return VicStatusDataFile(file_path)


class Archive:
    def __init__(self, path, sources):
        self.path = path
        self.sources = sources
        self.name = util.basename(path)
        self.default_instance = self._get_default_instance()
        self.logger = util.get_logger(self)

    def _get_default_instance(self):
        default_instance = 'Development'

        date_str = self.name[:8]
        date = datetime.datetime.strptime(date_str, '%y-%m-%d')
        if date >= util.first_default_prod_date:
            default_instance = 'Production'

        return default_instance

    def load(self, archives, reverse):
        """
        Process data from an archive and merge it with existing data (Jenkins and %%ci33%% only).
        For CQ, prepare for merging.
        :param archives:    list of all archives to be processed
        :param reverse:     if true, reverse order of processing pulldirs
        """
        archive_temp_dir = None

        try:
            pull_dir_paths, cq_file_path, archive_temp_dir = self._get_components(archives)

            if pull_dir_paths:
                pull_dir_paths.sort(reverse=reverse)
                ft_info = FtInfo()

                for pull_dir_path in pull_dir_paths:
                    self._process_pull_dir(pull_dir_path, ft_info)

                ft_info.process()

            if cq_file_path is not None:
                self.logger.info('%s', util.basename(cq_file_path))
                self.sources['cq_old'].load_new_data(cq_file_path)

            self.path.replace(util.archive_dir / self.name)
        finally:
            if archive_temp_dir:
                util.rmtree(archive_temp_dir, no_exist_ok=True)

    def _get_components(self, archives):
        """
        Extracts necessary components of an archive to be able to process the archive
        :param archives:      A collection of all archives
        :return:
            1. A collection of paths to the directories in the archive
            2. The path to ClearQuest data associated with this archive (maybe None)
            3. The path to the temporary directory extracted by archive_name
        """
        self.logger.info('loading archive %s', self.name)

        if self.path.suffix != '.zip':
            if self.path.with_suffix('.zip') in archives:
                self.logger.warning('A folder and archive exist with the same name - removing folder.')
                util.rmtree(self.path)
            else:
                self.logger.warning('Archive is actually a folder - skipping.')
            return None, None, None

        # unzip archive into temp directory
        archive_temp_dir = self._extract(archives)

        # get all items in temp dir
        archive_contents = list(archive_temp_dir.glob('*'))

        # get pull directory paths and cq data path
        pull_dir_paths, cq_file_path = self._get_pull_data_paths(archive_contents)

        return pull_dir_paths, cq_file_path, archive_temp_dir

    def _extract(self, archives):
        """
        Extract a new data archive.
        :param archives: list of all archives
        :return: directory of extracted archive
        """
        archive_temp_path = self.path.with_suffix('')

        if archive_temp_path in archives:
            util.rmtree(archive_temp_path, no_exist_ok=True)
            archives.remove(archive_temp_path)

        with zipfile.ZipFile(str(self.path)) as archive:
            for i in range(0, 5):
                try:
                    archive.extractall(str(archive_temp_path))
                    break
                except OSError:
                    if i < 4:
                        self.logger.error('Error extracting archive. Retrying (%s attempts remaining)', 4 - i)
                        continue
                    self.logger.error('Could not extract archive.')
                    raise

        return archive_temp_path

    def _get_pull_data_paths(self, archive_contents):
        """
        Get pull directories and files from extracted new data archive
        :param archive_contents: list of paths in extracted new data archive
        :return: directory paths and CQ file path
        """
        pull_dir_paths = []
        cq_file_path = None

        for path in archive_contents:
            if path.is_dir():
                pull_dir_paths.append(path)
            elif path.name == 'CQ_Data.csv':
                if cq_file_path is None:
                    cq_file_path = path
                else:
                    sys.exit('Multiple CQ_Data.csv files!')
            else:
                self.logger.info('Some other type of file detected: %s. Ignoring', path)

        return pull_dir_paths, cq_file_path

    def _process_pull_dir(self, path, ft_info):
        pull_dir_basename = util.basename(path)
        self.logger.info('%s', pull_dir_basename)

        pull_sources = path.glob('*')
        for pull_source in pull_sources:
            pull_source_name = util.basename(pull_source)

            if pull_source_name not in self.sources:
                self.logger.warning('unknown source: %s', pull_source_name)
                continue

            source = self.sources[pull_source_name]
            kwargs = {}

            if isinstance(source, ProductSource):
                kwargs['default_instance'] = self.default_instance
                kwargs['ft_info'] = ft_info
            elif isinstance(source, VicStatusSource):
                dt = datetime.datetime.strptime(pull_dir_basename, '%y%m%d%H%M%S')
                dt = dt.replace(tzinfo=datetime.timezone.utc)
                kwargs['timestamp'] = dt.timestamp()

            source.load_new_data(pull_source, **kwargs)


class FtInfo:
    def __init__(self):
        self.ft_info = {}

    def process(self):
        for filename, tables in self.ft_info.items():
            for table_name, content in tables.items():
                self._process_file(filename, table_name, content)

    def _process_file(self, filename, table_name, content):
        if not content:
            return

        identifier = '{0}_{1}'.format(filename, table_name)

        db_file_path = util.jenkins_ft_data_dir / '{0}.csv'.format(identifier)

        if table_name == 'features':
            key_func = self._gen_ft_feature_key
        elif table_name == 'scenarios':
            key_func = self._gen_ft_scenario_key
        else:
            raise Exception('Other table_name found! ' + table_name)

        # TODO: load file for keys first time we see it instead of every time
        # load keys of existing FT file
        current_keys = []
        if db_file_path.exists():
            with db_file_path.open(newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    current_keys.append(key_func(row))

        new_rows = []
        for key, value in content.items():
            if key not in current_keys:
                new_rows.append(value)

        if new_rows:
            if db_file_path.exists():
                with db_file_path.open() as file:
                    header = file.readline().strip()
                    fieldnames = header.split(',')
            else:
                fieldnames = list(new_rows[0].keys())

            if not db_file_path.exists():
                with db_file_path.open('w', newline='') as db_file:
                    writer = csv.DictWriter(db_file, fieldnames=fieldnames)
                    writer.writeheader()

            with db_file_path.open('a', newline='') as db_file:
                writer = csv.DictWriter(db_file, fieldnames=fieldnames)
                for row in new_rows:
                    writer.writerow(row)

    @staticmethod
    def load_ft_info(event):
        if 'reports' not in event:
            return {}, {}

        all_features = {}
        all_scenarios = {}

        reports = event['reports']
        reports = OrderedDict(sorted(reports.items(), key=lambda t: t[0]))

        for report_name, report in reports.items():
            if not report:
                continue

            if 'artifact' in report_name:
                report_name = report_name[report_name.find('artifact') + 9:]

            for feature in report:
                feature, scenarios = FtInfo._load_feature(feature, report_name, event)

                if feature:
                    feature_id = feature['id']
                    if feature_id not in all_features:
                        all_features[feature_id] = []
                    all_features[feature_id].append(feature)

                for scenario in scenarios:
                    scenario_id = scenario['id']
                    if scenario_id not in all_scenarios:
                        all_scenarios[scenario_id] = []
                    all_scenarios[scenario_id].append(scenario)

        final_features = {}
        for feature_id, features in all_features.items():
            feature = reduce(FtInfo._reduce_test, features)
            feature_key = FtInfo._gen_ft_feature_key(feature)
            final_features[feature_key] = feature

        final_scenarios = {}
        for scenario_id, scenarios in all_scenarios.items():
            scenario = reduce(FtInfo._reduce_test, scenarios)
            scenario_key = FtInfo._gen_ft_scenario_key(scenario)
            final_scenarios[scenario_key] = scenario

        return final_features, final_scenarios

    @staticmethod
    def _reduce_test(acc, test):
        result = test['result']
        acc_result = acc['result']

        if acc_result == 'failed':
            return acc
        if result == 'failed':
            return test
        if acc_result == 'skipped' and result != 'skipped':
            return test
        return acc

    @staticmethod
    def _load_feature(feature, report_name, event):
        if not isinstance(feature, dict) or 'elements' not in feature or ('id' in feature and not isinstance(feature['id'], str)) or 'name' not in feature:
            return None, []

        scenarios = []

        feature_name = feature['name']
        feature_id = feature['id'] if 'id' in feature else feature_name
        feature_tags = FtInfo._get_ft_tags(feature)

        elements = feature['elements']

        feature_backgrounds = filter(lambda element: element['type'] == 'background', elements)
        feature_scenarios = list(filter(lambda element: element['type'] != 'background', elements))

        background_results = list(map(FtInfo._get_element_result, feature_backgrounds))
        failed_background_indices = {i: x for i, x in enumerate(background_results) if x != 'passed'}

        scenario_results = list(map(FtInfo._get_element_result, feature_scenarios))

        # for each scenario with a failed corresponding background, set its result to failed
        scenario_results = [failed_background_indices[i] if i in failed_background_indices else x for i, x in enumerate(scenario_results)]

        for i, element in enumerate(feature_scenarios):
            if 'name' not in element:
                continue

            element_result = scenario_results[i]

            element_name = element['name']
            element_id = element['id'] if 'id' in element else element_name
            element_tags = list(set(FtInfo._get_ft_tags(element) + feature_tags))  # combine tags of this element and its feature

            element_row = {
                'name': element_name,
                'id': element_id,
                'result': element_result,
                'tags': ':'.join(element_tags),
                'feature_id': feature_id,
                'report_name': util.basename(report_name),
                'job_instance': event['instance'],
                'job_ci': event['ci'],
                'job_number': event['number'],
                'job_timestamp': event['timestamp'],
                'job_release': event['release']
            }

            scenarios.append(element_row)

        feature_result = FtInfo._get_result(scenario_results)

        feature_row = {
            'name': feature_name,
            'id': feature_id,
            'result': feature_result,
            # 'duration': feature_duration,
            'tags': ':'.join(feature_tags),
            'report_name': util.basename(report_name),
            'job_instance': event['instance'],
            'job_ci': event['ci'],
            'job_number': event['number'],
            'job_timestamp': event['timestamp'],
            'job_release': event['release']
        }

        return feature_row, scenarios

    @staticmethod
    def _reduce_result(acc, result):
        if acc == 'failed' or result == 'failed':
            return 'failed'
        if acc == 'skipped' and result == 'skipped':
            return 'skipped'
        return 'passed'

    @staticmethod
    def _get_result(results):
        if results:
            result = reduce(FtInfo._reduce_result, results)
        else:
            result = 'skipped'

        return result

    @staticmethod
    def _get_element_result(element):
        steps = element['steps'] if 'steps' in element else []

        steps_with_result = list(filter(lambda step: 'result' in step, steps))

        # duration = reduce(lambda a, step: a + step['result']['duration'],
        #                   filter(lambda step: 'duration' in step['result'], steps_with_result), 0)

        step_results = [step['result']['status'] for step in steps_with_result]

        return FtInfo._get_result(step_results)

    @staticmethod
    def _get_ft_tags(element):
        tags = []

        if 'tags' in element:
            element_tags = element['tags']

            for tag in element_tags:
                if isinstance(tag, dict):
                    name = tag['name']
                elif isinstance(tag, str):
                    name = tag
                else:
                    raise Exception('Unknown tag type! {0}'.format(tag))

                if name.startswith('@'):
                    name = name[1:]

                if name not in tags:
                    tags.append(name)

        return tags

    @staticmethod
    def _gen_ft_scenario_key(scenario):
        return '{0}:{1}:{2}:{3}:{4}:{5}'.format(scenario['job_instance'], scenario['job_ci'], scenario['job_number'],
                                                scenario['job_timestamp'], scenario['feature_id'], scenario['id'])

    @staticmethod
    def _gen_ft_feature_key(feature):
        return '{0}:{1}:{2}:{3}:{4}:{5}'.format(feature['job_instance'], feature['job_ci'], feature['job_number'],
                                                feature['job_timestamp'], feature['report_name'], feature['id'])

    def update(self, ft_info_2):
        for filename, tables in ft_info_2.items():
            if filename not in self.ft_info:
                self.ft_info[filename] = tables
                continue

            for table_name, contents in tables.items():
                if table_name in self.ft_info[filename]:
                    self.ft_info[filename][table_name].update(contents)
                else:
                    self.ft_info[filename][table_name] = contents


class DataFile:
    def __init__(self, path):
        self.path = path
        self.name = util.basename(path)
        self._normalize_filename()
        self.events = {}

    def is_empty(self):
        return self.path.stat().st_size <= 0

    def _normalize_filename(self):
        pass

    def load_events(self, **kwargs):
        pass

    def _load_event(self, raw_data, **kwargs):
        pass

    def process(self, data_dir, file_stats, event_keys):
        pass

    def _construct_db_path(self, data_dir):
        """
        Construct the path to database file
        """
        return data_dir / self.name


class JsonDataFile(DataFile):
    def load_events(self, **kwargs):
        with self.path.open() as file:
            for line in file:
                self._load_event(line, **kwargs)

    def process(self, data_dir, file_stats, event_keys):
        if self.name not in event_keys:
            event_keys[self.name] = {'existing': set(), 'new': set()}

        existing_key_set = event_keys[self.name]['existing']
        new_key_set = event_keys[self.name]['new']

        db_file = self._construct_db_path(data_dir)

        added = 0
        skipped = 0
        skipped_overall = 0

        # open the db file for appending and iterate through events to calculate TTR and then append to the db file
        with db_file.open('a') as file:
            for key, event in self.events.items():
                # use the key to determine if this event should be added to the db file
                if key not in existing_key_set and key not in new_key_set:
                    file.write(json.dumps(event) + '\n')
                    new_key_set.add(key)
                    added += 1
                elif key in existing_key_set:
                    skipped_overall += 1
                else:
                    skipped += 1

        if self.name not in file_stats:
            file_stats[self.name] = {'added': 0, 'skipped': 0}

        file_stats[self.name]['added'] += added
        file_stats[self.name]['skipped'] += skipped_overall

        return added, skipped + skipped_overall


class ProductDataFile(JsonDataFile):
    def __init__(self, path, default_instance):
        self.default_instance = default_instance
        self.ft_info_dict = {}
        super().__init__(path)

    def _normalize_filename(self):
        if 'Production' not in self.name and 'Development' not in self.name:
            self.name = self.default_instance + '_' + self.name

        name_without_instance = self.name[self.name.find('_') + 1:]
        ci = name_without_instance[:name_without_instance.find('_')]
        if ci in CI_SUBS:
            self.name = self.name.replace(ci, CI_SUBS[ci])

    def load_events(self, **kwargs):
        super().load_events()
        kwargs['ft_info'].update(self.ft_info_dict)

    def _load_event(self, raw_data, **kwargs):
        raw_event = ProductRawEvent(raw_data, self.default_instance)

        if raw_event.is_building():
            return

        cooked_event = raw_event.cook()

        if Constants.FUNCTIONAL_TEST in cooked_event['stage']:
            self._load_ft_info(cooked_event)

        key = cooked_event.get_key()
        self.events[key] = cooked_event

    def _load_ft_info(self, event):
        ft_info_filename = '{0}_{1}_{2}'.format(event['instance'], event['ci'], event['release'])
        if ft_info_filename not in self.ft_info_dict:
            self.ft_info_dict[ft_info_filename] = {'features': {}, 'scenarios': {}}

        features, scenarios = FtInfo.load_ft_info(event)
        self.ft_info_dict[ft_info_filename]['features'].update(features)
        self.ft_info_dict[ft_info_filename]['scenarios'].update(scenarios)

        if 'reports' in event:
            del event['reports']


class InsDataFile(JsonDataFile):
    def _normalize_filename(self):
        if len(self.name.split('_')) < 2:
            self.name = self.name.replace('.json', '_develop.json')

    def _load_event(self, raw_data, **kwargs):
        raw_event = InsRawEvent(raw_data)

        if raw_event.is_building():
            return

        cooked_event = raw_event.cook()

        key = cooked_event.get_key()
        self.events[key] = cooked_event


class VicDataFile(JsonDataFile):
    def _normalize_filename(self):
        if 'Production' not in self.name and 'Development' not in self.name:
            self.name = 'Production_' + self.name

    def _load_event(self, raw_data, **kwargs):
        raw_event = VicRawEvent(raw_data)

        if raw_event.is_building():
            return

        cooked_event = raw_event.cook()

        key = cooked_event.get_key()
        self.events[key] = cooked_event


class VicStatusDataFile(JsonDataFile):
    def _load_event(self, raw_data, **kwargs):
        raw_event = VicStatusRawEvent(raw_data)
        cooked_events = raw_event.cook(**kwargs)

        for event in cooked_events:
            key = event.get_key()
            self.events[key] = event


class RawEvent:
    def cook(self, **kwargs):
        pass


class CookedEvent:
    def get_key(self):
        return None


class JsonDictEvent(dict):
    def __init__(self, data):
        if isinstance(data, str):
            super().__init__(**json.loads(data))
        elif isinstance(data, dict):
            super().__init__(**json.loads(json.dumps(data)))
        else:
            raise TypeError('Incompatible type for JsonEvent! Need dict or str.')


class JsonListEvent(list):
    def __init__(self, data):
        if isinstance(data, str):
            super().__init__(json.loads(data))
        elif isinstance(data, list):
            super().__init__(json.loads(json.dumps(data)))
        else:
            raise TypeError('Incompatible type for JsonEvent! Need dict or str.')


class JenkinsRawEvent(JsonDictEvent, RawEvent):
    def _get_parameters(self):
        found_parameters = {}

        try:
            actions = self['actions']
            for action in actions:
                if '_class' not in action or action['_class'] != 'hudson.model.ParametersAction':
                    continue

                parameters = action['parameters']
                for parameter in parameters:
                    name = parameter['name']
                    value = parameter['value']
                    if value == '':
                        value = 'blank'
                    found_parameters[name] = value
        except KeyError:
            pass

        return found_parameters

    def is_building(self):
        return False


class ProductRawEvent(JenkinsRawEvent):
    def __init__(self, data, default_instance):
        super().__init__(data)
        self.default_instance = default_instance

    def cook(self, **kwargs):
        cooked_event = ProductCookedEvent({})

        for field in INTERESTING_JENK%%ci33%%_FIELDS:
            if field in self:
                cooked_event[field] = self[field]

        # accounting for bug in export_jenkins (very early november, 2018)
        # AWS_Deploy and AWS_FunctionalTest stages were set to just 'AWS'
        # Stage is added to every event based on what we know
        # TODO: Do not rely on this knowledge
        if cooked_event['stage'] == 'AWS':
            full_display_name = cooked_event['fullDisplayName'].lower()

            if 'deploy' in full_display_name:
                new_stage = 'AWS_Deploy'
            elif 'func' in full_display_name:
                new_stage = 'AWS_FunctionalTest'
            else:
                raise Exception('problem: stage == AWS but full_display_name does not contain "deploy" or "func". event: {0}'.format(json.dumps(cooked_event)))

            cooked_event['stage'] = new_stage

        # if this is legacy data without the "instance" field, set it to the default
        if 'instance' not in self:
            cooked_event['instance'] = self.default_instance

        # modify the ci field if there is a substitute (ex. %%ci4%% to %%ci13%%)
        ci = cooked_event['ci']
        if ci in CI_SUBS:
            cooked_event['ci'] = CI_SUBS[ci]

        # if this is legacy data without the "ss" (subsystem) field, use the ciToSs map to set it
        if 'ss' not in cooked_event:
            cooked_event['ss'] = util.ci_to_ss[cooked_event['ci']]

        parameters = self._get_parameters()
        cooked_event.update(parameters)

        if 'baselines' in cooked_event:
            del cooked_event['baselines']

        cooked_event['release'] = self._get_release(cooked_event)
        cooked_event['iteration'] = self._get_iteration(cooked_event)

        # if this is a unit test event, slim down and pull out the report and get pass/fail/skip/total counts
        if Constants.UNIT_TEST in cooked_event['stage']:
            self._parse_unit_test_event(cooked_event)
        # if this is a functional test event, slim down and pull out the reports
        elif Constants.FUNCTIONAL_TEST in cooked_event['stage'] and 'reports' in self:
            cooked_event['reports'] = self['reports']

        if 'cause' not in cooked_event:
            cooked_event['cause'] = Constants.CAUSE_NOT_ASSIGNED

        upstream_project, upstream_build = self._get_upstream()

        if upstream_project and upstream_build:
            cooked_event['upstreamProject'] = upstream_project
            cooked_event['upstreamBuild'] = upstream_build

        cause = cooked_event['cause']
        cooked_event['derived_cause'] = self._get_derived_cause(cause)

        return cooked_event

    @staticmethod
    def _get_release(event):
        release = Constants.VERSION_NOT_ASSIGNED

        if 'BASELINE_VERSION' in event:
            release = event['BASELINE_VERSION']
        elif 'PIPELINE_VERSION' in event:
            pipeline_version = event['PIPELINE_VERSION']
            split = pipeline_version.split('.')
            if len(split) == 5:
                release = '.'.join(split[:4])

        return release

    @staticmethod
    def _get_iteration(event):
        if 'release' in event:
            release = event['release']

            if release != Constants.VERSION_NOT_ASSIGNED:
                iteration_match = ITERATION_REX.search(release)
                if iteration_match:
                    iteration = iteration_match.group()
                    return iteration

        return Constants.ITERATION_NOT_ASSIGNED

    def _get_upstream(self):
        upstream_project = None
        upstream_build = None

        if 'actions' in self:
            actions = self['actions']
            for action in actions:
                if ('_class' not in action
                        or action['_class'] != 'hudson.model.CauseAction'):
                    continue
                for cause in action['causes']:
                    if 'UpstreamCause' in cause['_class']:
                        upstream_project = cause['upstreamProject']
                        upstream_build = int(cause['upstreamBuild'])

        return upstream_project, upstream_build

    def _parse_unit_test_event(self, new_event):
        if 'report' in self:
            report = self['report']
            self._get_ut_counts_with_report(report, new_event)
        elif 'actions' in self:
            for action in self['actions']:
                if 'totalCount' in action:
                    self._get_ut_counts_with_action(action, new_event)
                    break

    @staticmethod
    def _get_ut_counts_with_report(report, new_event):
        fail_count = report['failCount']
        skip_count = report['skipCount']
        pass_count = report['passCount']
        total_count = fail_count + skip_count + pass_count

        if total_count > 0 and new_event['result'] != 'ABORTED':
            new_event['failCount'] = fail_count
            new_event['skipCount'] = skip_count
            new_event['passCount'] = pass_count
            new_event['totalCount'] = total_count

    @staticmethod
    def _get_ut_counts_with_action(action, new_event):
        fail_count = action['failCount']
        skip_count = action['skipCount']
        total_count = action['totalCount']
        pass_count = total_count - fail_count - skip_count

        new_event['failCount'] = fail_count
        new_event['skipCount'] = skip_count
        new_event['passCount'] = pass_count
        new_event['totalCount'] = total_count

    @staticmethod
    def _get_derived_cause(cause):
        cause_lower = cause.lower()
        if 'self' in cause_lower and 'service' in cause_lower:
            return 'Self-Service'
        if 'nightly' in cause_lower and '2nd' in cause_lower and 'wave' in cause_lower:
            return 'Nightly-2nd-Wave'
        if 'nightly' in cause_lower:
            return 'Nightly'
        if 'weekly' in cause_lower:
            return 'Weekly'
        if 'user' in cause_lower:
            return 'User'

        return cause

    def is_building(self):
        return 'building' in self and self['building'] is True


class ProductCookedEvent(JsonDictEvent, CookedEvent):
    def get_key(self):
        return '{0}:{1}:{2}:{3}'.format(self['ci'], self['stage'], self['number'], self['timestamp'])


class InsRawEvent(JenkinsRawEvent):
    def cook(self, **kwargs):
        cooked_event = InsCookedEvent(self)

        if 'pipeline' not in cooked_event and 'core' in cooked_event:
            cooked_event['pipeline'] = cooked_event['core']

        if 'branch' not in cooked_event:
            if 'instance' in cooked_event:
                branch = cooked_event['instance']
            else:
                branch = 'develop'

            cooked_event['branch'] = branch

        if 'stages' in cooked_event:
            for stage in cooked_event['stages']:
                if 'stageFlowNodes' in stage:
                    del stage['stageFlowNodes']

        return cooked_event

    def is_building(self):
        return 'status' in self and self['status'] == 'IN_PROGRESS'


class InsCookedEvent(JsonDictEvent, CookedEvent):
    def get_key(self):
        return '{0}:{1}:{2}:{3}'.format(self['pipeline'], self['branch'], self['id'], self['timestamp'])


class VicRawEvent(JenkinsRawEvent):
    def cook(self, **kwargs):
        cooked_event = VicCookedEvent({})

        for key, value in self.items():
            if key in ('artifacts', 'culprits', 'changeSet', 'actions'):
                continue
            cooked_event[key] = value

        parameters = self._get_parameters()
        cooked_event.update(parameters)

        if 'vic_number' in self:
            cooked_event['A_VIC'] = self['vic_number']

        if 'vic_ci' in self:
            cooked_event['ASSIGNED_CI'] = self['vic_ci']

        if 'instance' not in cooked_event:
            cooked_event['instance'] = 'Production'

        return cooked_event

    def is_building(self):
        return ('building' in self and self['building']) or ('status' in self and self['status'] == 'IN_PROGRESS')


class VicCookedEvent(JsonDictEvent, CookedEvent):
    def get_key(self):
        return '{0}:{1}'.format(self['id'], self['timestamp'])


class VicStatusRawEvent(JsonListEvent, RawEvent):
    def cook(self, **kwargs):
        cooked_events = []

        for item in self:
            event = VicStatusCookedEvent(item)

            # for legacy data
            if 'timestamp' not in event:
                event['timestamp'] = kwargs['timestamp']

            cooked_events.append(event)

        return cooked_events


class VicStatusCookedEvent(JsonDictEvent, CookedEvent):
    def get_key(self):
        return '{0}:{1}'.format(self['timestamp'], self['ci_allocation'])


class CqCookedEvent(JsonDictEvent, CookedEvent):
    def get_key(self):
        key = '{0}:{1}:{2}'.format(self['type'], self['dr_id'], self['timestamp'])

        if self['type'] == 'modify':
            key += ':{0}:{1}:{2}'.format(self['change_field'], self['before'], self['after'])

        return key


if __name__ == '__main__':
    PROCESSOR = Processor(sys.argv[1:])

    try:
        PROCESSOR.main()
    except Exception:
        PROCESSOR.logger.exception('Fatal error')
        raise
