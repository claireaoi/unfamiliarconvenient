#!/bin/bash

#To activate Mycroft and environment
./start-mycroft.sh all
source .venv/bin/activate #enter the Mycroft virtual environment to use msm skills etc
export PYTHONIOENCODING=UTF-8

#To launch an interaction
python3 ./chris/src/selfQuest.py \
--nDrift=1 \
--lengthML=100 \
--nSimMax=50 \
--nSearch=100 \
--lengthWalk=10\
--walkNetwork=False \
--audibleSelfQuest=False \
--visualizeGraph=False
