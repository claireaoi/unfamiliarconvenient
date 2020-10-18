# !/usr/local/bin/python3
# -*- coding: utf-8 -*-


######Description############
#
# Main Script for the Interaction between you and your voice assistant
#
######About############


#***********************************************************************PARAMETERS***************************************************************************
global keepThreshold
keepThreshold=50
global n_search_new_concept
n_search_new_concept=10 #  When look for words bounded to a certain number to avoid too slow. (Here, bound on found wikipediable word!).
global n_search_sim_concept
n_search_sim_concept=30 # when compare for words in self, this is a max number look for
audible_selfquest=False #TODO: Remove this parameter
global threshold_similarity
threshold_similarity=0.4 # threshold when to consider 2 concepts as similar
#TODO: Implement that this threshold vary through life
global life_time
life_time=0

own_ML_model=True
path_ML_model='./chris/models/gpt-2'
global temperature
temperature=1.0 #for ML model #TODO: Make it evolve
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

from transformers import GPT2Tokenizer, GPT2LMHeadModel


#Global variables
global human_bla
human_bla=""
global VA_bla
VA_bla=""
global savedBla
savedBla=""

###IMPORT other scripts
import coreQuest
import scraper

print("\n")
print('Setting up client to connect to a local mycroft instance. ')
print("\n")

# Initialise Mycroft Message Bus
client = MessageBusClient()

#client.run_in_thread()#NEED THIS ?

print("=======================================================")
print('Human, please say something after you see ~~Connected~~')
print("=======================================================")
print("\n")

#***********************************************************************PRELIMINARIES*************************************************************************

def record_human_utterance(message, ifEvolve=True):
    """
        Record utterance of human to a string.
    """
    human_bla = str(message.data.get('utterances')[0])
    print(f'Human said "{human_bla}"')

    if ifEvolve:
        with open('./chris/data/heard.txt', "a") as f:#Add it to conversation historics
            f.write(human_bla + ". ")
            print("Recorded Human")


def record_VA_utterance(message, ifEvolve=True):
    """
        Record utterance of what the VA say
    """
    VA_bla = message.data.get('utterance')
    print('VA said "{}"'.format(VA_bla))

    if ifEvolve and len(VA_bla)>keepThreshold:
        with open('./chris/data/heard.txt', "a") as f:#Add it to conversation historics
            f.write(VA_bla + ". ")
            print("Recorded VA")


def gpt2(context, length_output, temperature): 
    """
        One ML drift with gpt-2, with a context. Printed and said by VA.
    """
    process = tokenizer.encode(context, return_tensors = "pt")
    generator = model.generate(process, max_length = length_output, temperature = temperature, repetition_penalty = 2)
    drift = tokenizer.decode(generator.tolist()[0])
    client.emit(Message('speak', data={'utterance': drift})) #does it say this or just will answer?
    print(drift)
    return drift

def loadSelf(firstTime):
    """
        The VA loads his self_graph and memory as last saved. Or build it if first time.
    """
    if firstTime:
        blabla=[]
        phrase="Hatching self in process..."
        print(phrase)
        self_graph, memory, description=coreQuest.hatchSelf(n_search_new_concept)
        print(description)
        #if audible_selfquest:
        #    client.emit(Message('speak', data={'utterance': phrase}))
        #if audible_selfquest:
        #    client.emit(Message('speak', data={'utterance': description}))

    else:
        with open('./chris/data/selfgraph.txt', 'r') as json_file:
            #self_graph = json.load(json_file)
            self_graph = eval(json_file.read()) # which one RIGHT ?
        with open('./chris/data/memory.txt', "r") as f:
            memory=f.readlines() #List of words concepts he looked up
        with open('./chris/data/heard.txt', "r") as f: #Last historics before Chris learned
            heard=f.read().replace('\n', '')
        phrase="I am here. Self Quest can begin."
        print(phrase)
        if audible_selfquest:
            client.emit(Message('speak', data={'utterance': phrase}))
  
    return self_graph, memory, heard

#***********************************************************************MAIN INTERACTION*************************************************************************


