#!/bin/bash

#To activate Mycroft and environment
./start-mycroft.sh all
source .venv/bin/activate #enter the Mycroft virtual environment to use msm skills etc
export PYTHONIOENCODING=UTF-8

#To launch an interaction
python3 ./chris/scripts/selfQuest.py \
--firstTime=False \
--nDrift=0 \
--lengthML=100 \
--n_search_sim_concept=50 \
--n_search_new_concept=100 \
--lengthWalk=10 \
--walkNetwork=False \
--audible_selfquest=False \
--visualizeGraph=True
