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
import subprocess
import splunklib.client as client

HOST = os.environ['PIVT_HOST']
PORT = "8089"
USERNAME = "ft-user"
PASSWORD = "ft-user"


@given('splunk container is up and running')
def step_impl(context):
	status = subprocess.check_output(["ping", "-c", "1", HOST])
	assert status is not False


@then('login to splunk')
def step_impl(context):
	service = client.connect(
		host=HOST,
		port=PORT,
		username=USERNAME,
		password=PASSWORD)

	app_names = [app.name for app in service.apps]
	assert 'pivt' in app_names
	assert 'random_name' not in app_names
