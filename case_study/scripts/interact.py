# !/usr/local/bin/python3
# -*- coding: utf-8 -*-


######Description############
# Main Script for the Interaction between you and your voice assistant

######About############
#***********************************************************************LIBRARY IMPORT***************************************************************************

###IMPORT libraries
import fire
import numpy as np
import random
import re
import json
import time
import urllib.request
import keyboard  # using module keyboard
import os.path 
from os import path
from mycroft_bus_client import MessageBusClient, Message
from mycroft.audio import wait_while_speaking
from transformers import GPT2Tokenizer, GPT2LMHeadModel
#Import of other scripts
import coreQuest
import scraper
from utils import crop_unfinished_sentence, loadSelf

#***********************************************************************PARAMETERS***************************************************************************

#####PARAMETERS WHICH EVOLVE#############
#TODO: EVOLVE both With size graph: nSelf=len(list(self_graph.keys()))
global threshold_similarity
threshold_similarity=0.1 # threshold when to consider 2 concepts as similar
global n_sim_concept
n_sim_concept=30 # when compare for words in self, this is a max number look for, else slow down too much
global FIRST_RUN
FIRST_RUN=False
######OTHER PARAMETERS TO BE TUNED##############
global TEMPERATURE
TEMPERATURE=1.0 #for ML model 
global TEMPERATURE_VARIANCE
TEMPERATURE_VARIANCE=0.3 #for ML model
global MIN_CHAR_SAVE
MIN_CHAR_SAVE=40
global SEED_LENGTH#BEWARE IN OPINION LENGTH TAKEN INTO ACCOUNT!
SEED_LENGTH=80#WOULD BE DOUBLED...
global OPINION_LENGTH
OPINION_LENGTH=500
global OPINION_LENGTH_VARIANCE
OPINION_LENGTH_VARIANCE=40
global MIN_CHAR_BIT
MIN_CHAR_BIT=80
global MIN_CHAR_BLOCK
MIN_CHAR_BLOCK=200
global BOUND_CHAR_EXTRACT
BOUND_CHAR_EXTRACT=400 
global BOUND_CHAR_EXTRACT_VARIANCE
BOUND_CHAR_EXTRACT_VARIANCE=100
global OPINION_TIMEOUT
OPINION_TIMEOUT=10
#################################FIXED PARAMETERS##############
global MAX_PICK_WORD
MAX_PICK_WORD=20 # When look for words bounded to a certain number to avoid too slow.
# Amounts to bound on found wikipediable word! When search from opinion, may be bigger.
global OWN_ML_MODEL
OWN_ML_MODEL=False
global path_ML_model
path_ML_model='./case_study/models/gpt-2'
global SAVE_BLA
SAVE_BLA=True
global self_graph
global memory
global self_data
global begin_interaction_loop
begin_interaction_loop=True
global concept_1
concept_1=""
global concept_2
concept_2=""
global concept_3
concept_3=""
global extract_1
extract_1=""
global wait_for_opinion
wait_for_opinion=False
global timeout_start
timeout_start=0


#***********************************************************************PRELIMINARIES*************************************************************************    


def gpt2_text_generation(context, length_output, TEMPERATURE): 
    """
        One ML drift with gpt-2, with a context. Printed and said by VA.
        With some stochasticity
    """
    process = tokenizer.encode(context, return_tensors = "pt")
    #generator = model.generate(process, max_length = length_output, TEMPERATURE = TEMPERATURE, repetition_penalty = 2.0)
    generator = model.generate(process, max_length = length_output, TEMPERATURE = TEMPERATURE, repetition_penalty = 2.0, do_sample=True, top_k=20)
    drift = tokenizer.decode(generator.tolist()[0])
    client.emit(Message('speak', data={'utterance': drift})) #does it say this or just will answer?
    return drift



