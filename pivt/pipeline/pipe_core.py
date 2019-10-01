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

from functools import partial
from urllib.request import urlopen
import inspect

class Pipeline:
    """
    Orchestrates collections of stages and junctions.

    This class is a collection of stages and junctions and has methods and properties for
    building and controlling the execution of a pipeline.
    """
    def __init__(self, context = None):
        self.stages = []
        self.context = context

    def _pick_path(self, path):
        """
        Private function used for picking branches in the pipeline.

        :param path: A pair consisting of (predicate function, pipeline)
        """
        predicate = path[0]
        pipeline = path[1]
        if predicate(data):
            return pipeline.run(data)
        return False

    def connect_branch_junction(self, predicates, pipelines):
        """
        Connects a branching junction to the end of the pipeline.

        This method attempts to assign predicates to pipelines by index. If the lengths
        of the predicates and pipelines do not match, assignments will take place up to the
        last element in the shorter list.

        :param predicates: A list of functions that take one argument and return true or false
        :param pipelines: A list of pipelines to transfer control to based on the predicates
        """
        def branch_junction(data):
            """
            A branch junction will send data to every pipeline where the associated predicate returns true.

            :param data: The input data
            :return: A map object that will execute the associated pipeline for every predicate that returned true.
            """
            return map(self._pick_path, zip(predicates, pipelines))
        self.stages.append(branch_junction)

    def connect_select_junction(self, predicates, pipelines):
        """
        Connects a select junction to the end of the pipeline.

        This method attempts to assign predicates to pipelines by index. If the lengths
        of the predicates and pipelines do not match, assignments will take place up to the
        last element in the shorter list.

        :param predicates: A list of functions that take one argument and return true or false
        :param pipelines: A list of pipelines to transfer control to based on the predicates
        :return: A function that executes a branch junction
        """
        def select_junction(data):
        """
        A selection junction will send data to the first pipeline where the associated predicate
        returns true.

        :param data: The input data
        :return: The pipeline return data associated with the first predicate that returned True or
                 False if no predicate returned True.
        """

            for path in zip(predicates, pipelines):
                data = self.pick_path(path)
                if data:
                    return data
            return False
        self.stages.append(select_junction)

    def connect_binary_junction(self, predicate, true_pipeline, false_pipeline):
        """
        Connects a binary junction to the end of the pipeline.

        :param predicate: A function that takes one argument and returns True or False.
        :param true_pipeline: The pipeline that is executed if the predicate returns True.
        :param false_pipeline: The pipeline that is executed if the predicate returns False.
        """
        def binary_junction(data):
            """
            This method returns the output of one of two pipelines depending on the output of the predicate.

            :param data: The input data
            :return: The return value of the true_pipeline if predicate returned True, otherwise the
                     value of the false_pipeline.
            """
            if predicate(data):
                return true_pipeline.run(data)
            return false_pipeline.run(data)
        self.stages.append(binary_junction)

    def connect_transforms(self, transforms):
        """
        Extends the stages of the pipeline with a list of transformation stages.

        :param transforms: A list of transformation stages
        """
        self.stages.extend(transforms)

    def connect_transform(self, transform):
        """
        Extends the stages of the pipeline with a transformation stage.

        :param transform: A single transformation stage
        """
        self.stages.append(transform)

    def run(self, seed=None):
        """
        Execute the stages in the pipeline in order.

        :param seed: Seed for the data
        """
        data = seed
        for stage in self.stages:
            try:
                new_data = stage(data, self.context)
                data = new_data
            except ValueError:
                # Log error in pipeline
                pass
        return data

class Context:
    """
    Used for keeping track of various stage options and pipeline states.

    This is meant to be an extremely flexible system for keeping track of the state of the pipeline.
    It is up to the developer not to abuse the context object and make things too obscure to follow.
    """
    def __init__(self):
        self.option_id = 0
        self.options = {}
        self.data = {}

    def add_options(self, kv_pairs):
        """
        Adds options to the context.

        The passed in options will be automatically assigned a unique id. This should be
        used within the stage to keep track of how it accesses its options.

        :param kv_pairs: A dictionary that represents options for a specfic stage.
        :return: The context object and the unique id for these options.
        """
        self.options[self.option_id] = {}
        self.options[self.option_id].update(kv_pairs)
        this_option_id = self.option_id
        self.option_id += 1
        return self, this_option_id

