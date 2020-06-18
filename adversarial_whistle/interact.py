# !/usr/local/bin/python3
# -*- coding: utf-8 -*-


######Description############
#
# Main Script for the Interaction between you and your voice assistant
#
######About############
# This script was created for the workshop Unfamiliar Virtual Convenient - Growing your Voice Assistant
# led by Vytautas Jankauskas and Claire Glanois through School of Machines, Make & believe, in spring 2020.
#
# Feel free to tune, or reshape it according to your project.


#***********************************************************************PARAMETERS***************************************************************************
keepThreshold=50
ifEvolve=True


#***********************************************************************INITIALIZATION***************************************************************************

###IMPORT libraries
import fire
import numpy as np
import random
import re
#Import for NLP
import nltk
from nltk.corpus import words, wordnet
from nltk.stem.wordnet import WordNetLemmatizer
import urllib.request
from nltk import word_tokenize, sent_tokenize, pos_tag
import keyboard  # using module keyboard
#Import for Mycroft
import os.path
from os import path
from mycroft_bus_client import MessageBusClient, Message
from mycroft.audio import wait_while_speaking

#Global variables
global humanBla
humanBla=""
global VABla
VABla=""
global savedBla
savedBla=""

# Initialise Mycroft Message Bus
client = MessageBusClient()

print("\n")
print('Setting up client to connect to a local mycroft instance. ')
print("\n")
print("=======================================================")
print('Human, please say something after you see ~~Connected~~')
print("=======================================================")
print("\n")

#***********************************************************************PRELIMINARIES*************************************************************************

def record_human_utterance(message, ifEvolve=ifEvolve):
    """
        Record utterance of human to a string.
    """
    humanBla = str(message.data.get('utterances')[0])
    print(f'Human said "{humanBla}"')

    if ifEvolve:
        with open('./workshop/data/whatVAHeard.txt', "a") as f:#Add it to conversation historics
            f.write(humanBla + ". ")
            print("Recorded Human")


def record_VA_utterance(message, ifEvolve=ifEvolve):
    """
        Record utterance of what the VA say
    """
    VABla = message.data.get('utterance')
    print('VA said "{}"'.format(VABla))

    if ifEvolve and len(VABla)>keepThreshold:
        with open('./workshop/data/whatVAHeard.txt', "a") as f:#Add it to conversation historics
            f.write(VABla + ". ")
            print("Recorded VA")

#***********************************************************************MAIN INTERACTION*************************************************************************


def interactLoop():
    """
        Interaction with the VA
    """

    #(0) Catch what the human is saying
    client.on('recognizer_loop:utterance', record_human_utterance)
    #(1) Catch what the VA is answering
    client.on('speak', record_VA_utterance) #recording the VA bla is given as a handler for speak message.
    # wait while Mycroft is speaking
    #wait_while_speaking()
    #(2) ifEvolve, the VA records what has been said to later grow from it.

    client.run_forever()


#***********************************************************************END*************************************************************************

#Direct Launch Interact
if __name__ == '__main__':
    fire.Fire(interactLoop)