def interact_with_human_global(message):
    """
        The VA reacts to what a human say:
        _either its the beginning of the interaction
        _or its opinion
    """

    global begin_interaction_loop
    global wait_for_opinion
    global timeout_start
    global OPINION_TIMEOUT
    timeout_end = time.time()
    timeout=timeout_end-timeout_start
    print("time out", timeout)
    #TIME OUT OPINION
    if timeout>OPINION_TIMEOUT and wait_for_opinion:
        wait_for_opinion=False
        begin_interaction_loop=True
        #TODO: one bool should be enough
            # #If no human opinion, start a new interaction
        print("Timeout. Human had no opinion ...:(")
     #print("=======================================================")
    #     print("END INTERACTION LOOP")
    #     print("=======================================================")
        print("=======================================================")
        print("LAUNCH NEW INTERACTION LOOP")
        print("=======================================================")
        #print("listening...")
        #PRINT sth ?
    #   #client.on('recognizer_loop:utterance', interact_with_human_global)
   

    if begin_interaction_loop and not wait_for_opinion:
        print("=======================================================")
        print("Caught human bla")
        begin_interaction_loop=False
        human_bla = str(message.data.get('utterances')[0])
        print(f'Human said "{human_bla}"')

        if SAVE_BLA and len(human_bla)>MIN_CHAR_SAVE:
            with open('./case_study/data/heard_human.txt', "a") as f:#Add it to conversation historics
                f.write(human_bla + ". ")
                print("Saved Human bla")
        #LAUNCH INTERACT LOOP PART 1
        interact1(human_bla)

    elif wait_for_opinion and not begin_interaction_loop:
        wait_for_opinion=False
        print("=======================================================")
        print("Caught human opinion")
        human_opinion = str(message.data.get('utterances')[0])
        print(f'Human said "{human_opinion}"')
        client.emit(Message('speak', data={'utterance': "Noted."}))
        if SAVE_BLA and len(human_opinion)>MIN_CHAR_SAVE:
            with open('./case_study/data/heard_human.txt', "a") as f:#Add it to conversation historics
                f.write(human_opinion + ". ")
                print("Saved Human opinion")
        #LAUNCH INTERACT LOOP PART 2
        interact2(human_opinion)

    #if keyboard.is_pressed('q'):#TODO: OK as such ? Save more files ? ACTIVATE WHEN CHRIS IUS AUDIO !
    #    print("Ending our Interaction...")
    #    sys.exit()



#***********************************************************************MAIN PROCEDURE************************************************************************


