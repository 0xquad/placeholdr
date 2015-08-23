#!/bin/bash
#
# Copyright (c) 2015, Alexandre Hamelin <alexandre.hamelin gmail.com>
#
# Initializes the project virtualenv by installing requirements.

set -e

[[ -e requirements.txt ]] || {
    echo 'not in the project directory? missing requirements.txt'
    exit 1
}

[[ -z "$VIRTUAL_ENV" ]] || {
    echo 'already in a virtualenv'
    exit 1
}

[[ -d bin ]] && [[ -d lib ]] && [[ -d include ]] && {
    echo 'virtualenv already initialized'
    exit 1
}

virtualenv -p python3 .
. bin/activate
pip install -r requirements.txt
# Fix for Python 3
sed -i 's/\.iteritems/.items/g' lib/*/site-packages/flaskext/genshi.py
