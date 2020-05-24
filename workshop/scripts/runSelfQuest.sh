#!/bin/bash

export PYTHONIOENCODING=UTF-8

#To activate Mycroft and environment
source ./.venv/bin/activate #enter the Mycroft virtual environment to use msm skills etc
./start-mycroft.sh all


#To launch an interaction
python3 ./workshop/scripts/selfQuest.py \
--firstTime=False \
--walkNetwork=False \
--audibleSelfQuest=False \
--visualizeGraph=True \
--ifMLDrift=False \
--lengthML=100 \
--nSimMax=50 \
--nSearch=100 \
--lengthWalk=10 \
--finetuned_ML_model= False \
--path_finetuned_ML_model='./workshop/models/gpt-2'
