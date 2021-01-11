# !/usr/local/bin/python3
# -*- coding: utf-8 -*-


######Description############
#
# Main Script for the Interaction between you and your voice assistant
#
######About############
#TODO: Vary the parameters like temperature, length_opinion w/ stochasticity
#TODO Vary the parameters like threshold_similarity, proba answer // proba look for work,  w/ lifetime and size graph
#TODO: Vary all mycroft all "message" and "concept"
#TODO: Recent Memory check and update it ? and erase it ? words that the VA has looked
#TODO: Check When Human say nothing


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
import time

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
firstTime=False
global ifEvolve
ifEvolve=True
global minimum_char_one_scrap
minimum_char_one_scrap=80
global minimum_char_all_scrap
minimum_char_all_scrap=400
global maximum_char_scrap
maximum_char_scrap=800#CHECK CAN CHANGE>>>
global self_graph
global memory
global self_data
global begin_interaction_loop
begin_interaction_loop=True
global ask_human_opinion
ask_human_opinion=False
global concept_1
concept_1=""
global concept_2
concept_2=""
global concept_3
concept_3=""
global extract_1
extract_1=""
global human_opinion
human_opinion=""

#Initialize machine learning model
global tokenizer
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
global model
if own_ML_model:
    model=GPT2LMHeadModel.from_pretrained(path_ML_model)
else:
    model=GPT2LMHeadModel.from_pretrained("gpt2")



#***********************************************************************PRELIMINARIES*************************************************************************    

def merge(text1, text2):
    """
    #TODO: Take half of the texts if too long ?
    """
    return text1+ " " + text2

def loadSelf(firstTime):
    """
        The VA loads his self_graph, memory, lifetime, as last saved. Or build it if first time.
    """

    if firstTime:
        phrase="Hatching self in process..."
        print(phrase)
        self_graph, memory, description=coreQuest.hatchSelf(n_search_new_concept, threshold_similarity)
        self_data=dict()
        self_data["lifetime"]=0
        print(description)
  
    else:
        with open('./case_study/data/selfgraph.txt', 'r') as json_file:
            self_graph = json.load(json_file)
            #self_graph = eval(json_file.read()) # which one RIGHT ? for txt file
        with open('./case_study/data/memory.txt', "r") as f:
            memory=f.readlines() #List of words concepts he looked up
        with open('./case_study/data/selfdata.txt', "r") as json_file:
            #Dictionary with self_data
            self_data=json.load(json_file)
        lifetime=self_data["lifetime"]
        phrase="I am here. My lifetime is "+ str(lifetime) + " interactions."
        print(phrase)
        #client.emit(Message('speak', data={'utterance': phrase}))#cannot put before run forever ?
  
    return self_graph, memory, self_data


def interact_with_human_global(message):
    """
        The VA reacts to what a human say:
        _either its the beginning of the interaction
        _or its 
    """

    global begin_interaction_loop
    global ask_human_opinion
    global human_opinion

    if begin_interaction_loop and ((human_opinion is None) or (human_opinion=="")):#before with ask_human_opinion...
        begin_interaction_loop=False
        human_bla = str(message.data.get('utterances')[0])
        print(f'Human said "{human_bla}"')

        if ifEvolve:
            with open('./case_study/data/heard_human.txt', "a") as f:#Add it to conversation historics
                f.write(human_bla + ". ")
                print("Saved Human bla")
        #LAUNCH INTERACT1
        interact1(human_bla)

    elif (not begin_interaction_loop) and (not human_opinion is None) and (human_opinion==""):
        #Then means human opinion has been expressed
        #ask_human_opinion=False
        human_opinion=""#Reset opinion
        print("=======================================================")
        print("Caught human opinion")
        human_bla = str(message.data.get('utterances')[0])
        print(f'Human said "{human_bla}"')
        client.emit(Message('speak', data={'utterance': "Noted."}))

        if ifEvolve:
            with open('./case_study/data/heard_human.txt', "a") as f:#Add it to conversation historics
                f.write(human_bla + ". ")
                print("Saved Human opinion")
        #LAUNCH INTERACT2
        interact2(human_bla)

    #if keyboard.is_pressed('q'):#TODO: OK as such ? Save more files ? ACTIVATE WHEN CHRIS IUS AUDIO !
    #    print("Ending our Interaction...")
    #    sys.exit()


