#!/bin/bash

#To activate Mycroft and environment
./start-mycroft.sh all
source .venv/bin/activate #enter the Mycroft virtual environment to use msm skills etc
export PYTHONIOENCODING=UTF-8

#To launch an interaction
python3 ./chris/src/interact.py \
--mood='neutral'\
--lengthML=200 \
--nMLDrift=1 \
--nSimMax=10 \
--nSearch=1 \
--ifEvolve=True \
--lengthWalk=10\
--walkNetwork=False \
--delayedSelfQuest=True \
--audibleSelfQuest=False \
--visualizeGraph=False
