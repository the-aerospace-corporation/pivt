#!/bin/bash

script_dir="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
script_dir=${script_dir/\/cygdrive\/c\//C:\/}
script_dir=${script_dir/\/c\//C:\/}

owner=$(stat -c \"%u:%g\" $script_dir)

docker run -v $script_dir:/viz node:6.11.0 bash -c "cd /viz && npm run build && chown $owner visualization.js"
