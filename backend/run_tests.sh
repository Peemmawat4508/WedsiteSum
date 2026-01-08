#!/bin/bash
cd "$(dirname "$0")"
export PYTHONPATH=$PYTHONPATH:.
source venv/bin/activate
./venv/bin/pytest tests/ -v
