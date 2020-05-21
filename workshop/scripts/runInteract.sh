#!/bin/bash

#To activate Mycroft and environment
./start-mycroft.sh all
source .venv/bin/activate #enter the Mycroft virtual environment to use msm skills etc
export PYTHONIOENCODING=UTF-8

#To launch an interaction
python3 ./chris/scripts/interact.py \
--mood='neutral'\
--lengthML=200 \
--nMLDrift=1 \
--ifEvolve=True \
--randomizeMood=True \
--visualizeGraph=False
