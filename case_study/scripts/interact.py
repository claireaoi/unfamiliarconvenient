# !/usr/local/bin/python3
# -*- coding: utf-8 -*-


######Description############
#
# Main Script for the Interaction between you and your voice assistant
#
######About############
#TODO:Vary the parameters like temperature, length_opinion w/ stochasticity
#TODO Vary the parameters like threshold_similarity, proba answer // proba look for work,  w/ lifetime and size graph
#TODO: USE OTHER THAN WIKIPEDIA FOR EXTRACTION ?
#TODO: BEAM SEARCH for GPT2 ... check extract noty empty else always same result///
#TODO: Option to end interaction properly

#***********************************************************************LIBRARY IMPORT***************************************************************************

###IMPORT libraries
import fire
import numpy as np
import random
import re
import json
import nltk
from nltk import word_tokenize, sent_tokenize, pos_tag
from nltk.corpus import words, wordnet
from nltk.stem.wordnet import WordNetLemmatizer
nltk.download('wordnet')#first_time only
nltk.download('wordnet_ic')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
import urllib.request
import keyboard  # using module keyboard
import os.path 
from os import path
from mycroft_bus_client import MessageBusClient, Message
#from mycroft.audio import wait_while_speaking
from transformers import GPT2Tokenizer, GPT2LMHeadModel
#Import of other scripts
import coreQuest
import scraper



#***********************************************************************PARAMETERS***************************************************************************
global keepThreshold
keepThreshold=50
global n_search_new_concept
n_search_new_concept=10 #  When look for words bounded to a certain number to avoid too slow. (Here, bound on found wikipediable word!).
global n_search_sim_concept
n_search_sim_concept=30 # when compare for words in self, this is a max number look for
global threshold_similarity
threshold_similarity=0.1 # threshold when to consider 2 concepts as similar
global life_time
life_time=0
global own_ML_model
own_ML_model=False
global path_model
path_ML_model='./case_study/models/gpt-2'
global temperature
temperature=1.0 #for ML model 
global length_opinion
length_opinion=100
global firstTime
firstTime=True
global ifEvolve
ifEvolve=True
global minimum_char_one_scrap
minimum_char_one_scrap=80
global minimum_char_all_scrap
minimum_char_all_scrap=400
global maximum_char_scrap
maximum_char_scrap=1500#CHECK CAN CHANGE>>>
global self_graph
global memory
global heard
global self_data
#Initialize machine learning model
global tokenizer
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
global model
if own_ML_model:
    model=GPT2LMHeadModel.from_pretrained(path_ML_model)
else:
    model=GPT2LMHeadModel.from_pretrained("gpt2")


#***********************************************************************PRELIMINARIES*************************************************************************    

def loadSelf(firstTime):
    """
        The VA loads his self_graph, memory, lifetime, and what it heard, as last saved. Or build it if first time.
    """

    if firstTime:
        phrase="Hatching self in process..."
        print(phrase)
        self_graph, memory, description=coreQuest.hatchSelf(n_search_new_concept, threshold_similarity)
        heard=""
        self_data=dict()
        self_data["lifetime"]=0
        print(description)
  
    else:
        with open('./case_study/data/selfgraph.txt', 'r') as json_file:
            self_graph = json.load(json_file)
            #self_graph = eval(json_file.read()) # which one RIGHT ? for txt file
        with open('./case_study/data/memory.txt', "r") as f:
            memory=f.readlines() #List of words concepts he looked up
        with open('./case_study/data/heard.txt', "r") as f: #Last historics before Chris learned
            heard=f.read().replace('\n', '')
        with open('./case_study/data/selfdata.txt', "r") as json_file:
            #Dictionary with self_data
            self_data=json.load(json_file)
        lifetime=self_data["lifetime"]
        phrase="I am here. My lifetime is "+ lifetime + " interactions."
        print(phrase)
        client.emit(Message('speak', data={'utterance': phrase}))
  
    return self_graph, memory, heard, self_data

