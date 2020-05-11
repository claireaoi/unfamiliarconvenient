#!/bin/bash

#Comment below for ...
#source ./myenv/bin/activate


./start-mycroft.sh all
export PYTHONIOENCODING=UTF-8


#For interact
python3 chris/src/interact.py \
--mood='neutral'\
--question="Christopher, tell me about acid rain." \
--lengthML=200 \
--nMLDrift=1 \
--nSimMax=10 \
--nSearch=1 \
--ifEvolve=True \
--lengthWalk=10\
--walkNetwork=False \
--delayedSelfQuest=True \
--audibleSelfQuest=False

#For acidLoops
#python3 src/drift.py --question="Tell me about acid rain." --nLoop=2 --nDrift=2

#For test
#python3 src/test0.py
