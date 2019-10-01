#!/bin/bash

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
script_dir=${script_dir/\/cygdrive\/c\//C:\/}
script_dir=${script_dir/\/c\//C:\/}

dow=$(date +%a)
proxy_url=http://30525:$dow@proxy-west.aero.org:8080

owner=$(stat -c \"%u:%g\" $script_dir)

docker run -e http_proxy=$proxy_url -e https_proxy=$proxy_url -v $script_dir:/viz node:6.11.0 bash -c "cd /viz && npm config set user root && npm install && chown -R $owner node_modules"
