#!/bin/bash
cd ${BASH_SOURCE%/*}
cd ../

PYTHON=./.venv/bin/python3

$PYTHON src/visualisation.py ./replay