def interactLoop(length_opinion):
    """
        Interaction with the VA
    """
    #TODO: Check if first implementation

    #(0) Preliminaries: load self graph etc
    self_graph, memory, heard=loadSelf(firstTime, audible_selfquest, n_search_new_concept)
    #Initialize machine learning model
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    if own_ML_model:
        model=GPT2LMHeadModel.from_pretrained(path_ML_model)
    else:
        model=GPT2LMHeadModel.from_pretrained("gpt2")

    #(1) Catch what the human is saying. Has been recorded in human_bla
    client.on('recognizer_loop:utterance', record_human_utterance)
    
    #(2) Chris ask listener to be patient.
    client.emit(Message('speak', data={'utterance': "Hmmm. Let me think about this."}))

    #(3) Chris extract one or two word from utterance
    # Look at words for which exist wikipedia Page and not in self_graph nor in memory. 
    OKWikipedia, self_graph=coreQuest.extractWiki(heard, self_graph, memory, n_search_new_concept)#actually real n_search_new_concept may double because of composed words.
    #TODO: Not only on wikipedia this extraction.

    #(4) Pick one word from this list (if not empty) #TODO: Could try with another one after ?
    #And look for similar concept in self graph.
    no_new_concept=False
    if OKWikipedia==[]:
        no_new_concept=True #did not hear any new word
    elif not firstTime:
        new_concept=random.choice(OKWikipedia)
        self_graph, if_added_concept, closer_concept, similarity_score=coreQuest.isSelf(self_graph, new_concept, n_search_sim_concept)

    #(5-A) Has not find a new concept interesting him. Will Look about two self concepts online. or one ?
    if no_new_concept or not if_added_concept:
        client.emit(Message('speak', data={'utterance': "I am not interested by this question. "}))
        self_concepts=self_graph.keys()#his self-graph
        self_concept_1= random.choice(self_concepts) #PICK SOMETHING #TODO: Pick last one added with another one ?
        self_concept_2=random.choice(self_concepts)
        query= self_concept_1+ " "+self_concept_1 #Add something between two concept linking?
        client.emit(Message('speak', data={'utterance': "But let me tell you what I am interested about."}))
        interest="How " + self_concept_1+ " and "+ self_concept_2 + " come together ."
        client.emit(Message('speak', data={'utterance': interest}))
        scraped_data, extract=scraper.surf(query)
    #(5-B) Has find a new concept interesting him. Will Look about it online. or one ?
    else:
        phrase="Hmmm. This is interesting. In wonder how it is related to "+ closer_concept
        client.emit(Message('speak', data={'utterance': phrase}))
        query=new_concept + " "+ closer_concept
        scraped_data, extract=scraper.surf(query)
    
    #(6) Say a bit of the article about what found online
    client.emit(Message('speak', data={'utterance': extract}))

    #(7) Say his own opinion about it with his gpt-2 model
    context= extract + "However, I personally think that "#TODO:Vary the words here
    opinion=gpt2(context, length_opinion, temperature)#TODO:Vary the parameters like temperature, length_opinion
    client.emit(Message('speak', data={'utterance': opinion}))


    #(8) Ask: What do you think about it?
    client.emit(Message('speak', data={'utterance': "What do you think about it ?"}))

    #(9) Record what the human is answering into human_bla #TODO: should check this is not old human_bla
    client.on('recognizer_loop:utterance', record_human_utterance)


    #(10) Say 'noted'
    client.emit(Message('speak', data={'utterance': "Noted."}))

    #(11) Save data: human and scraped online. 
    with open('./chris/data/heard_human.txt', "a") as f:
        f.write(human_bla)
    with open('./chris/data/heard_online.txt', "a") as f:
        f.write(scraped_data)

    #(12) Update the self_graph and the memory
    with open('./chris/data/selfgraph.txt', 'w') as outfile:
        json.dump(self_graph, outfile)

    with open('./chris/data/memory.txt', "w") as f:
        f.write("\n".join(memory))

    #Catch what the VA is answering
    #client.on('speak', record_VA_utterance) #recording the VA bla is given as a handler for speak message.
    # wait while Mycroft is speaking
    #wait_while_speaking()
    #client.run_forever()


#***********************************************************************END*************************************************************************

#Direct Launch Interact
if __name__ == '__main__':
    fire.Fire(interactLoop)