def interact1(human_bla):
    """
        Interaction with the VA.
    """
    global self_graph
    global self_data
    global memory
    global concept_1
    global concept_2
    global extract_1
    global begin_interaction_loop
    global wait_for_opinion
    global timeout_start
    
    #(1) Chris update its lifetime, save it and ask the listener to be patient.
    print("=======================================================")
    print("Step 1--Preliminaries")
    print("=======================================================")
    client.emit(Message('speak', data={'utterance': "Let me think about this."}))
    
    self_data["lifetime"]+=1
    with open('./case_study/data/selfdata.txt', 'w') as outfile:
        json.dump(self_data, outfile)

    #(2) Chris extract one or two word from utterance
    # Look at words for which exist wikipedia Page and not in self_graph nor in memory. 
    print("=======================================================")
    print("step 2- Extract words from humam Bla") #NO GPt2 in default core QUEST i love trees etc check why printed
    print("=======================================================")
    OKWikipedia, self_graph=coreQuest.extractWiki(human_bla, self_graph, memory, MAX_PICK_WORD)
    print("Words extracted from human blabla:", OKWikipedia)
    
    #(3) Pick one word from this list (if not empty)
    #And look for similar concept in self graph.
    print("=======================================================")
    print("Step 3--Look for a similar self-concept")
    print("=======================================================")
    no_new_concept=False
    if OKWikipedia==[]:
        no_new_concept=True #did not hear any new word
        if_added_concept=False
        print("Did not hear any new word interesting in human blabla.")
    else:
        new_concept=random.choice(OKWikipedia)
        print("Picked a new concept:", new_concept)
        self_graph, if_added_concept, closer_concept=coreQuest.isSelf(self_graph, new_concept, n_sim_concept,threshold_similarity)
        print("Closer concept in self-graph {}. If added it to self graph: {}".format(closer_concept, if_added_concept))
        #Update memory with this concept
        memory.append(new_concept)
        with open('./case_study/data/memory.txt', "a") as f:
            f.write("\n"+new_concept)
        #if added concept, update self graph:
        if if_added_concept:
            with open('./case_study/data/selfgraph.txt', 'w') as outfile:# update self graph:
                json.dump(self_graph, outfile)
        concept_1,concept_2=new_concept,closer_concept


    #(4A) ONLINE SURF AND SCRAP 
    print("=======================================================")
    print("step 4--Pick Concepts")
    print("=======================================================")
    #CASE A. Has not find a new concept interesting him. Will Look about two self concepts online. or one ?
    if no_new_concept or (not if_added_concept):
        client.emit(Message('speak', data={'utterance': "I am not interested by this question. "}))
        client.emit(Message('speak', data={'utterance': "But let me tell you what I am interested about."}))
        self_concepts=self_graph.keys()#his self-graph
        concept_1= random.choice(list(self_concepts)) #Or pick last?
        concept_2=concept_1
        while concept_1==concept_2:#so not same
            concept_2=random.choice(list(self_concepts))
    
    #CASE B. Has picked some interesting concept, and try find the link...
    else:#if_added concept true
        phrase="Oh. This is interesting."
        client.emit(Message('speak', data={'utterance': phrase}))

    #(5) ONLINE SURF AND SCRAP 
    print("=======================================================")
    print("step 5--Surf online space and Scrap")
    print("=======================================================")
    #Form query and Scrap online space
    query= concept_1+ " "+ concept_2
    interest="I wonder how " + concept_1+ " and "+ concept_2 + " come together ."
    client.emit(Message('speak', data={'utterance': interest}))
    print(interest)
    print("Now surfing the online space...")
    nb_char_extract=BOUND_CHAR_EXTRACT+random.randint(-BOUND_CHAR_EXTRACT_VARIANCE, BOUND_CHAR_EXTRACT_VARIANCE)
    #FOR TESTING ONLY TEMP REMOVE SCRAPER
    scraped_data, extract_1=[], "blue whales surfing USA "
    #scraped_data, extract_1=scraper.surf_google(query, MIN_CHAR_BIT, MIN_CHAR_BLOCK, nb_char_extract) 
    
    #SAVE DATA THAT WAS SCRAPED
    with open('./case_study/data/heard_online.txt', "a") as f:
        for text in scraped_data:
            f.write(text)
        print("Saved scraped data")

    #(6) Say a bit of the article about what found online
    print("=======================================================")
    print("step 6---Share what found")
    print("=======================================================")
    client.emit(Message('speak', data={'utterance': "Let me share what I found while surfing the online space."}))#Change these sentence
    client.emit(Message('speak', data={'utterance': extract_1}))

    begin_interaction_loop=False
    wait_for_opinion=True
    #So do not ask the question too fast below
    #wait_while_speaking()#TODO: CHECK WITH WAIT WHILE SPEAKING

    #(7) Ask: What do you think about it?
    print("=======================================================")
    print("step 7----Ask for human opinion")
    print("=======================================================")
    ask_opinion="What do you think about it ?"
    client.emit(Message('speak', data={'utterance': ask_opinion}))#Change these sentence
    timeout_start=time.time()
    print("Waiting for human opinion (or anything)...")



