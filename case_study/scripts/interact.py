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
threshold_similarity=0.1 # threshold when to consider 2 concepts as similar
#TODO: Implement that this threshold vary through life
global life_time
life_time=0
global own_ML_model
own_ML_model=False
global path_model
path_ML_model='./case_study/models/gpt-2'
global temperature
temperature=1.0 #for ML model #TODO: Make it evolve
global length_opinion
length_opinion=100
global firstTime
firstTime=False
#***********************************************************************INITIALIZATION***************************************************************************


###IMPORT libraries
import fire
import numpy as np
import random
import re
import json

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
#from mycroft.audio import wait_while_speaking
from transformers import GPT2Tokenizer, GPT2LMHeadModel
###IMPORT other scripts
import coreQuest
import scraper

nltk.download('wordnet')
nltk.download('wordnet_ic')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

#Global variables
global tokenizer
global model
global self_graph
global memory
global heard

#Initialize machine learning model
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
if own_ML_model:
    model=GPT2LMHeadModel.from_pretrained(path_ML_model)
else:
    model=GPT2LMHeadModel.from_pretrained("gpt2")

print("\n")
print('Setting up client to connect to a local mycroft instance. ')
print("\n")

# Initialise Mycroft Message Bus
client = MessageBusClient()
    
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
        with open('./case_study/data/heard.txt', "a") as f:#Add it to conversation historics
            f.write(human_bla + ". ")
            print("Recorded Human")
    

def interact_with_human(message, ifEvolve=True):
    """
        Record utterance of human to a string.
    """
    human_bla = str(message.data.get('utterances')[0])
    print(f'Human said "{human_bla}"')
    
    if ifEvolve:
        with open('./case_study/data/heard.txt', "a") as f:#Add it to conversation historics
            f.write(human_bla + ". ")
            print("Recorded Human")
    
    interactLoop(human_bla)
    print("Interaction finished")


def record_VA_utterance(message, ifEvolve=True):
    """
        Record utterance of what the VA say
    """
    VA_bla = message.data.get('utterance')
    print('VA said "{}"'.format(VA_bla))

    if ifEvolve and len(VA_bla)>keepThreshold:
        with open('./case_study/data/heard.txt', "a") as f:#Add it to conversation historics
            f.write(VA_bla + ". ")
            print("Recorded VA")


def gpt2(context, length_output, temperature): 
    """
        One ML drift with gpt-2, with a context. Printed and said by VA.
    """
    process = tokenizer.encode(context, return_tensors = "pt")
    generator = model.generate(process, max_length = length_output, temperature = temperature, repetition_penalty = 2.0)
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
        self_graph, memory, description=coreQuest.hatchSelf(n_search_new_concept, threshold_similarity)
        heard=""
        print(description)
  
    else:
        with open('./case_study/data/selfgraph.txt', 'r') as json_file:
            self_graph = json.load(json_file)
            #self_graph = eval(json_file.read()) # which one RIGHT ? for txt file
        with open('./case_study/data/memory.txt', "r") as f:
            memory=f.readlines() #List of words concepts he looked up
        with open('./case_study/data/heard.txt', "r") as f: #Last historics before Chris learned
            heard=f.read().replace('\n', '')
        phrase="I am here. Self Quest can begin."
        print(phrase)
        if audible_selfquest:
            client.emit(Message('speak', data={'utterance': phrase}))
  
    return self_graph, memory, heard

#***********************************************************************MAIN INTERACTION*************************************************************************


def interactLoop(human_bla):
    """
        Interaction with the VA
    """
    global self_graph
    global memory
    global heard  

    #(2) Chris ask listener to be patient.
    print("=======================================================")
    print("step 1 of interaction Loop")
    client.emit(Message('speak', data={'utterance': "Hmmm. Let me think about this."}))

    #(3) Chris extract one or two word from utterance
    # Look at words for which exist wikipedia Page and not in self_graph nor in memory. 
    print("=======================================================")
    print("step 3") #NO GPt2 in default core QUEST i love trees etc check why printed
    OKWikipedia, self_graph=coreQuest.extractWiki(human_bla, self_graph, memory, n_search_new_concept)#actually real n_search_new_concept may double because of composed words.
    #TODO: Not only on wikipedia this extraction.
    print("Wikipediable words found in human bla:", OKWikipedia)
    #(4) Pick one word from this list (if not empty) #TODO: Could try with another one after ?
    #And look for similar concept in self graph.
    print("=======================================================")
    print("Step 4")
    no_new_concept=False
    if OKWikipedia==[]:
        no_new_concept=True #did not hear any new word
    elif not firstTime:
        new_concept=random.choice(OKWikipedia)
        self_graph, if_added_concept, closer_concept, similarity_score=coreQuest.isSelf(self_graph, new_concept, n_search_sim_concept,threshold_similarity)

    print("Added the concept", if_added_concept)
    #(5-A) Has not find a new concept interesting him. Will Look about two self concepts online. or one ?
    print("=======================================================")
    print("step 5")
    #BARACK OBAMA similairity score is barack or obama or both but always 0...
    #and here check still not onlz for wikipediable word? because check for barack and obama and both together??
    #put threshold at 0.1
    if no_new_concept or (not if_added_concept):
        client.emit(Message('speak', data={'utterance': "I am not interested by this question. "}))
        self_concepts=self_graph.keys()#his self-graph
        self_concept_1= random.choice(list(self_concepts)) #PICK SOMETHING #TODO: Pick last one added with another one ?
        self_concept_2=random.choice(list(self_concepts))
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
    print("=======================================================")
    print("step 6")
    client.emit(Message('speak', data={'utterance': extract}))

    #(7) Say his own opinion about it with his gpt-2 model
    print("=======================================================")
    print("step 7")
    #TODO: BEAM SEARCH for GPT2 ... check extract noty empty else always same result///
    context= extract + "However, I personally think that "#TODO:Vary the words here
    opinion=gpt2(context, length_opinion, temperature)#TODO:Vary the parameters like temperature, length_opinion
    #client.emit(Message('speak', data={'utterance': opinion})) alreadz saz it above 


    #(8) Ask: What do you think about it?
    print("=======================================================")
    print("step 8")
    client.emit(Message('speak', data={'utterance': "What do you think about it ?"}))

    #(9) Record what the human is answering into human_bla #TODO: should check this is not old human_bla
    print("=======================================================")
    print("step 9")
    client.on('recognizer_loop:utterance', record_human_utterance)
    #TODO: CALL FUNCTION HERE because else dont wait for...>>>


    #(10) Say 'noted'
    print("=======================================================")
    print("step 10")
    client.emit(Message('speak', data={'utterance': "Noted."}))

    #(11) Save data: human and scraped online. 
    print("=======================================================")
    print("step 11")
    with open('./case_study/data/heard_online.txt', "a") as f:
        f.write(scraped_data)

    #(12) Update the self_graph and the memory
    print("=======================================================")
    print("step 12")
    with open('./case_study/data/selfgraph.txt', 'w') as outfile:
        json.dump(self_graph, outfile)

    with open('./case_study/data/memory.txt', "w") as f:
        f.write("\n".join(memory))



#***********************************************************************END*************************************************************************

#(0) Preliminaries: load self graph etc
print("Preliminaries-load Self")
self_graph, memory, heard=loadSelf(firstTime)#, audible_selfquest, n_search_new_concept). CFHECK THESE ARGUMENTS


# Catch what the human is saying. Has been recorded in human_bla
print("listening...")
client.on('recognizer_loop:utterance', interact_with_human)

client.run_forever()

#Direct Launch Interact
#if __name__ == '__main__':
#    fire.Fire(interactLoop)
