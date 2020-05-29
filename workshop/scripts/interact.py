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


#***********************************************************************INITIALIZATION***************************************************************************
keepThreshold=50

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

###IMPORT other scripts
import coreQuest

#***********************************************************************PRELIMINARIES*************************************************************************

def record_human_utterance(message):
    """
        Record utterance of human to a string.
    """
    humanBla = str(message.data.get('utterances')[0])
    print(f'Human said "{humanBla}"')

def record_VA_utterance(message):
    """
        Record utterance of what the VA say
    """
    print('Mycroft said "{}"'.format(VABla))
    VABla = str(message.data.get('utterances')[0]) 

#Mycroft init
print('Setting up client to connect to a local mycroft instance. ')
client = MessageBusClient()
print('Conversation may start.')
client.on('recognizer_loop:utterance', record_human_utterance)
wait_while_speaking() #wait for Mycroft to finish speaking. Useless now, but will be helpful later
client.run_forever()

#***********************************************************************MAIN INTERACTION*************************************************************************


def interactLoop(ifEvolve=True):
    """
        One interaction Loop with the VA.
    """
    #(0) Catch what the human is saying
    client.on('recognizer_loop:utterance', record_human_utterance)

    #(1) Catch what the VA is answering
    client.on('speak', record_VA_utterance) #recording the VA bla is given as a handler for speak message.

    #(2) ifEvolve, the VA records what has been said to later grow from it.
    if ifEvole:
        savedBla=humanBla
        if len(VABla)>keepThreshold:
            savedBla+=" /n"+ VABla #If above the threshold, add VABla o the savedBla too
        with open('./workshop/data/whatVAHeard.txt', "a") as f:#Add it to conversation historics
           f.write(savedBla)


def interact(ifEvolve=True):
    """
        Interaction with the VA, running until touch ´q´pressed.
    """
    loopCount=0
    #Interact until press key 'q' on keyboard:
    while not keyboard.is_pressed('q'):
        loopCount+=1
        print('Interaction n° "{}" begins.'.format(loopCount))
        interactLoop(ifEvolve)

    print('Human ended interaction.')



#***********************************************************************END*************************************************************************

#Direct Launch Interact
if __name__ == '__main__':
    fire.Fire(interact)
