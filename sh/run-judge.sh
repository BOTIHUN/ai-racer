#!/bin/bash
cd ${BASH_SOURCE%/*}
cd ../

PYTHON=./.venv/bin/python3

$PYTHON ./src/judge/run.py --replay_file replay config.json 1
