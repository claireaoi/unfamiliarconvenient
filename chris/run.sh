#!/bin/bash

#Comment below for ...
#source ./myenv/bin/activate
export PYTHONIOENCODING=UTF-8


#For acidLoops
#python3 src/drift.py --question="Tell me about acid rain." --nLoop=2 --nDrift=2

#For test
#python3 src/test0.py

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
