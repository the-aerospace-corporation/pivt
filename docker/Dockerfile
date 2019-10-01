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

FROM splunk/splunk:7.0.3

ENV TZ=America/Los_Angeles
USER root

ENV PYTHON_VERSION 3.5.6

RUN DOW=$(date +%a) \
    && export http_proxy=http://30525:$DOW@proxy-west.aero.org:8080 \
    && export https_proxy=http://30525:$DOW@proxy-west.aero.org:8080 \
    && apt-get update && apt-get -y upgrade \
    && apt-get install -y build-essential wget zlib1g-dev libssl-dev \
    && wget https://www.python.org/ftp/python/$PYTHON_VERSION/Python-$PYTHON_VERSION.tgz \
    && tar xf Python-$PYTHON_VERSION.tgz \
    && cd Python-$PYTHON_VERSION \
    && ./configure && make && make install \
    && pip3 install requests \
    && cd .. && rm -rf Python* \
    && apt install -y npm

COPY entrypoint.sh /sbin

WORKDIR /opt/splunk/etc
COPY splunk_etc .

WORKDIR /app/pivt
