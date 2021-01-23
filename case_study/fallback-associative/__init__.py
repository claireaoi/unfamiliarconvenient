# !/usr/local/bin/python3
# -*- coding: utf-8 -*-

######Description############
#
# FallBack Skill where...
#
######About############
#***********************************************************************LIBRARY IMPORT***************************************************************************

###IMPORT libraries
import numpy as np
import random
import re
import json
import time
import urllib.request
import os.path 
from os import path
#from mycroft.audio import wait_while_speaking
from transformers import GPT2Tokenizer, GPT2LMHeadModel
#Import from other scripts
import scraper
from utils import loadSelf, extractWiki, isSelf

#***********************************************************************PARAMETERS***************************************************************************

#####PARAMETERS WHICH EVOLVE#############
#TODO: EVOLVE both With size graph: nSelf=len(list(self.graph.keys()))
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
path_ML_model='./gpt-2'
global SAVE_BLA
SAVE_BLA=True
global timeout_start
timeout_start=0

#TODO: CHANGE PATHS

#***********************************************************************INITIALIZATION MYCROFT***************************************************************************

from mycroft.skills.core import FallbackSkill


#***********************************************************************PRELIMINARIES***************************************************************************
#TODO: DIVIDE into 2 handle, one for opinion, one for beginning..
#***********************************************************************MAIN CLASS***************************************************************************

