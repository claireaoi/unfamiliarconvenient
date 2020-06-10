#!/bin/bash

export PYTHONIOENCODING=UTF-8

# start mycroft
./start-mycroft.sh all

#To launch an interaction
python3 ./workshop/scripts/interact.py --ifEvolve=True \