# Verification functions
def verify_context(context, function_name):
    """
    Verify that the context exists.

    :param context: A context object
    :param function_name: The developer friendly name for the caller of this function
    :raise: ValueError if context object is None
    """
    if context is None:
        raise ValueError('Argument context cannot be None when creating a {}'.format(function_name))

# Readers
def create_terminal_reader(prompt=None, context=None):
    """
    Create a terminal reader with the given prompt.

    :param prompt: <string> to prompt you
    :param context: A context object that will be assigned the given prompt
    :return: A function that reads from the terminal and the modified context object
    """
    verify_context(context, 'terminal reader')
    context, options_id = context.add_options({
        'prompt': prompt
    })
    def reader(data, context):
        """
        Prompts the user and return user input.

        :param data: Used only to match the stage interface
        :param context: A context object
        :return: The user input
        """
        prompt = context.options[options_id]['prompt']
        return input(prompt)

    return reader, context

def create_file_reader(path=None, mode='r', context=None):
    """
    Create a file reader with the given path.

    :param path: The path to the file to be read
    :param mode: The mode of the file reader
    :param context: A context object that will be assigned the given path and mode for this reader
    :return: A function that reads a file for a path and the modified context object
    """
    verify_context(context, 'file reader')
    context, options_id = context.add_options({
        'path': path,
        'mode': mode
    })
    def reader(data, context):
        path = context.options[options_id]['path']
        mode = context.options[options_id]['mode']
        with open(path, mode) as fd:
           return fd.read()

    return reader, context

def create_url_reader(url=None, context=None):
    """
    Create a url reader from the given url

    :param url: The url to read data from
    :param context: A context object that will be assigned a url for this reader
    :return: A function that reads data from a url, and the modified context object
    """
    verify_context(context, 'url reader')
    context, options_id = context.add_options({
        'url': url
    })
    def reader(data, context):
        url = context.options[options_id]['url']
        return urlopen(url).read()

    return reader, context

# Writers
def create_terminal_writer(context=None):
    """
    Create a terminal writer

    :return: A function that prints the given data
    """
    verify_context(context, 'terminal writer')
    def writer(data, context):
        print(data)
        return data

    return writer, context

def create_file_writer(path=None, mode='a+', newline=False, context=None):
    """
    Create a file reader with the given path.

    :param path: The path to the file to write to (optional)
    :return: A function that writes to a file for a path
    """
    verify_context(context, 'file writer')
    context, options_id = context.add_options({
        'path': path,
        'mode': mode,
        'newline': newline
    })
    def writer(data, context):
        """
        Write data to a file

        :data: Data to write
        :context: A context object that should contain the path, mode and newline option for
                  the writer.
        """
        path = context.options[options_id]['path']
        mode = context.options[options_id]['mode']
        newline = context.options[options_id]['newline']
        with open(path, mode) as fd:
            if newline:
                data += '\n'
            fd.write(data)

    return writer, context


# Helpful stage creation functions
def verify_stage(func):
    """
    Verify that the passed in value can qualify as a stage.

    :param func: A function with 1 input parameter.
    :return: None.
    :raise: ValueError if func does not qualify as a stage.
    """
    if inspect.isfunction(func): return
    raise ValueError('{} does not qualify as a stage.'.format(func))

def create_custom_stage(func):
    """
    Create a completely custom stage.

    :param func: A function with 1 input parameter.
    :return: The passed in function unmodified.
    :raise: ValueError if func does not qualify as a stage.
    """
    verify_stage(func)
    return func

def create_packing_stage(func):
    """
    Create a stage that packs data with the value of func(data).

    :param func: A function with 1 input parameter.
    :return: Return a stage that returns data in the form (data, func(data))
    :raise: ValueError if func does not qualify as a stage.
    """
    verify_stage(func)
    return lambda data: (data, func(data))


# Utility functions
def collection_version(func):
    """
    Creates a function that applies to a collection.

    :param func: A function that takes one argument
    :return: A function that takes a list and applies func to each item
    """
    def apply_func_to_collection(data):
        for elem in data:
            func(elem)

    return apply_func_to_collection

def filter_dict(d, f):
    return {k: v for k, v in d.items() if f(v)}

def filter_dict_none(d):
    return filter_dict(d, lambda v: v is not None)