def gpt2(context, length_output, temperature): 
    """
        One ML drift with gpt-2, with a context. Printed and said by VA.
    """
    process = tokenizer.encode(context, return_tensors = "pt")
    #generator = model.generate(process, max_length = length_output, temperature = temperature, repetition_penalty = 2.0)
    generator = model.generate(process, max_length = lengthDrift, temperature = temperature, repetition_penalty = 2.0, do_sample=True, top_k=50)


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
    global self_data
    global concept_1
    global concept_2
    global extract_1
    global human_opinion
    
    #(1) Chris update its lifetime, save it and ask the listener to be patient.
    print("=======================================================")
    print("Step 1--Preliminaries")
    print("=======================================================")
    client.emit(Message('speak', data={'utterance': "Hmmm. Let me think about this."}))
    
    self_data["lifetime"]+=1
    with open('./case_study/data/selfdata.txt', 'w') as outfile:
        json.dump(self_data, outfile)

    #(2) Chris extract one or two word from utterance
    # Look at words for which exist wikipedia Page and not in self_graph nor in memory. 
    print("=======================================================")
    print("step 2- Extract words from humam Bla") #NO GPt2 in default core QUEST i love trees etc check why printed
    print("=======================================================")
    OKWikipedia, self_graph=coreQuest.extractWiki(human_bla, self_graph, memory, n_search_new_concept)#actually real n_search_new_concept may double because of composed words.

    print("Words extracted from human blabla:", OKWikipedia)
    
    #(3) Pick one word from this list (if not empty)
    #And look for similar concept in self graph.
    print("=======================================================")
    print("Step 3--Look for a similar self-concept")
    print("=======================================================")
    no_new_concept=False
    if OKWikipedia==[]:
        no_new_concept=True #did not hear any new word
        print("Did not hear any new word interesting in human blabla.")
    else:
        new_concept=random.choice(OKWikipedia)
        print("Picked a new concept:", new_concept)
        self_graph, if_added_concept, closer_concept=coreQuest.isSelf(self_graph, new_concept, n_search_sim_concept,threshold_similarity)
        print("If added the concept to self-graph:", if_added_concept)
        print("Closer concept in self-graph:", closer_concept)
        #Update memory with this concept
        memory.append(new_concept)
        with open('./case_study/data/memory.txt', "a") as f:
            f.write("\n".join(memory))
        #if added concept, update self graph:
        if if_added_concept:
            with open('./case_study/data/selfgraph.txt', 'w') as outfile:
                json.dump(self_graph, outfile)
        concept_1=new_concept
        concept_2=closer_concept


    #(4A) ONLINE SURF AND SCRAP 
    print("=======================================================")
    print("step 4--Surf online space and Scrap")
    print("=======================================================")
    #BARACK OBAMA similairity score is barack or obama or both but always 0...#TODO: CHECK THIS
    #and here check still not onlz for wikipediable word? because check for barack and obama and both together??

    #CASE A. Has not find a new concept interesting him. Will Look about two self concepts online. or one ?
    if no_new_concept or (not if_added_concept):
        client.emit(Message('speak', data={'utterance': "I am not interested by this question. "}))
        client.emit(Message('speak', data={'utterance': "But let me tell you what I am interested about."}))
        self_concepts=self_graph.keys()#his self-graph
        concept_1= random.choice(list(self_concepts)) #PICK SOMETHING #TODO: or Pick last one added with another one ?
        concept_2=concept_1
        while concept_1==concept_2:#so not same
            concept_2=random.choice(list(self_concepts))
    #CASE B. Has picked some interesting cocnept, and try find the link...
    else:
        phrase="Hmmm. This is interesting."
        client.emit(Message('speak', data={'utterance': phrase}))
    #Form Query and Scrap online space
    query= concept_1+ " "+ concept_2
    interest="I wonder how " + self_concept_1+ " and "+ self_concept_2 + " come together ."
    client.emit(Message('speak', data={'utterance': interest}))
    print(interest)
    print("Now surfing the online space...")
    scraped_data, extract_1=scraper.surf_google(query, minimum_char_one_scrap, minimum_char_all_scrap, maximum_char_scrap)
    
    #SAVE DATA THAT WAS SCRAPED
    print("Save data...")
    with open('./case_study/data/heard_online.txt', "a") as f:
        for text in scraped_data:
            f.write(text)

    #(5) Say a bit of the article about what found online
    print("=======================================================")
    print("step 5---Share what found")
    print("=======================================================")
    client.emit(Message('speak', data={'utterance': "Let me share what I found while surfing the online space."}))#Change these sentence
    client.emit(Message('speak', data={'utterance': extract_1}))

    #(6) Ask: What do you think about it?
    print("=======================================================")
    print("step 6----Ask for human opinion")
    print("=======================================================")
    message="What do you think about it ?"
    print("Waiting for human opinion...")
    human_opinion=client.wait_for_response(Message('speak', data={'utterance': message}), reply_type=None, timeout=10)
     #TODO: CHECK THIS so to wait for human to answer during 10 seconds...ELSE USE LINE BELOW
    #global ask_human_opinion
    #ask_human_opinion=True
    #client.emit(Message('speak', data={'utterance': message}))
    #time.sleep(3)
   
    #Cf for following interaction the interact_with_human
    #message_out=client.wait_for_response(message, reply_type=None, timeout=10)
    #catched_opinion(message_out)
    #client.on('recognizer_loop:utterance', ask_opinion_human)