def interact2(human_bla):
    """
        End of an interaction loop with an human. 
        At the end of this loop, the VA is listening still for a possible other loop.
    """
    global self_graph   
    global memory
    global self_data
    global concept_3
    global begin_interaction_loop
    
    print("=======================================================")
    print("step 8----Extract new concept from human opinion")
    print("=======================================================")
    #(7) Pick a new concept from human opinion:
    OKWikipedia, self_graph=coreQuest.extractWiki(human_bla, self_graph, memory, MAX_PICK_WORD)
    print("Words extracted from human opinion:", OKWikipedia)
   
    found_new_concept=False
     #CASE A where empty: AS SUCH STILL WOULD GIVE HIS OPINION 
    if OKWikipedia==[]:
        print("Did not find anything interesting in this opinion.")
        message="Noted. But I dont see how this is interesting."
        client.emit(Message('speak', data={'utterance': message}))

    #CASE B where found new concept
    else:
        found_new_concept=True
        concept_3=random.choice(OKWikipedia)
        print("Picked a new concept:", concept_3)
        message="Ah. Interesting. I wonder how {} is related to {} and {}".format(concept_3, concept_1, concept_2)
        client.emit(Message('speak', data={'utterance': message}))

        #Update memory with this concept
        memory.append(concept_3)
        with open('./case_study/data/memory.txt', "a") as f:
            f.write("\n"+concept_3)

        print("=======================================================")
        print("step 9----New Surf & Scrap.")
        print("=======================================================")
        #(9) New surf& scrap with these 3 concepts. and Save
        new_query= concept_3 + " "+ concept_1+ " "+ concept_2
        print("Now surfing the online space...")
        print("New Query", new_query)
        #FOR TESTING ONLYYY
        scraped_data_2, extract_2=[], "blue whales surfing USA "
        nb_char_extract=int(BOUND_CHAR_EXTRACT+BOUND_CHAR_EXTRACT_VARIANCE*random.uniform(-1,1))
        #scraped_data_2, extract_2=scraper.surf_google(new_query, MIN_CHAR_BIT, MIN_CHAR_BLOCK, nb_char_extract)
        #SAVE DATA THAT WAS SCRAPED
        print("Save scraped data...")
        with open('./case_study/data/heard_online.txt', "a") as f:
            for text in scraped_data_2:
                f.write(text)

        print("=======================================================")
        print("step 10----Share what found online ")
        print("=======================================================")
        #(10) Say a bit of the article about what found online
        client.emit(Message('speak', data={'utterance': "Let me share what I just found."}))
        client.emit(Message('speak', data={'utterance': extract_2}))

    print("=======================================================")
    print("step 11----Give his own opinion")
    print("=======================================================")
    #(11) Give his own opinion: generate it with gpt-2
    if found_new_concept:
        seed=extract_1[:SEED_LENGTH]+ " " + extract_2[:SEED_LENGTH]
    else:
        seed=extract_1[:SEED_LENGTH]
    context= seed+"\n"+"I think"#Or add sth?
    length_output=OPINION_LENGTH + random.randint(-OPINION_LENGTH_VARIANCE, +OPINION_LENGTH_VARIANCE)
    TEMPERATURE_gpt2=TEMPERATURE+TEMPERATURE_VARIANCE*random.uniform(-1,1)
    opinion=gpt2_text_generation(context, length_output, TEMPERATURE_gpt2) 
    opinion = opinion.replace(seed, "") #TODO: REMOVE context from output...???
    print("Opinion VA:", opinion)
    
    print("=======================================================")
    print("END INTERACTION LOOP")
    print("=======================================================")
    begin_interaction_loop=True #reset open to begin interaction again
    #RELAUNCH THE INITIAL INTERACTION (this happens in LOOP)
    print("=======================================================")
    print("LAUNCH NEW INTERACTION LOOP")
    print("=======================================================")
    print("listening...")
    
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
self_graph, memory, self_data=loadSelf(FIRST_RUN)#

#########(2) LAUNCH THE INTERACTION (running in loop)
print("=======================================================")
print("LAUNCH INTERACTION LOOP")
print("=======================================================")
print("listening...")
#client.run_in_thread() #here require loop again
client.on('recognizer_loop:utterance', interact_with_human_global) 


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
    
#     if SAVE_BLA:
#         with open('./case_study/data/heard.txt', "a") as f:#Add it to conversation historics
#             f.write(human_bla + ". ")
#             print("Recorded Human")

# def record_VA_utterance(message):
#     """
#         Record utterance of what the VA say
#     """
#     VA_bla = message.data.get('utterance')
#     print('VA said "{}"'.format(VA_bla))

#     if SAVE_BLA and len(VA_bla)>keepThreshold:
#         with open('./case_study/data/heard.txt', "a") as f:#Add it to conversation historics
#             f.write(VA_bla + ". ")
#             print("Recorded VA")