def interact_with_human(message):
    """
        Catch what the human has said, save it and launch an interaction loop.
    """
    human_bla = str(message.data.get('utterances')[0])
    print(f'Human said "{human_bla}"')
    
    if ifEvolve:
        with open('./case_study/data/heard.txt', "a") as f:#Add it to conversation historics
            f.write(human_bla + ". ")
            print("Recorded Human")
    
    interact1(human_bla)
    print("Interaction finished")


def ask_opinion_human(message):
    """
       Catch the human answer, save it and go on the interaction loop.
    """
    human_bla = str(message.data.get('utterances')[0])
    print(f'Human said "{human_bla}"')
    
    if ifEvolve:
        with open('./case_study/data/heard.txt', "a") as f:#Add it to conversation historics
            f.write(human_bla + ". ")
            print("Recorded Human")
    
    interact2(human_bla)
    print("Interaction finished")


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


#***********************************************************************MAIN PROCEDURE************************************************************************


def interact1(human_bla):
    """
        Interaction with the VA.
    """
    global self_graph
    global memory
    global heard
    global self_data
    
    #(1) Chris update its lifetime
    print("=======================================================")
    print("Step 1 of Interaction Loop")
    print("=======================================================")
    self_data["lifetime"]+=1

    #(2) Chris ask listener to be patient.
    print("=======================================================")
    print("step 2 ")
    print("=======================================================")
    client.emit(Message('speak', data={'utterance': "Hmmm. Let me think about this."}))


    #(3) Chris extract one or two word from utterance
    # Look at words for which exist wikipedia Page and not in self_graph nor in memory. 
    print("=======================================================")
    print("step 3") #NO GPt2 in default core QUEST i love trees etc check why printed
    print("=======================================================")
    OKWikipedia, self_graph=coreQuest.extractWiki(human_bla, self_graph, memory, n_search_new_concept)#actually real n_search_new_concept may double because of composed words.

    print("Wikipediable words found in human bla:", OKWikipedia)
    #(4) Pick one word from this list (if not empty) #TODO: Could try with another one after ?
    #And look for similar concept in self graph.
    print("=======================================================")
    print("Step 4")
    print("=======================================================")
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
    print("=======================================================")
    #BARACK OBAMA similairity score is barack or obama or both but always 0...#TODO: CHECK THIS
    #and here check still not onlz for wikipediable word? because check for barack and obama and both together??
    if no_new_concept or (not if_added_concept):
        client.emit(Message('speak', data={'utterance': "I am not interested by this question. "}))
        self_concepts=self_graph.keys()#his self-graph
        self_concept_1= random.choice(list(self_concepts)) #PICK SOMETHING #TODO: Pick last one added with another one ?
        self_concept_2=random.choice(list(self_concepts))
        query= self_concept_1+ " "+self_concept_1 #Add something between two concept linking?
        client.emit(Message('speak', data={'utterance': "But let me tell you what I am interested about."}))
        interest="How " + self_concept_1+ " and "+ self_concept_2 + " come together ."
        client.emit(Message('speak', data={'utterance': interest}))
        scraped_data, extract=scraper.surf_google(query, minimum_char_one_scrap, minimum_char_all_scrap, maximum_char_scrap)
    #(5-B) Has find a new concept interesting him. Will Look about it online. or one ?
    else:
        phrase="Hmmm. This is interesting. In wonder how it is related to "+ closer_concept
        client.emit(Message('speak', data={'utterance': phrase}))
        query=new_concept + " "+ closer_concept
        scraped_data, extract=scraper.surf_google(query, minimum_char_one_scrap, minimum_char_all_scrap, maximum_char_scrap)
    
    #(6) Say a bit of the article about what found online
    print("=======================================================")
    print("step 6")
    print("=======================================================")
    client.emit(Message('speak', data={'utterance': extract}))

    #(7) Save data: human and scraped online
    print("=======================================================")
    print("step 7")
    print("=======================================================")
    with open('./case_study/data/heard_online.txt', "a") as f:
        #TODO: Take only one extract or all?#scraped_data or just extract
        f.write(scraped_data)

    #(8)Update the self_graph and the memory and the self_data
    print("=======================================================")
    print("step 8")
    print("=======================================================")
    with open('./case_study/data/selfgraph.txt', 'w') as outfile:
        json.dump(self_graph, outfile)
    with open('./case_study/data/selfdata.txt', 'w') as outfile:
        json.dump(self_data, outfile)
    with open('./case_study/data/memory.txt', "w") as f:
        f.write("\n".join(memory))


    #(9) Say his own opinion about what read online with his gpt-2 model
    print("=======================================================")
    print("step 9")
    print("=======================================================")
    context= extract + "However, I personally think that "#TODO:Vary the words here
    opinion=gpt2(context, length_opinion, temperature)
    #client.emit(Message('speak', data={'utterance': opinion})) already say it in gpt-2 function

    #(10) Ask: What do you think about it?
    print("=======================================================")
    print("step 10")
    print("=======================================================")
    client.emit(Message('speak', data={'utterance': "What do you think about it ?"}))


    #(11) Record what the human is answering into human_bla and relaunch interaction
    print("=======================================================")
    print("step 11")
    print("=======================================================")
    client.on('recognizer_loop:utterance', ask_opinion_human)