def interact2(human_bla):
    """
        End of an interaction loop with an human. 
        At the end of this loop, the VA is listening still for a possible other loop.
    """
    global self_graph   
    global memory
    global self_data
    global concept_3
    
    print("=======================================================")
    print("step 7----Extract new concept from human opinion")
    print("=======================================================")
    #(7) Pick a new concept from human opinion:
    OKWikipedia, self_graph=coreQuest.extractWiki(human_bla, self_graph, memory, n_search_new_concept)
    print("Words extracted from human opinion:", OKWikipedia)
   
    found_new_concept=False
     #CASE A where empty: AS SUCH STILL WOULD GIVE HIS OPINION 
    if OKWikipedia==[]:
        print("Did not find anything interesting in this opinion.".)
        message="Hmmm. Noted. But I dont see how this is interesting."
        client.emit(Message('speak', data={'utterance': message}))

    #CASE B where found new concept
    else:
        found_new_concept=True
        concept_3=random.choice(OKWikipedia)
        print("Picked a new concept:", concept_3)
        message="Hmmm. Interesting. I wonder how {} is related to {} and {}".format(concept_3, concept_1, concept_2)
        client.emit(Message('speak', data={'utterance': message}))

        #Update memory with this concept
        memory.append(concept_3)#TODO INSTEAD rewrite all simply add...
        with open('./case_study/data/memory.txt', "w") as f:
            f.write("\n".join(memory))

        print("=======================================================")
        print("step 8----New Surf & Scrap.")
        print("=======================================================")
        #(8) New surf& scrap with these 3 concepts. and Save
        new_query= concept_3 + " "+ concept_1+ " "+ concept_2
        print("Now surfing the online space...")
        scraped_data_2, extract_2=scraper.surf_google(new_query, minimum_char_one_scrap, minimum_char_all_scrap, maximum_char_scrap)

        #SAVE DATA THAT WAS SCRAPED
        print("Save scraped data...")
        with open('./case_study/data/heard_online.txt', "a") as f:
            for text in scraped_data_2:
                f.write(text)

        print("=======================================================")
        print("step 9----Share what found online ")
        print("=======================================================")
        #(5) Say a bit of the article about what found online
        client.emit(Message('speak', data={'utterance': "Let me share what I just found."})) #Vary these sentences
        client.emit(Message('speak', data={'utterance': extract_2}))

    print("=======================================================")
    print("step 10----Give his own opinion")
    print("=======================================================")
    #(10) Give his own opintion: generate it with gpt-2
    if found_new_concept:
        seed=merge(extract_1, extract_2)##Take 1/3 of scrap 1 and 1/3 of scrap2 for seeding gpt2 or half ?
    else:
        seed=extract_1
    context= seed +"\n"+"I personally think that "
    opinion=gpt2(context, length_opinion, temperature) #TODO: REMOVE context from output...?
    print("Opinion VA:", opinion)
    
    print("=======================================================")
    print("END INTERACTION LOOP")
    print("=======================================================")

    time.sleep(3)

    #>>>RELAUNCH THE INITIAL INTERACTION (this happens in LOOP)
    print("=======================================================")
    print("LAUNCH NEW INTERACTION LOOP")
    print("=======================================================")
    print("listening...")
    global begin_interaction_loop
    begin_interaction_loop=True
    #client.on('recognizer_loop:utterance', interact_with_human)#not if forever




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

