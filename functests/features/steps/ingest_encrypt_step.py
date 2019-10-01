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

from behave import *
import os
import json
import splunklib.client as client
import splunklib.results as results

HOST = os.environ['PIVT_HOST']
PORT = "8089"
USERNAME = "ft-user"
PASSWORD = "ft-user"
DATA_PATH = '/app/ft-data/data/'
APP_PATH = '/app/pivt/var/data/data/'

# connect to splunk
service = client.connect(
	host=HOST,
	port=PORT,
	username=USERNAME,
	password=PASSWORD)

@given('{files} exist in the "{folder}" folder')
def step_files_exist(context, files, folder):
	files = json.loads(files)

	for file in files:
		if not os.path.exists(DATA_PATH + folder + '/' + file):
			print('file not found', file)
			assert False
	# assert True

@given('{files} have the same 256 bytes in the "{folder}" folder')
def step_compare_first_256_bytes(context, files, folder):
	file_paths = [DATA_PATH + folder + '/' + filename for filename in json.loads(files)]
	files = [open(file_path).read() for file_path in file_paths]

	byte_count = 0

	for chars in zip(*files):
		for i in range(len(chars)):
			for j in range(i + 1, len(chars)):
				if (byte_count <= 255) and (chars[i] == chars[j]):
					byte_count += 1
				elif (byte_count > 255):
					assert True
					break
				else:
					print('first 256 bytes do not match')
					assert False
					break

@then('{files} should be in "{index}" splunk index and "{folder}" folder')
def step_find_file_in_splunk(context, files, index, folder):
	sources = set()
	files = {APP_PATH + folder + '/' + filename for filename in json.loads(files)}

	kwargs_oneshot = {
		'earliest_time': 0,
		'latest_time': 'now',
		'count': 0
	}

	searchquery_oneshot = "search index={0} | stats count by source".format(index)

	oneshotsearch_results = service.jobs.oneshot(searchquery_oneshot, **kwargs_oneshot)

	reader = results.ResultsReader(oneshotsearch_results)
	for item in reader:
		for key, value in item.items():
			if key != 'source':
				continue
			sources.add(value)

	assert files <= sources
