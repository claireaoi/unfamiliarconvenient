#!/bin/bash

export PYTHONIOENCODING=UTF-8
#To activate Mycroft and environment
source ../../.venv/bin/activate #enter the Mycroft virtual environment to use msm skills etc
../../start-mycroft.sh all


#To launch an interaction
python3 interact.py \
--mood='neutral'\
--lengthML=200 \
--nMLDrift=1 \
--ifEvolve=True \
--randomizeMood=True \
--visualizeGraph=False