self_graph, memory, self_data=loadSelf(firstTime)#

#########(2) LAUNCH THE INTERACTION (running in loop)
print("listening...")
#client.run_in_thread() #here require loop again


client.on('recognizer_loop:utterance', interact_with_human_global) 

""" while True:
    if begin_interaction_loop and not ask_human_opinion:#double security. needed ?
        client.on('recognizer_loop:utterance', interact_with_human) """
    #elif ask_human_opinion and not begin_interaction_loop:
        #client.on('recognizer_loop:utterance', ask_human_opinion)
        
client.run_forever()#beware here keep cathing stuff ever and ever


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



# def ask_opinion_human(message):
#     """
#        Catch the human answer, save it and go on the interaction loop.
#     """
#     print("STEP 12=======================================================")
#     print("CATCHED HUMAN OPINION")
#     human_bla = str(message.data.get('utterances')[0])
#     print(f'Human said "{human_bla}"')
    
#     if ifEvolve:
#         with open('./case_study/data/heard.txt', "a") as f:#Add it to conversation historics
#             f.write(human_bla + ". ")
#             print("Saved Human opinion")
#     global ask_human_opinion
#     ask_human_opinion=False
    
#     interact2(human_bla)


# def catched_opinion(message):
#     """
#        Catch the human answer, save it and go on the interaction loop.
#     """
#     print("STEP 12=======================================================")
#     global ask_human_opinion
#     if message is None:
#         print("DID NOT CATCHED ANY HUMAN OPINION")
#         ask_human_opinion=False
#         interact2("")
#     else:
#         print("CATCHED HUMAN OPINION")
#         human_bla = str(message.data.get('utterances')[0])
#         print(f'Human said "{human_bla}"')
        
#         if ifEvolve:
#             with open('./case_study/data/heard.txt', "a") as f:#Add it to conversation historics
#                 f.write(human_bla + ". ")
#                 print("Saved Human opinion")
#         ask_human_opinion=False
#         interact2(human_bla)


# def interact_with_human(message):
#     """
#         Catch what the human has said, save it and launch an interaction loop.
#     """
#     global begin_interaction_loop
#     human_bla = str(message.data.get('utterances')[0])
#     print(f'Human said "{human_bla}"')

#     if ifEvolve:
#         with open('./case_study/data/heard.txt', "a") as f:#Add it to conversation historics
#             f.write(human_bla + ". ")
#             print("Saved Human bla")

#     begin_interaction_loop=False
    
#     interact1(human_bla)
