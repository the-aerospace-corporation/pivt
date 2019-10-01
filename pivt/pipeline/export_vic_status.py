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

import json
import time
from functools import partial
from pathlib import Path
import pipe_core as pc

class VicStatusLogger:
    pass

def create_vic_status_pipeline(source, target):
    # Initial setup of the vic status pipeline context and other data
    context = pc.Context()
    timestamp = time.time()
    gmtime = time.gmtime(timestamp)
    date = time.strftime('%Y%m%d%H%M%S', gmtime)[2:]
    target_dir = target / date / 'vic_status'
    target_path = target_dir / ('{}.json'.format(target))

    ## STAGES OF THE PIPELINE

    # Define the reader
    #reader, context = pc.create_url_reader(source, context)
    reader, context = pc.create_file_reader(path=source, context=context)

    # Create the target directory
    def dir_creator(data, context):
        target_dir.mkdir(parents=True, exist_ok=True)
        return data

    # Take the raw data from the previous stage and parse it as json
    def parser(raw_data, context):
    #    logger.info('Parsing data')
        return json.loads(raw_data)

    # Take the items from the previous stage and add a timestamp field
    def timestamper(items, context):
        for item in items:
            item['timestamp'] = timestamp
        return items

    # Convert the data from the previous stage to JSON
    def serializer(items, context):
        return json.dumps(items)

    # Define the writer
    writer, context = pc.create_file_writer(
        path=target_path,
        newline=True,
        context=context
    )

    ## PIPELINE CREATION

    vic_status_pipeline = pc.Pipeline(context)
    vic_status_pipeline.connect_transforms(
        [
            reader,
            dir_creator,
            parser,
            timestamper,
            serializer,
            writer
        ]
    )

    return vic_status_pipeline

vic_status_pipeline = create_vic_status_pipeline('test_in.json', Path('test_out'))
vic_status_pipeline.run()
