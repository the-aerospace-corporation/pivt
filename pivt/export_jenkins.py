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
Exports data from Jenkins
"""

import time
import json
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.error import URLError
import re
import configparser
import sys
import copy
import yaml
from pivt.util import util
from pivt.util import Constants


class JenkinsExporter:
    """
    Export data from Jenkins.
    """
    def __init__(self):
        util.setup()
        self.logger = util.get_logger(self)

        self.prod_url = util.conf_manager.get('pivt', 'export_jenkins', 'jenkins_prod_url')
        self.dev_url = util.conf_manager.get('pivt', 'export_jenkins', 'jenkins_dev_url')

        bitbucket_url = util.conf_manager.get('pivt', 'export_jenkins', 'bitbucket_url')
        bitbucket_ins_project = util.conf_manager.get('pivt', 'export_jenkins', 'bitbucket_ins_project')
        bitbucket_ins_repo = util.conf_manager.get('pivt', 'export_jenkins', 'bitbucket_ins_repo')
        ins_all_cores_file = util.conf_manager.get('pivt', 'export_jenkins', 'ins_all_cores_file')

        self.ins_all_cores_repo_commits_url = '{0}/rest/api/1.0/projects/{1}/repos/{2}/commits/'.format(
            bitbucket_url, bitbucket_ins_project, bitbucket_ins_repo)
        self.ins_all_cores_file_url = '{0}/projects/{1}/repos/{2}/raw/{3}?at='.format(
            bitbucket_url, bitbucket_ins_project, bitbucket_ins_repo, ins_all_cores_file)

        self.ut_subproject_regex = re.compile(r'\n(\S+) #(\d+) completed\.')
        self.report_api = 'api/json?tree=*,testActions[*],suites[cases[' \
                          'testActions[*],age,className,duration,failedSince,name,skipped,status],' \
                          'duration,id,name,timestamp]'

        self.create_vic_number_regex = re.compile(r"Created AWS VIC '(\d+)' under IP")
        self.vic_ci_regex = re.compile(r'CI: (.+)')

        date = time.strftime('%Y%m%d%H%M%S', time.gmtime())[2:]
        base_dir = util.new_data_dir / date

        self.jenkins_dir = base_dir / 'jenkins'
        self.ins_dir = base_dir / 'ins'
        self.vic_dir = base_dir / 'vic'

        self.config = configparser.ConfigParser({'lastJobPulledTime': '0'})

        self.unpulled_builds = {}
        self.unpulled_builds_last = {}

        self.solved_causes = {}

        self.pipeline_files = {}

        self.all_cores_commits = None
        self.all_cores_files = {}

    def main(self):
        """Pull data from Jenkins."""
        self.logger.info('Python version: %s', sys.version)

        try:
            urlopen(self.prod_url)
        except URLError as err:
            self.logger.error('Could not reach Jenkins production server: %s', self.prod_url)
            self.logger.error('Error: %s', err.reason)
            self.logger.error('Quitting')
            return 1

        self.jenkins_dir.mkdir(parents=True, exist_ok=True)
        self.ins_dir.mkdir(parents=True, exist_ok=True)
        self.vic_dir.mkdir(parents=True, exist_ok=True)

        prod_sources, dev_sources, vic_prod_sources, vic_dev_sources = self.load_sources()
        ins_sources = self.load_ins_sources()
        self.load_config()

        # load file of unpulled jobs
        if util.unpulled_builds_file.exists():
            with util.unpulled_builds_file.open() as file:
                self.unpulled_builds_last = json.loads(file.read())

        self.load_all_cores_commits()

        self.pull(prod_sources, self.prod_url, Constants.PRODUCTION, '{0}/job/{1}/api/json?tree=builds[url,timestamp]',
                  self.pull_build_product, self.get_file_name_fields_product, self.jenkins_dir)
        self.pull(dev_sources, self.dev_url, Constants.DEVELOPMENT, '{0}/job/{1}/api/json?tree=builds[url,timestamp]',
                  self.pull_build_product, self.get_file_name_fields_product, self.jenkins_dir)
        self.pull(ins_sources, self.dev_url, '%%ci33%%',
                  '{0}/view/Development/view/glp/job/{1}/api/json?tree=builds[url,timestamp]',
                  self.pull_build_ins, self.get_file_name_fields_ins, self.ins_dir)
        self.pull(vic_prod_sources, self.prod_url, 'VIC', '{0}/job/{1}/api/json?tree=builds[url,timestamp]',
                  self.pull_build_vic, self.get_file_name_fields_vic, self.vic_dir)
        self.pull(vic_dev_sources, self.dev_url, 'VIC', '{0}/job/{1}/api/json?tree=builds[url,timestamp]',
                  self.pull_build_vic, self.get_file_name_fields_vic, self.vic_dir)

        util.etc_dir.mkdir(parents=True, exist_ok=True)

        # write list of currently building jobs to file
        with util.unpulled_builds_file.open('w') as file:
            file.write(json.dumps(self.unpulled_builds) + '\n')

        with util.metadata_file.open('w') as config_file:
            self.config.write(config_file)

        return 0

    @staticmethod
    def load_sources():
        """
        Load sources from sources files
        :return: sources lists
        """
        prod_sources = []
        dev_sources = []

        vic_prod_sources = []
        vic_dev_sources = []

        sources_content = JenkinsExporter.load_sources_file(util.sources_file)
        for source in sources_content:
            instance = source['instance']
            if instance == Constants.PRODUCTION:
                prod_sources.append(source)
            elif instance == Constants.DEVELOPMENT:
                dev_sources.append(source)
            else:
                prod_source = copy.deepcopy(source)
                prod_source['instance'] = Constants.PRODUCTION
                prod_sources.append(prod_source)

                dev_source = copy.deepcopy(source)
                dev_source['instance'] = Constants.DEVELOPMENT
                dev_sources.append(dev_source)

        sources_vic_content = JenkinsExporter.load_sources_file(util.sources_file_vic)
        for source in sources_vic_content:
            prod_source = copy.deepcopy(source)
            prod_source['instance'] = Constants.PRODUCTION
            vic_prod_sources.append(prod_source)

            dev_source = copy.deepcopy(source)
            dev_source['instance'] = Constants.DEVELOPMENT
            vic_dev_sources.append(dev_source)

        return prod_sources, dev_sources, vic_prod_sources, vic_dev_sources

    @staticmethod
    def load_sources_file(path):
        """
        Load one sources file.
        :param path: path to the file
        :return: content of the file as an array of dicts
        """
        content = []

        with path.open() as file:
            # load headers
            headers = []

            header_line = file.readline()
            header_names = header_line.split()
            for header_name in header_names:
                start = header_line.index(header_name)
                headers.append({'name': header_name, 'start': start})

            for i in range(1, len(headers)):
                header = headers[i]
                prev_header = headers[i - 1]
                prev_header['end'] = header['start']

            for line in file:
                row = {}

                for header in headers:
                    header_name = header['name']
                    start = header['start']

                    if 'end' in header:
                        end = header['end']
                        field = line[start:end]
                    else:
                        field = line[start:]

                    field = field.strip()
                    if field == '':
                        field = None

                    row[header_name] = field

                content.append(row)

        return content

    def load_ins_sources(self):
        url = '{0}/view/Development/view/glp/api/json?tree=jobs[name]'.format(self.dev_url)
        jobs_text = self.get_text_from_request(url, True)

        if not jobs_text:
            raise Exception('Could not pull jobs from %%ci33%% url ({0})'.format(url))

        job_names = [job['name'] for job in json.loads(jobs_text)['jobs']]

        ins_sources = []
        for job_name in job_names:
            if job_name.startswith('Platform-Patch-Pipeline-'):
                pipeline = 'Patch'
                branch = job_name[24:]
            elif job_name.startswith('Platform-Template-AllCores-Pipeline-'):
                pipeline = 'AllCores'
                branch = job_name[36:]
            else:
                continue

            ins_sources.append({'pipeline': pipeline, 'branch': branch, 'job_name': job_name})

        return ins_sources

    def load_config(self):
        """
        Load metadata config file.
        """
        if util.metadata_file.exists():
            self.config.read(str(util.metadata_file))

    def load_all_cores_commits(self):
        """
        Load commits from %%ci33%% repo.
        """
        self.logger.info('Loading AllCores commits')

        commits_str = self.get_text_from_request(self.ins_all_cores_repo_commits_url, True)

        if not commits_str:
            self.logger.warning('get request on all cores repo commits got nothing. not pulling %%ci33%%')
            return

        commits = json.loads(commits_str)

        if 'values' not in commits:
            self.logger.warning('no "values" in commits dict. not pulling %%ci33%%')
            return

        self.all_cores_commits = commits['values']

        self.logger.info('%d commits found', len(self.all_cores_commits))

    def pull(self, sources, base_url, pull_title, request_url, pull_build_func, get_source_fields_func, data_dir):
        """
        Pull data from Jenkins server.
        :param sources: list of sources to pull
        :param base_url: base URL of the server
        :param pull_title:
        :param request_url: URL to append to base_url to fetch data
        :param pull_build_func: function used to pull a single build
        :param get_source_fields_func: function used to get the source fields from a source
        :param data_dir: directory to place pulled data
        :return: total requests made and total bytes pulled
        """
        self.logger.info('==================================')
        self.logger.info('Starting pull (%s)', pull_title)

        total_requests = 0
        total_bytes_pulled = 0

        for source in sources:
            source_filename = self.get_file_name(source, get_source_fields_func)

            requests, bytes_pulled = self.pull_source(source, source_filename, data_dir, base_url, request_url,
                                                      pull_build_func)
            total_requests += requests
            total_bytes_pulled += bytes_pulled

        self.logger.info('Total requests made: %s; Total bytes pulled: %s',
                         total_requests, total_bytes_pulled)

        self.logger.info('==================================\n')

        return total_requests, total_bytes_pulled

    def pull_source(self, source, source_filename, source_data_dir, base_url, request_url, pull_build_func, **kwargs):
        """
        Pull one generic Jenkins source
        :param source: the Jenkins source from a sources file
        :param source_filename:
        :param source_data_dir: the directory to save the exported data
        :param base_url: the URL of the Jenkins instance to pull the data from
        :param request_url: Jenkins URL to request a source - expects two placeholders: one for the base URL and one
        for the job name
        :param pull_build_func: the function to use for pulling a single build
        :return: number of requests and number of bytes pulled
        """
        metrics = {'requests': 0, 'bytes_pulled': 0}

        job_name = source['job_name']

        self.logger.info('Pulling %s (%s)', source_filename, job_name)

        builds_request = request_url.format(base_url, job_name)
        builds_text = self.get_text_from_request(builds_request, True, metrics)

        if not builds_text:
            return metrics['requests'], metrics['bytes_pulled']

        builds_json = json.loads(builds_text)
        builds = builds_json['builds']
        job_class = builds_json['_class']

        file_json, _ = self.pull_builds(builds, source_filename, metrics, pull_build_func, base_url=base_url,
                                        job_class=job_class, **kwargs)

        requests = metrics['requests']
        bytes_pulled = metrics['bytes_pulled']

        self.logger.info('Requests made: %s; Bytes pulled: %s', requests, bytes_pulled)

        if file_json:
            file_json = sorted(file_json, key=lambda event: event['timestamp'])

            filename = source_data_dir / (source_filename + '.json')
            with filename.open('w') as file:
                for build in file_json:
                    file.write(json.dumps(build) + '\n')

        self.logger.info('Done.')

        return requests, bytes_pulled

    def pull_builds(self, builds, source_filename, metrics, pull_build_func, **kwargs):
        """
        Pull generic Jenkins builds for specific job.
        :param builds: list of builds to pull
        :param source_filename: filename of the source these builds belong to
        :param metrics: metrics dictionary to keep track of number of requests made and bytes pulled
        :param pull_build_func: function used to pull a single build
        :param kwargs:
        :return: list of events to write to a file and the number of builds pulled
        """
        self.logger.info('Builds available: %d', len(builds))

        file_json = []
        pulled_builds = 0

        last_job_pulled_time = self.get_last_job_pulled_time(source_filename)
        new_last_job_pulled_time = last_job_pulled_time

        # pull unpulled jobs
        unpulled_builds = []
        if source_filename in self.unpulled_builds_last:
            unpulled_builds = list(set(self.unpulled_builds_last[source_filename]))

        self.logger.info('Unpulled builds: %d', len(unpulled_builds))
        for build_url in unpulled_builds:
            build = pull_build_func(build_url, source_filename, metrics, **kwargs)

            if build:
                file_json.append(build)
                pulled_builds += 1

        self.logger.debug('Pulling new builds')
        for build in builds:
            build_timestamp = build['timestamp']
            if build_timestamp <= last_job_pulled_time:
                continue

            build_url = build['url']
            if build_url in unpulled_builds:
                continue

            build = pull_build_func(build_url, source_filename, metrics, **kwargs)

            if build:
                if build_timestamp > new_last_job_pulled_time:
                    new_last_job_pulled_time = build_timestamp

                file_json.append(build)
                pulled_builds += 1

        self.logger.info('Builds pulled: %d', pulled_builds)

        self.config.set(source_filename, 'lastJobPulledTime', str(new_last_job_pulled_time))

        return file_json, pulled_builds

    def pull_build_product(self, build_url, source_filename, metrics, **kwargs):
        """
        Pull one build from Jenkins.
        :param build_url: URL for the specific build to pull
        :param source_filename: filename of the source these builds belong to
        :param metrics: metrics dictionary to keep track of number of requests made and bytes pulled
        :param kwargs:
        :return: JSON representation of the pulled build
        """
        base_url = kwargs['base_url']

        build_json = self.pull_freestyle_build(build_url, metrics)

        if not build_json:
            return None

        if self.is_building(build_json, 'building', True):
            self.logger.debug('Currently building - skipping')
            self.add_to_unpulled(source_filename, build_url)
            return None

        source_filename_parts = source_filename.split('_')
        instance = source_filename_parts[0]
        ci = source_filename_parts[1]
        stage = source_filename_parts[2].replace('-', '_')

        if stage == 'Pipeline':
            if build_url in self.pipeline_files:
                properties = self.pipeline_files[build_url]['props']
                pipeline_json = self.pipeline_files[build_url]['json']
            else:
                self.pipeline_files[build_url] = {}

                raw_properties = self.pull_one_file('pipeline.properties', build_json, build_url, metrics, str())
                properties = self.parse_pipeline_properties(raw_properties, build_json)
                self.pipeline_files[build_url]['props'] = properties

                pipeline_json = json.loads(self.pull_one_file('pipeline.json', build_json, build_url, metrics, '{}'))
                self.pipeline_files[build_url]['json'] = pipeline_json

            build_json['pipeline_properties'] = properties
            build_json['pipeline_json'] = pipeline_json
        else:
            pipeline_url = self.get_parameter(build_json, 'PIPELINE_URL')

            files = self.get_pipeline_files(pipeline_url, metrics)
            if files == 'pipeline_building':
                self.logger.debug('Pipeline currently building - skipping')
                self.add_to_unpulled(source_filename, build_url)
                return None

            if files is not None:
                build_json['pipeline_properties'] = files['props']
                build_json['pipeline_json'] = files['json']

        build_json['ci'] = ci
        build_json['stage'] = stage
        build_json['instance'] = instance
        build_json['ss'] = util.ci_to_ss[ci]

        cause = self.get_cause(build_json, instance, base_url, metrics)
        build_json['cause'] = cause

        # pipeline_json = self.pull_one_file('pipeline.json', build_json, build_url, metrics, '{}')
        # build_json['pipeline_json'] = json.loads(pipeline_json)

        if 'FunctionalTest' in stage:
            reports = self.pull_ft(build_json, build_url, metrics)
            build_json['reports'] = reports
        elif 'UnitTest' in stage:
            report = self.pull_ut(build_url, base_url, metrics)
            if report:
                build_json['report'] = report

        return build_json

    def get_pipeline_files(self, pipeline_url, metrics):
        """
        Get pipeline.properties and pipeline.json for a specific pipeline job.
        :param pipeline_url: URL of the pipeline job
        :param metrics: metrics dictionary to keep track of number of requests made and bytes pulled
        :return: files in JSON format
        """
        if not pipeline_url:
            return None

        if pipeline_url in self.pipeline_files:
            return {
                'props': self.pipeline_files[pipeline_url]['props'],
                'json': self.pipeline_files[pipeline_url]['json']
            }

        pipeline_build_json = self.pull_freestyle_build(pipeline_url, metrics)

        if not pipeline_build_json:
            return None

        # check if pipeline build is complete
        # if not, self.add_to_building and return none
        if self.is_building(pipeline_build_json, 'building', True):
            return 'pipeline_building'

        self.pipeline_files[pipeline_url] = {}

        properties = self.pull_one_file('pipeline.properties', pipeline_build_json, pipeline_url, metrics, str())
        parsed_properties = self.parse_pipeline_properties(properties, pipeline_build_json)
        self.pipeline_files[pipeline_url]['props'] = parsed_properties

        pipeline_json = self.pull_one_file('pipeline.json', pipeline_build_json, pipeline_url, metrics, '{}')
        if pipeline_json is not None:
            pipeline_json = json.loads(pipeline_json)
        self.pipeline_files[pipeline_url]['json'] = pipeline_json

        return {'props': parsed_properties, 'json': pipeline_json}

    def pull_build_ins(self, build_url, source_filename, metrics, **kwargs):
        """
        Pull one %%ci33%% build from Jenkins.
        :param build_url: URL for the specific build to pull
        :param source_filename: filename of the source these builds belong to
        :param metrics: metrics dictionary to keep track of number of requests made and bytes pulled
        :param kwargs:
        :return: JSON representation of the pulled build
        """
        build_json = self.pull_workflow_build(build_url, source_filename, self.dev_url, metrics)

        if not build_json:
            return None

        source_filename_parts = source_filename.split('_')
        pipeline = source_filename_parts[0]
        branch = source_filename_parts[1]

        build_json['pipeline'] = pipeline
        build_json['branch'] = branch

        if pipeline == 'AllCores':
            all_cores = self.pull_ins_all_cores_file(build_json['timestamp'], metrics)
            if all_cores is not None:
                self.insert_core_info_into_build_json(build_json, all_cores)

        traditional_build_json = self.pull_freestyle_build(build_url, metrics, depth=0)
        if traditional_build_json:
            params = self.get_all_parameters(traditional_build_json)
            build_json['params'] = params

        return build_json

    def pull_ins_all_cores_file(self, build_timestamp, metrics):
        """
        Pull %%ci33%% AllCores file from %%ci33%% repository
        :param build_timestamp:
        :param metrics: metrics dictionary to keep track of number of requests made and bytes pulled
        :return: AllCores file in JSON format
        """
        if self.all_cores_commits is None:
            return None

        commit_id = None

        for commit in self.all_cores_commits:
            timestamp = commit['committerTimestamp']
            if timestamp > build_timestamp:
                continue

            commit_id = commit['id']
            break

        if commit_id is None:
            return None

        if commit_id in self.all_cores_files:
            return self.all_cores_files[commit_id]

        file_url = self.ins_all_cores_file_url + commit_id
        file_str = self.get_text_from_request(file_url, True, metrics)

        if not file_str:
            return None

        all_cores = yaml.safe_load(file_str)

        self.all_cores_files[commit_id] = all_cores

        return all_cores

    def insert_core_info_into_build_json(self, build_json, all_cores):
        """
        Insert core info from %%ci33%% AllCores file into Jenkins build
        :param build_json:
        :param all_cores:
        :return:
        """
        if all_cores is None:
            self.logger.warning('all_cores is None. build: %s', build_json['_links']['self']['href'])
            return

        if 'AllCores' not in all_cores:
            self.logger.warning('No "AllCores" at root of all_cores dict')
            return

        if len(all_cores.keys()) > 1:
            self.logger.warning('Not just "AllCores" in all_cores dict. build: %s',
                                build_json['_links']['self']['href'])

        # retrieve stages from build_json and organize them in a map
        # to more efficiently address them later
        build_stages = build_json['stages']
        build_stages_map = {}
        for stage in build_stages:
            name = stage['name']
            build_stages_map[name] = stage

        # for each stage in the all_cores file, check if a stage of the same name exists in build_stages.
        # if it does, insert the stage contents into the build_stage under a new key: "truth".
        # if it does not, create a new build stage with a sole kv pair: "truth": stage from file
        file_stages = all_cores['AllCores']
        for file_stage in file_stages:
            name = file_stage['name']

            # the YAML file is structured as a dict but is parsed as an array with the elements as members of the array
            # and the keys of the elements being inserted into the element with its value set to null.
            # this step removes those elements
            if name in file_stage:
                del file_stage[name]

            if name in build_stages_map:
                build_stage = build_stages_map[name]
                build_stage['truth'] = file_stage
            else:
                build_stages.append({'truth': file_stage})

    def pull_build_vic(self, build_url, source_filename, metrics, **kwargs):
        """
        Pull one VIC build from Jenkins.
        :param build_url: URL for the specific build to pull
        :param source_filename: filename of the source these builds belong to
        :param metrics: metrics dictionary to keep track of number of requests made and bytes pulled
        :param kwargs:
        :return: JSON representation of the pulled build
        """
        job_class = kwargs['job_class']

        if 'workflow' in job_class.lower():
            build_json = self.pull_workflow_build(build_url, source_filename, self.prod_url, metrics)
        else:
            build_json = self.pull_freestyle_build(build_url, metrics)
            if self.is_building(build_json, 'building', True):
                self.logger.debug('Currently building - skipping')
                self.add_to_unpulled(source_filename, build_url)
                return None

        if not build_json:
            return None

        instance = source_filename.split('_')[0]
        build_json['instance'] = instance

        if 'AWS-VIC-Manager' in source_filename and 'actions' in build_json:
            action = self.get_parameter(build_json, 'ACTION')

            console_request = build_url + '/consoleText'
            console_text = self.get_text_from_request(console_request, False, metrics)

            if console_text:
                if action == 'create-vic':
                    vic_number_match = self.create_vic_number_regex.search(console_text)
                    if vic_number_match:
                        vic_number = vic_number_match.group(1)
                        build_json['vic_number'] = int(vic_number)
                else:
                    vic_ci_match = self.vic_ci_regex.search(console_text)
                    if vic_ci_match:
                        vic_ci = vic_ci_match.group(1)
                        build_json['vic_ci'] = vic_ci
            else:
                self.logger.warning('no console text for %s', build_url)

        return build_json

    def get_cause(self, event, instance, base_url, metrics):
        """
        Get the cause of an event using the following algorithm:

            1.	If the cause is an "UpstreamCause" (meaning this job was kicked off by another), we get the name of
                that job
                a.	If the words ‘self’ and ‘service’, or ‘nightly’, or ‘weekly’ are in that job name, the cause is
                    set to that job name (e.g. Self-Service, Nightly-Builds, Nightly-%%ci27%%-Core, Weekly-Builds)
                b.	Else, get the name of the upstream job
                     i. If the upstream job is in solved_causes, use that cause
                    ii. Else, pull the upstream job and start from the beginning with that job (the algorithm is
                        recursive)
            2.	Else if the cause is a "UserIdCause", set the cause to "user"
            3.	Else, set the cause to "Not Assigned"

        When a cause is determined, it is cached in solved_causes

        :param event: the Jenkins event to get the cause from
        :param instance: the Jenkins instance the event is from
        :param base_url: the URL of the Jenkins instance to pull the data from
        :param metrics: metrics dictionary to keep track of number of requests made and bytes pulled
        :return: the cause of the event
        """
        if 'actions' not in event:
            return Constants.CAUSE_NOT_ASSIGNED

        project_name = self.get_project_name(event)
        build_number = int(event['number'])

        event_key = self.get_causes_event_key(project_name, build_number)

        if instance in self.solved_causes and event_key in self.solved_causes[instance]:
            return self.solved_causes[instance][event_key]

        actions = event['actions']
        for action in actions:
            if '_class' not in action or action['_class'] != 'hudson.model.CauseAction':
                continue

            for cause in action['causes']:
                cause_class = cause['_class']

                if 'UpstreamCause' in cause_class:
                    upstream_project = cause['upstreamProject']
                    upstream_project_lower = upstream_project.lower()

                    if (('self' in upstream_project_lower and 'service' in upstream_project_lower) or
                            'nightly' in upstream_project_lower or
                            'weekly' in upstream_project_lower):
                        self.save_cause(event_key, upstream_project, instance)
                        return upstream_project

                    upstream_build = cause['upstreamBuild']

                    upstream_event_key = self.get_causes_event_key(upstream_project, upstream_build)
                    if instance in self.solved_causes and upstream_event_key in self.solved_causes[instance]:
                        cause_name = self.solved_causes[instance][upstream_event_key]
                        self.save_cause(event_key, cause_name, instance)
                        return cause_name

                    upstream_url = cause['upstreamUrl']

                    build_request = '{0}/{1}/{2}/api/json'.format(base_url, upstream_url, upstream_build)
                    build_text = self.get_text_from_request(build_request, True, metrics)

                    if build_text:
                        build_json = json.loads(build_text)
                        cause_name = self.get_cause(build_json, instance, base_url, metrics)
                        self.save_cause(event_key, cause_name, instance)
                        return cause_name
                elif 'UserIdCause' in cause_class:
                    cause_name = 'user'
                    self.save_cause(event_key, cause_name, instance)
                    return cause_name

        return Constants.CAUSE_NOT_ASSIGNED

    @staticmethod
    def get_project_name(event):
        """
        Get the project name of an event.
        It's often found in the 'fullDisplayName' attribute, along with the build number. Ex: '%%ci16%%-Build #213'
        If it's not found in 'fullDisplayName', look in the URL. Ex: 'http://<server>:<port>/job/%%ci16%%-Build/213/
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

    def save_cause(self, event_key, cause, instance):
        """
        Save the cause of an event to the solved_causes dictionary.
        :param event_key: key to use for the event
        :param cause:
        :param instance: the Jenkins instance the event is from
        :return:
        """
        if instance not in self.solved_causes:
            self.solved_causes[instance] = {}
        self.solved_causes[instance][event_key] = cause

    @staticmethod
    def get_causes_event_key(project_name, number):
        """
        Generate key for an event for use in the solved_causes dictionary.
        :param project_name: name of the Jenkins "project" (job) the event came from
        :param number: the build number of the event
        :return: the key
        """
        return '{0}:{1}'.format(project_name, number)

    def parse_pipeline_properties(self, properties, build_json):
        """
        Parse pipeline.properties file into JSON format.
        :param properties: pipeline.properties file in string format
        :param build_json: build info
        :return: pipeline.properties file in JSON format
        """
        props_dict = {}

        if not isinstance(properties, str):
            self.logger.warning('properties argument is not a string! type is %s', type(properties))
            return props_dict

        for line in properties.splitlines():
            parts = line.split('=')
            key = parts[0].strip()
            value = parts[1].strip()

            if key in props_dict:
                self.logger.warning('key %s is a duplicate. existing value: %s, new value: %s. overwriting. build number: %d',
                                    key, props_dict[key], value, build_json['number'])

            props_dict[key] = value

        return props_dict

    def pull_one_file(self, filename, build_json, build_url, metrics, default):
        """
        Pull one file for a build.
        :param filename: name of the file to pull
        :param build_json:
        :param build_url: the URL of the build
        :param metrics: metrics dictionary to keep track of number of requests made and bytes pulled
        :param default: what to return if nothing matching filename is found
        :return: the pipeline.json data
        """
        self.logger.debug('Pulling %s', filename)

        if 'artifacts' not in build_json:
            return default

        artifacts = build_json['artifacts']
        matching_files = list(filter(lambda x: x['fileName'] == filename, artifacts))
        if not matching_files:
            return default

        matching_files_count = len(matching_files)
        if matching_files_count > 1:
            self.logger.warning('Multiple %s files for %s; count: %d; list: %s', filename, build_url,
                                matching_files_count, matching_files)
        relative_path = matching_files[0]['relativePath']
        return self.pull_artifact(build_url, relative_path, metrics)

    def pull_ft(self, build_json, build_url, metrics):
        """Pull all functional test reports for a build."""
        self.logger.debug('Pulling FT data')

        reports = {}

        artifacts = build_json['artifacts']
        if artifacts:
            for artifact in artifacts:
                if not artifact:
                    continue
                relative_path = artifact['relativePath']
                report = self.pull_ft_report_artifact(build_url, relative_path, metrics)
                if not report:
                    continue
                if relative_path not in reports:
                    reports[relative_path] = report

        triggered_builds = []

        actions = build_json['actions']
        for action in actions:
            if 'triggeredBuilds' in action:
                triggered_builds = action['triggeredBuilds']
                break

        for triggered_build in triggered_builds:
            reports_temp = self.pull_ft_triggered_build(triggered_build, metrics)
            for report_url, report in reports_temp.items():
                if report_url not in reports:
                    reports[report_url] = report

        return reports

    def pull_ft_report_artifact(self, build_url, relative_path, metrics):
        """Pull functional test report for a build."""
        if not relative_path.endswith('.json'):
            return None

        self.logger.debug('Pulling FT report %s', relative_path)

        report_text = self.pull_artifact(build_url, relative_path, metrics)

        if report_text:
            try:
                report = json.loads(report_text)
                return report
            except ValueError:
                pass

        return None

    def pull_artifact(self, build_url, relative_path, metrics):
        """Pull artifact for a build."""
        self.logger.debug('Pulling artifact %s', relative_path)
        report_url = build_url + '/artifact/' + relative_path
        return self.get_text_from_request(report_url, True, metrics)

    def pull_ft_triggered_build(self, triggered_build, metrics):
        """Pull data for a triggered build."""
        reports = {}

        if not triggered_build:
            return reports

        try:
            triggered_build_url = triggered_build['url']
            self.logger.debug('Pulling triggered build %s', triggered_build_url)
        except KeyError:
            self.logger.warning('Triggered build has no url:\n%s', json.dumps(triggered_build))
            return reports

        artifacts_request = triggered_build_url + '/api/json?tree=artifacts[relativePath,fileName]'
        artifacts_text = self.get_text_from_request(artifacts_request, True, metrics)

        if not artifacts_text:
            return reports

        artifacts_json = json.loads(artifacts_text)
        artifacts = artifacts_json['artifacts']

        for artifact in artifacts:
            relative_path = artifact['relativePath']
            report = self.pull_ft_report_artifact(triggered_build_url, relative_path, metrics)
            if not report:
                continue
            if relative_path not in reports:
                reports[relative_path] = report

        return reports

    def pull_ut(self, build_url, base_url, metrics):
        """Pull unit test report for a build."""
        report_request = '{0}/testReport/{1}'.format(build_url, self.report_api)
        report_text = self.get_text_from_request(report_request, False, metrics)

        if report_text:
            report = json.loads(report_text)
        else:
            report = self.pull_ut_subprojects(build_url, base_url, metrics)

        return report

    def pull_ut_subprojects(self, build_url, base_url, metrics):
        """Pull unit test report from a build's subprojects."""
        report = None

        console_text_request = build_url + '/consoleText'
        console_text = self.get_text_from_request(console_text_request, False, metrics)

        if console_text:
            report = {'duration': 0, 'failCount': 0, 'passCount': 0, 'skipCount': 0, 'suites': []}

            sub_projects = self.ut_subproject_regex.findall(console_text)
            for sub_project in sub_projects:
                self.pull_ut_report_from_subproject(sub_project, report, base_url, metrics)

            if report['duration'] == 0:
                report = None
        else:
            self.logger.warning('no console text for %s', build_url)

        return report

    def pull_ut_report_from_subproject(self, sub_project, report, base_url, metrics):
        """Pull unit test report from a subproject."""
        sub_project_report_url = '{0}/job/{1}/{2}/testReport/{3}'.format(base_url, sub_project[0],
                                                                         sub_project[1], self.report_api)
        sub_report_str = self.get_text_from_request(sub_project_report_url, False, metrics)

        if sub_report_str:
            sub_report = json.loads(sub_report_str)

            report['duration'] += sub_report['duration']
            report['failCount'] += sub_report['failCount']
            report['passCount'] += sub_report['passCount']
            report['skipCount'] += sub_report['skipCount']
            report['suites'] += sub_report['suites']

    def pull_freestyle_build(self, build_url, metrics, depth=1):
        """Pull generic Jenkins freestyle build."""
        self.logger.debug('Pulling %s', build_url)

        build_request = build_url + '/api/json?depth={0}'.format(depth)
        build_text = self.get_text_from_request(build_request, True, metrics)

        if not build_text:
            return None

        build_json = json.loads(build_text)

        return build_json

    def pull_workflow_build(self, build_url, filename, base_url, metrics):
        """Pull generic Jenkins workflow build."""
        self.logger.debug('Pulling %s', build_url)

        build_request = build_url + '/wfapi'
        build_text = self.get_text_from_request(build_request, True, metrics)

        if not build_text:
            return None

        build_json = json.loads(build_text)

        if self.is_building(build_json, 'status', 'IN_PROGRESS'):
            self.logger.debug('Currently building - skipping')
            self.add_to_unpulled(filename, build_url)
            return None

        build_json['timestamp'] = build_json['startTimeMillis']

        stages = build_json['stages']

        for i, stage in enumerate(stages):
            stages[i] = self.pull_workflow_build_stage(stage, base_url, metrics)

        return build_json

    def pull_workflow_build_stage(self, old_stage, base_url, metrics):
        """
        Pull a stage of a Jenkins workflow build.
        :param old_stage: the original stage
        :param base_url: the URL of the Jenkins instance to pull the data from
        :param metrics: metrics dictionary to keep track of number of requests made and bytes pulled
        :return: the modified stage
        """
        stage = copy.deepcopy(old_stage)

        try:
            stage_url = stage['_links']['self']['href']
        except KeyError:
            return stage

        stage_request = base_url + '/' + stage_url
        stage_text = self.get_text_from_request(stage_request, True, metrics)

        if not stage_text:
            return stage

        stage_json = json.loads(stage_text)

        stage_flow_nodes = stage_json['stageFlowNodes']

        for node in stage_flow_nodes:
            self.pull_stage_flow_node(node, base_url, metrics)

        return stage_json

    def pull_stage_flow_node(self, node, base_url, metrics):
        """
        Pull a "stage flow node" of a Jenkins workflow build stage.
        :param node:
        :param base_url: the URL of the Jenkins instance to pull the data from
        :param metrics: metrics dictionary to keep track of number of requests made and bytes pulled
        :return:
        """
        try:
            node_log_url = node['_links']['log']['href']
        except KeyError:
            return

        node_log_request = base_url + '/' + node_log_url
        node_log_text = self.get_text_from_request(node_log_request, False, metrics)

        if node_log_text:
            node_log_json = json.loads(node_log_text)
            if 'text' in node_log_json:
                node['log'] = node_log_json['text']

    @staticmethod
    def is_building(build, building_field, building_value):
        """
        Check if a build is currently building. If it is, add it to the unpulled_builds dict.
        :param build:
        :param building_field: the field in the raw data that tells us if the build is currently building
        :param building_value: the value that building_field has to be for this build to be currently building
        :return: True if currently building, False otherwise
        """
        if build is not None and building_field in build and build[building_field] == building_value:
            return True
        return False

    def add_to_unpulled(self, file_name, build_url):
        """
        Add build info to unpulled dictionary.
        :param file_name: name of the file the build would be written to
        :param build_url:
        """
        if file_name not in self.unpulled_builds:
            self.unpulled_builds[file_name] = []
        if build_url not in self.unpulled_builds[file_name]:
            self.unpulled_builds[file_name].append(build_url)

    @staticmethod
    def get_file_name(source, get_fields_func):
        """Get long name of a source."""
        return '_'.join(get_fields_func(source))

    @staticmethod
    def get_file_name_fields_product(source):
        """
        Get file name fields from a product source.
        :param source:
        :return: the fields
        """
        fields = [source['instance'], source['ci'], source['stage'].replace('_', '-')]

        tags = source['tags']
        if tags is not None:
            fields.extend(tags.split(','))

        return fields

    @staticmethod
    def get_file_name_fields_ins(source):
        """
        Get file name fields from an %%ci33%% source.
        :param source:
        :return: the fields
        """
        return [source['pipeline'], source['branch'].replace('_', '-')]

    @staticmethod
    def get_file_name_fields_vic(source):
        """
        Get file name fields from a VIC source.
        :param source:
        :return: the fields
        """
        return [source['instance'], source['job_name']]

    def get_last_job_pulled_time(self, long_name):
        """Get lastjobpulledtime for a source from the config."""
        if not self.config.has_section(long_name):
            self.config.add_section(long_name)
        return int(self.config.get(long_name, 'lastJobPulledTime'))

    @staticmethod
    def get_parameter(build_json, name):
        """
        Get a parameter from a Jenkins build.
        :param build_json:
        :param name: name of the parameter
        :return: the parameter value
        """
        if 'actions' in build_json:
            actions = build_json['actions']
            for action in actions:
                if '_class' not in action or action['_class'] != 'hudson.model.ParametersAction':
                    continue

                for parameter in action['parameters']:
                    if parameter['name'] == name:
                        return parameter['value']

        return None

    @staticmethod
    def get_all_parameters(build_json):
        """
        Get all parameters from a Jenkins build.
        :param build_json:
        :return: dictionary of parameters
        """
        params = {}

        if 'actions' in build_json:
            actions = build_json['actions']
            for action in actions:
                if '_class' not in action or action['_class'] != 'hudson.model.ParametersAction':
                    continue

                for parameter in action['parameters']:
                    params[parameter['name']] = parameter['value']

        return params

    def get_text_from_request(self, request, show_warning, metrics=None):
        """Make a GET request and record metrics about the request."""
        self.logger.debug('Getting %s', request)

        content = None

        try:
            content = str(util.get(request), 'utf-8', 'replace')

            if metrics and 'requests' in metrics and 'bytes_pulled' in metrics:
                metrics['requests'] += 1
                metrics['bytes_pulled'] += len(content)
        except (HTTPError, URLError):
            if show_warning:
                self.logger.warning('%s not found', request)

        return content


if __name__ == '__main__':
    EXPORTER = JenkinsExporter()

    try:
        EXPORTER.main()
    except Exception:
        EXPORTER.logger.exception('Fatal error')
        raise