class AssociativeFallback(FallbackSkill):
    """
        A Fallback skill running some associative self quest, mapping the world
    """
    def __init__(self):
        super(AssociativeFallback, self).__init__()
        self.tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        if OWN_ML_MODEL:
            self.model=GPT2LMHeadModel.from_pretrained(path_ML_model)
        else:
            self.model=GPT2LMHeadModel.from_pretrained("gpt2") 
        self.graph, self.data=loadSelf(FIRST_RUN, MAX_PICK_WORD, threshold_similarity)
        self.state_interaction="beginning"#ELSE "opinion.."
        self.concepts,self.extracts =[], []


    def initialize(self):
        """
            Registers the fallback handler.
            The second Argument is the priority associated to the request.
            Lower is higher priority. But number 1-4 are bypassing other skills.
            Can register several handle
        """
        self.register_fallback(self.handle_associative, 1)#1 means always trigger it here
        #TODO: Have two different handle one for begin_interaction, other for opinion
        #self.register_fallback(self.handle_begin_interaction, 2)#1 means always trigger it here
        #self.register_fallback(self.handle_opinion, 3)#1 means always trigger it here

        
    def handle_associative(self, message):
        """
            to handle the utterance. 
        """
        #(0) Get the human utterance
        utterance = message.data.get("utterance")
        
        #(1) LOOK IF TIMEOUT OPINION
        timeout_end = time.time()
        timeout=timeout_end-timeout_start
        if self.state_interaction=="opinion" and timeout>OPINION_TIMEOUT:
            self.state_interaction=="beginning"
            print("Timeout. Human had no opinion ...:(")
            print("=======================================================")
            print("LAUNCH NEW INTERACTION LOOP")
            print("=======================================================")

        ###(2) INITIALISATION: if beginning....
        if self.state_interaction=="beginning": 
            self.concepts,self.extracts=[], [] #init back
            self.state_interaction=="opinion"
            print("=======================================================")
            print("Caught human bla")
            human_bla = str(message.data.get('utterances')[0])
            print(f'Human said "{human_bla}"')
            if SAVE_BLA and len(human_bla)>MIN_CHAR_SAVE:
                with open('./data/heard_human.txt', "a") as f:#Add it to conversation historics
                    f.write(human_bla + ". ")
                    print("Saved Human bla")
            #LAUNCH INTERACT LOOP PART 1
            self.interact_part1(human_bla)

        else:
            self.state_interaction=="beginning"#for after, reinit. HERE or below?
            print("=======================================================")
            print("Caught human opinion")
            human_opinion = str(message.data.get('utterances')[0])
            print(f'Human said "{human_opinion}"')
            self.speak("Noted.")
            if SAVE_BLA and len(human_opinion)>MIN_CHAR_SAVE:
                with open('./data/heard_human.txt', "a") as f:#Add it to conversation historics
                    f.write(human_opinion + ". ")
                    print("Saved Human opinion")
            #LAUNCH INTERACT LOOP PART 2
            self.interact_part2(human_opinion)

        return True#IF HANDLED...


    


    #the Skill creator must make sure the skill handler is removed when the Skill is shutdown by the system.
    def shutdown(self):
        """
            Remove this skill from list of fallback skills.
        """
        self.remove_fallback(self.handle_associative)
        #self.remove_fallback(self.handle_opinion)
        #self.remove_fallback(self.handle_beginning)
        super(AssociativeFallback, self).shutdown()


    def gpt2_text_generation(self, context, length_output, TEMPERATURE): 
        """
            One ML drift with gpt-2, with a context. Printed and said by VA.
            With some stochasticity
        """
        process = self.tokenizer.encode(context, return_tensors = "pt")
        generator = self.model.generate(process, max_length = length_output, TEMPERATURE = TEMPERATURE, repetition_penalty = 2.0, do_sample=True, top_k=20)
        drift = self.tokenizer.decode(generator.tolist()[0])
        self.speak(drift)
        return drift


    def interact_part1(self, human_bla):
        """
            Interaction with the VA.
        """

        global timeout_start
        
        #(1) Chris update its lifetime, save it and ask the listener to be patient.
        print("=======================================================")
        print("Step 1--Preliminaries")
        print("=======================================================")
        self.speak( "Let me think about this.")       
        self.data["lifetime"]+=1

        #(2) Chris extract one or two word from utterance
        # Look at words for which exist wikipedia Page and not in self.graph nor in self.memory. 
        print("=======================================================")
        print("step 2- Extract words from humam Bla") #NO GPt2 in default core QUEST i love trees etc check why printed
        print("=======================================================")
        OKWikipedia, self.graph=extractWiki(human_bla, self.graph, self.data["memory"], MAX_PICK_WORD)
        print("Words extracted from human blabla:", OKWikipedia)
        
        #(3) Pick one word from this list (if not empty)
        #And look for similar concept in self graph.
        print("=======================================================")
        print("Step 3--Look for a similar self-concept...or pick his own")
        print("=======================================================")
        no_new_concept, if_added_concept=False, False
        if OKWikipedia==[]:
            no_new_concept=True
            print("Did not hear any new word interesting in human blabla.")
        else:
            new_concept=random.choice(OKWikipedia)
            print("Picked a new concept:", new_concept)
            self.graph, if_added_concept, closer_concept=isSelf(self.graph, new_concept, n_sim_concept,threshold_similarity)
            print("Closer concept in self-graph {}. If added it to self graph: {}".format(closer_concept, if_added_concept))
            self.data["memory"].append(new_concept)#update memory and save
            with open('./data/selfdata.txt', 'w') as outfile:
                json.dump(self.data, outfile)
            if if_added_concept:
                self.concepts=[new_concept,closer_concept]
                with open('./data/selfgraph.txt', 'w') as outfile:# update self graph:
                    json.dump(self.graph, outfile)
                phrase="Oh. This is interesting."
                self.speak(phrase)
            else:
                print("Did not find a concept similar enough.")
        #Has not find a new concept interesting him. Will Look about two self concepts online. or one ?
        if no_new_concept or (not if_added_concept):
            self.speak("I am not interested by this question. ")
            self.speak("But let me tell you what I am interested about.")
            concepts=self.graph.keys()#his self-graph
            self.concepts=[random.choice(list(concepts))] #Or pick last?
            self.concepts.append(self.concepts[0])#append with same
            while self.concepts[0]==self.concepts[1]:#so not same
                self.concepts[1]=random.choice(list(concepts))
        

        #(4) ONLINE SURF AND SCRAP 
        print("=======================================================")
        print("step 4--Surf online space and Scrap")
        print("=======================================================")
        #Form query and Scrap online space
        query= self.concepts[0]+ " "+ self.concepts[1]
        interest="I wonder how " + self.concepts[0]+ " and "+ self.concepts[1] + " come together ."
        self.speak(interest)
        print(interest+ "\n"+ "Now surfing the online space...")
        nb_char_extract=BOUND_CHAR_EXTRACT+random.randint(-BOUND_CHAR_EXTRACT_VARIANCE, BOUND_CHAR_EXTRACT_VARIANCE)
        #FOR TESTING ONLY TEMP REMOVE SCRAPER
        scraped_data, extract=[], "blue whales surfing USA "
        #scraped_data, extract=scraper.surf_google(query, MIN_CHAR_BIT, MIN_CHAR_BLOCK, nb_char_extract) 
        self.extracts=[extract]

        #SAVE DATA THAT WAS SCRAPED 
        with open('./data/heard_online.txt', "a") as f:
            print("Saved scraped data")
            for text in scraped_data:
                f.write(text)

        #(6) Say a bit of the article about what found online
        print("=======================================================")
        print("step 5---Share what found")
        print("=======================================================")
        self.speak("Let me share what I found while surfing the online space.")
        self.speak(self.extracts[0])
        #wait_while_speaking()#TODO: CHECK WITH WAIT WHILE SPEAKING

        #(7) Ask: What do you think about it?
        print("=======================================================")
        print("step 6----Ask for human opinion")
        print("=======================================================")
        self.state_interaction="opinion"
        ask_opinion="What do you think about it ?"
        self.speak(ask_opinion)
        timeout_start=time.time()
        print("Waiting for human opinion (or anything)...")


    def interact_part2(self, human_bla):
        """
            End of an interaction loop with an human. 
            At the end of this loop, the VA is listening still for a possible other loop.
        """        
        print("=======================================================")
        print("step 7----Extract new concept from human opinion")
        print("=======================================================")
        #(7) Pick a new concept from human opinion:
        OKWikipedia, self.graph=extractWiki(human_bla, self.graph, self.data["memory"], MAX_PICK_WORD)
        print("Words extracted from human opinion:", OKWikipedia)
    
        if OKWikipedia==[]:#CASE A where empty: AS SUCH STILL WOULD GIVE HIS OPINION 
            print("Did not find anything interesting in this opinion.")
            message="Noted. But I dont see how this is interesting."
            self.speak(message)

        else: #CASE B where found new concept
            self.concepts.append(random.choice(OKWikipedia))
            print("Picked a new concept:", self.concepts[2])
            message="Ah. Interesting. I wonder how {} is related to {} and {}".format(self.concepts[2], self.concepts[0], self.concepts[1])
            self.speak(message)
            #Update self.memory with this concept and save data
            self.data["memory"].append(self.concepts[2])
            with open('./data/selfdata.txt', 'w') as outfile:
                json.dump(self.data, outfile)

            print("=======================================================")
            print("step 8----New Surf & Scrap.")
            print("=======================================================")
            #(9) New surf& scrap with these 3 concepts. and Save
            new_query= self.concepts[2] + " "+ self.concepts[0]+ " "+ self.concepts[1]
            print("Now surfing the online space looking for {} .".format(new_query))
            #FOR TESTING ONLYYY
            scraped_data_2, extract_2=[], "blue whales surfing USA"
            nb_char_extract=int(BOUND_CHAR_EXTRACT+BOUND_CHAR_EXTRACT_VARIANCE*random.uniform(-1,1))
            self.extracts.append(extract_2)#IF NOT EMPTY...
            #scraped_data_2, extract_2=scraper.surf_google(new_query, MIN_CHAR_BIT, MIN_CHAR_BLOCK, nb_char_extract)
            with open('./data/heard_online.txt', "a") as f:#save data
                print("Save scraped data...")
                for text in scraped_data_2:
                    f.write(text)

            print("=======================================================")
            print("step 9----Share what found online ")
            print("=======================================================")
            #(10) Say a bit of the article about what found online
            self.speak("Let me share what I just found.")
            self.speak(self.extracts[1])


        print("=======================================================")
        print("step 10----Give his own opinion")
        print("=======================================================")
        #(11) Give his own opinion: generate it with gpt-2
        if len(self.extracts)>1:
            seed=self.extracts[0][:SEED_LENGTH]+ " " + self.extracts[1][:SEED_LENGTH]
        else:
            seed=self.extracts[0][:SEED_LENGTH]
        context= seed+"\n"+"I think"#Or add sth?
        length_output=OPINION_LENGTH + random.randint(-OPINION_LENGTH_VARIANCE, +OPINION_LENGTH_VARIANCE)
        temperature_gpt2=TEMPERATURE+TEMPERATURE_VARIANCE*random.uniform(-1,1)
        opinion=self.gpt2_text_generation(context, length_output, temperature_gpt2) 
        opinion = opinion.replace(seed, "") #TODO: OK? REMOVED CONTEXT ? CHECK WITHOUT...
        print("Opinion VA:", opinion)

        print("=======================================================")
        print("END INTERACTION LOOP")
        print("=======================================================")
        print("LAUNCH NEW INTERACTION LOOP")
        self.state_interaction="beginning"
        print("listening...")
       
        


#***********************************************************************create SKILL***************************************************************************

def create_skill():
    return AssociativeFallback()
