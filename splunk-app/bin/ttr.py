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

from __future__ import absolute_import, division, print_function, unicode_literals
from splunklib.searchcommands import dispatch, EventingCommand, Configuration, Option, validators
import sys
import operator


@Configuration()
class TtrCommand(EventingCommand):
    """ Computes the time-to-repair (TTR) of a set of fields.

    ##Syntax

    .. code-block::
        ttr ttrfield=<field> resultfield=<field> passvalue=<value> <field-list>

    ##Example

    ..code-block::
        ttr ttrfield=ttr resultfield=result passvalue=SUCCESS instance ci stage release
    """
    ttrfield = Option(
        doc='''
        **Syntax:** **ttrfield=***<fieldname>*
        **Description:** Name of the field that will hold the computed TTR
        ''',
        require=True, validate=validators.Fieldname())

    resultfield = Option(
        doc='''
        **Syntax:** **resultfield=***<fieldname>*
        **Description:** Name of the field that holds the result of the event
        ''',
        require=True, validate=validators.Fieldname())

    passvalue = Option(
        doc='''
        **Syntax:** **passvalue=***<value>*
        **Description:** Value that *resultfield* needs to be to consider an event to be passing
        ''',
        require=True)

    timefield = Option(
        doc='''
        ''',
        default='_time', require=False, validate=validators.Fieldname())

    lookbeyondboundary = Option(
        doc='''
        ''',
        default=False, require=False, validate=validators.Boolean())


    def transform(self, records):
        earliest_time = self.metadata.searchinfo.earliest_time
        by_fieldnames = self.fieldnames

        self.logger.debug('ttrfield: %s, resultfield: %s, passvalue: %s, timefield: %s, lookbeyondboundary: %s, fieldnames: %s, earliest: %s', self.ttrfield, self.resultfield, self.passvalue, self.timefield, self.lookbeyondboundary, by_fieldnames, earliest_time)

        # get all events needed for TTR calculation
        if self.lookbeyondboundary:
            events_for_ttr = self.get_events_for_ttr(records, earliest_time, by_fieldnames)
        else:
            events_for_ttr = list(records)

        # calculate TTR
        sort_by_args = list(by_fieldnames)
        sort_by_args.append(self.timefield)
        events_for_ttr.sort(key = operator.itemgetter(*sort_by_args))

        metadata = {}
        self.init_metadata(metadata)

        last_by_fields = []

        for event in events_for_ttr:
            by_fields = self.get_by_fields(by_fieldnames, event)
            if by_fields != last_by_fields:
                self.init_metadata(metadata)

            ttr = self.calc_single_ttr(float(event[self.timefield]), event[self.resultfield], metadata)
            event[self.ttrfield] = ttr

            last_by_fields = by_fields

        final_events = []
        events_for_ttr.sort(key = operator.itemgetter(self.timefield), reverse=True)

        for event in events_for_ttr:
            timestamp = float(event[self.timefield])
            if self.lookbeyondboundary and timestamp < earliest_time:
                # throw away events before earliest_time
                break
            final_events.append(event)

        return final_events


    def get_events_for_ttr(self, records, earliest_time, by_fieldnames):
        events_for_ttr = []

        metadata = {}
        within_time_window = True

        last_timestamp = -1

        for record in records:
            timestamp = float(record[self.timefield])

            # make sure timestamps are decreasing
            if last_timestamp != -1 and timestamp > last_timestamp:
                raise Exception('events aren\'t in decreasing time order!')

            last_timestamp = timestamp

            result = record[self.resultfield]
            by_fields = self.get_by_fields(by_fieldnames, record)
            key = self.gen_ttr_prep_metadata_key(by_fields)

            if timestamp >= earliest_time:
                events_for_ttr.append(record)

                if key not in metadata:
                    metadata[key] = {'last_result': None, 'staged_events': [], 'has_success': False}

                combo = metadata[key]

                combo['last_result'] = result
                if result == self.passvalue:
                    combo['has_success'] = True
            else:
                if within_time_window:
                    for key in metadata.keys():
                        combo = metadata[key]
                        if not combo['has_success']:
                            del metadata[key]

                    within_time_window = False

                if not metadata:
                    break

                if key in metadata:
                    combo = metadata[key]
                    combo['staged_events'].append(record)
                    if result == self.passvalue:
                        events_for_ttr += combo['staged_events']
                        del metadata[key]

        return events_for_ttr


    @staticmethod
    def gen_ttr_prep_metadata_key(by_fields):
        key = ''
        for by_field in by_fields:
            key += by_field + ':'
        return key[:-1]


    @staticmethod
    def init_metadata(metadata):
        metadata['last_result'] = ''
        metadata['first_failure_time'] = 0
        metadata['encountered_success'] = False

    def calc_single_ttr(self, timestamp, result, metadata):
        ttr = None

        last_result = metadata['last_result']
        first_failure_time = metadata['first_failure_time']
        encountered_success = metadata['encountered_success']

        if not encountered_success and self.passing(result):
            metadata['encountered_success'] = True

        if (self.passing(last_result) or last_result == '') and not self.passing(result) and encountered_success:
            metadata['first_failure_time'] = timestamp
        elif not self.passing(last_result) and self.passing(result) and last_result != '' and first_failure_time != 0:
            ttr = timestamp - first_failure_time

        metadata['last_result'] = result

        return ttr

    def passing(self, result):
        return result == self.passvalue

    @staticmethod
    def get_by_fields(by_fieldnames, event):
        return [event[x] for x in by_fieldnames]

dispatch(TtrCommand, sys.argv, sys.stdin, sys.stdout, __name__)
