#!/bin/bash

export PYTHONIOENCODING=UTF-8

#To activate Mycroft and environment
source ../../.venv/bin/activate #enter the Mycroft virtual environment to use msm skills etc
../../start-mycroft.sh all

#To launch an interaction
python3 selfQuest.py \
--firstTime=False \
--walkNetwork=False \
--audibleSelfQuest=False \
--visualizeGraph=True \
--nDrift=0 \
--lengthML=100 \
--nSimMax=50 \
--nSearch=100 \
--lengthWalk=10
