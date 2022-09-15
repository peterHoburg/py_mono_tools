#!/bin/sh

set -e

. $VIRTUALENV_PATH/bin/activate

exec "$@"