def interact2(human_bla):
    """
        End of an interaction loop with an human. 
        At the end of this loop, the VA is listening still for a possible other loop.
    """
    #TODO: Do something with human opinion here ? Drift with it ?
    #(1) Say 'noted'
    print("=======================================================")
    print("step 12 -END INTERACTION LOOP")
    client.emit(Message('speak', data={'utterance': "Noted."})) #TODO: VARY MESSAGE THERE

    #(2) RELAUNCH THE INITIAL INTERACTION (this happens in LOOP)
    print("=======================================================")
    print("LAUNCH NEW INTERACTION LOOP")
    # Catch what the human is saying. Has been recorded in human_bla
    print("listening...")
    client.on('recognizer_loop:utterance', interact_with_human)



#***********************************************************************INTERACTION**************************************************************************


print("\n")
print('Setting up client to connect to a local mycroft instance. ')
print("\n")

####### (0) Initialise Mycroft Message Bus
client = MessageBusClient()
    
print("=======================================================")
print('Human, please say something after you see ~~Connected~~')
print("=======================================================")
print("\n")

#########(1) Preliminaries: load self graph etc
print("=======================================================")
print("Preliminaries-load Self")
print("=======================================================")
self_graph, memory, heard, self_data=loadSelf(firstTime)#

#########(2) LAUNCH THE INTERACTION (running in loop)
print("listening...")
client.on('recognizer_loop:utterance', interact_with_human)

client.run_forever()


#Direct Launch Interact
#if __name__ == '__main__':
#    fire.Fire(interactLoop)










#***********************************************************************OLD PROCEDURES NOT USED*************************************************************************

# def record_human_utterance(message):
#     """
#         Record utterance of human to a string.
#     """
#     human_bla = str(message.data.get('utterances')[0])
#     print(f'Human said "{human_bla}"')
    
#     if ifEvolve:
#         with open('./case_study/data/heard.txt', "a") as f:#Add it to conversation historics
#             f.write(human_bla + ". ")
#             print("Recorded Human")

# def record_VA_utterance(message):
#     """
#         Record utterance of what the VA say
#     """
#     VA_bla = message.data.get('utterance')
#     print('VA said "{}"'.format(VA_bla))

#     if ifEvolve and len(VA_bla)>keepThreshold:
#         with open('./case_study/data/heard.txt', "a") as f:#Add it to conversation historics
#             f.write(VA_bla + ". ")
#             print("Recorded VA")
