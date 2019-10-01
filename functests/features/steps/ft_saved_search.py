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
import sys
from time import sleep
import traceback
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
	password=PASSWORD,
	app='pivt')

@when('the search is run with nominal={nominal} and tag={tag}')
def step_search(context, nominal, tag):
	try:
		kwargs_oneshot = {
			'earliest_time': '2019-04-30T00:00:00',
			'latest_time': '2019-04-30T23:59:59'
		}

		searchquery_oneshot = '| savedsearch "PIVT Jenkins FT Scenarios" instance="Production" nominal="{0}" tag="{1}"'.format(nominal, tag)

		context.results = service.jobs.oneshot(searchquery_oneshot, **kwargs_oneshot)
	except Exception:
		print(traceback.format_exc())
		assert False

@then('the results should be')
def step_compare_results(context):
	try:
		table = {}
		for row in context.table:
			row_dict = {}

			for heading in row.headings:
				row_dict[heading] = row[heading]

			table[row_dict['number']] = row_dict

		reader = results.ResultsReader(context.results)
		results_count = 0

		for item in reader:
			results_count += 1

			expected = table[item['number']]
			for field, value in expected.items():
				assert item[field] == value

		assert results_count == len(table)
	except Exception:
		print(traceback.format_exc())
		assert False
