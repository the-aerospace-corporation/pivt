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
Manages configuration
"""

from pathlib import Path
import configparser
import logging


class ConfManager:
    """Configuration manager"""
    def __init__(self, conf_dir):
        if isinstance(conf_dir, str):
            conf_dir = Path(conf_dir)
        elif not isinstance(conf_dir, Path):
            raise Exception('conf_dir must be a str or Path object. instead got {0}'.format(type(conf_dir)))

        if conf_dir.exists() and not conf_dir.is_dir():
            raise Exception('{0} is not a directory!'.format(conf_dir))

        self.conf_dir = conf_dir
        self.default_dir = conf_dir / 'default'
        self.local_dir = conf_dir / 'local'

        self.logger = logging.getLogger(str(self.__class__.__name__))

        self.configs = {}

    def load(self):
        """Load configuration from files."""
        self.logger.info('Loading configurations')

        if not self.conf_dir.exists():
            raise Exception('Configuration directory {0} does not exist!'.format(self.conf_dir))

        default_conf_files = self.default_dir.glob('*')
        local_conf_files = self.local_dir.glob('*')

        conf_file_map = {}

        for file_path in default_conf_files:
            conf_file_map[file_path.stem] = [str(file_path)]

        for file_path in local_conf_files:
            if file_path.stem not in conf_file_map:
                conf_file_map[file_path.stem] = [str(file_path)]
            else:
                conf_file_map[file_path.stem].append(str(file_path))

        for filename, file_paths in conf_file_map.items():
            for file_path in file_paths:
                self.logger.info('Loading configuration from %s', file_path)

            config = configparser.ConfigParser()
            config.read(file_paths)

            self.configs[filename] = config

    def get(self, filename, stanza, setting):
        """
        Get a specific configuration value.
        :param filename: config file
        :param stanza: stanza the config setting is under
        :param setting: name of setting
        :return: config value
        """
        self.logger.info('Retrieving setting %s.%s.%s', filename, stanza, setting)

        if filename not in self.configs:
            raise Exception('No {0} config file! Config files: {1}'.format(filename, self.configs.keys()))

        config = self.configs[filename]

        if not config.has_section(stanza):
            raise Exception('No {0} stanza in config file {1}! Stanzas: {2}'
                            .format(stanza, filename, config.sections()))

        if not config.has_option(stanza, setting):
            raise Exception('No {0} setting in stanza {1} for config file {2}! Settings: {3}'
                            .format(setting, stanza, filename, config.options(stanza)))

        value = config.get(stanza, setting)

        self.logger.info('Value: %s', value)

        return value

    def set(self, filename, stanza, setting, value, create=False):
        """
        Set a configuration value and save it to a file.
        :param filename: config file
        :param stanza: stanza the config setting is under
        :param setting: name of setting
        :param value: value to save
        :param create: create the config file and stanza of either of them don't exist
        """
        self.logger.info('Setting %s.%s.%s to %s', filename, stanza, setting, value)

        if filename not in self.configs:
            if create:
                self.logger.info('Existing configuration not found. Creating.')
                self.configs[filename] = configparser.ConfigParser()
            else:
                raise Exception('No {0} config file! Config files: {1}'.format(filename, self.configs.keys()))

        config = self.configs[filename]

        if not config.has_section(stanza):
            if create:
                self.logger.info('Existing stanza not found in %s.conf. Creating', filename)
                config.add_section(stanza)
            else:
                raise Exception('No {0} stanza in config file {1}! Stanzas: {2}'
                                .format(stanza, filename, config.sections()))

        config.set(stanza, setting, str(value))

        self.local_dir.mkdir(parents=True, exist_ok=True)

        actual_file_path = self.local_dir / (filename + '.conf')

        local_config = configparser.ConfigParser()
        if actual_file_path.exists():
            self.logger.info('%s local config file exists. Loading.', filename)
            local_config.read(str(actual_file_path))

        if not local_config.has_section(stanza):
            local_config.add_section(stanza)
        elif local_config.has_option(stanza, setting):
            existing_value = local_config.get(stanza, setting)
            self.logger.info('Existing %s.%s.%s found; value: "%s". Overwriting with "%s".',
                             filename, stanza, setting, existing_value, value)

        local_config.set(stanza, setting, str(value))

        self.logger.info('Writing to local config file %s', str(actual_file_path))

        with actual_file_path.open('w') as file:
            local_config.write(file)

        self.logger.info('Done')

    def to_dict(self):
        """
        Convert configs to dict
        :return dict representing configs
        """
        conf_dict = {}
        for filename, config in self.configs.items():
            conf_dict[filename] = {section: dict(config[section]) for section in config.sections()}
        return conf_dict
