# !/usr/local/bin/python3
# -*- coding: utf-8 -*-


######Description############
#  
# VA is running a self Quest from what he previously heard: he is trying to grow and map his self, represented
# as a self-graph of concepts, and their relations.
#
######About############
# This script was created for the workshop Unfamiliar Virtual Convenient - Growing your Voice Assistant
# led by Vytautas Jankauskas and Claire Glanois through School of Machines, Make & believe, in spring 2020.
# 
# Feel free to tune, or reshape it according to your project.

#***********************************************************************PARAMETERS**************************************************************************


global maxmemory
maxmemory=200 #max memory VA when remember words he has looked up. The first element of memory tells the index of the last element added. To avoid looking for same element repeatedly.

global sleepTime
sleepTime=30 # Dont need a priori

wonders=["I wonder about W ", "Maybe it is worth for me to look into W ", "What W is all about?", "W still makes me confused."]
wakeUpWord="Christopher, "

#***********************************************************************INITIALIZATION***************************************************************************
###IMPORT Library
import fire
import json
import random

###IMPORT scripts
import coreQuest #Main script for the selfQuest, with the different procedures

#For the ML Drift
import transformers
import torch
from transformers import GPT2Tokenizer, GPT2LMHeadModel

###MYCROFT. MessageBus will enable us to control Mycroft through this script (trigger skills, etc.)
from mycroft_bus_client import MessageBusClient, Message
###The Message object is a representation of the messagebus message, this will always contain a message type but can also contain data and context.
####Message('MESSAGE_TYPE', data={'meaning': 42}, context={'origin': 'A.Dent'})
#The MycroftBusClient() object can be setup to connect to any host and port as well as any endpont on that host. 
#If no arguments are provided it will try to connect to a local instance of mycroftr core on the default endpoint and port.
client = MessageBusClient()
client.run_in_thread()
print('Setting up client to connect to a local mycroft instance')

#***********************************************************************PRELIMINARIES*************************************************************************

def loadSelf(firstTime, audible_selfquest, n_search_new_concept):
    """
        The VA loads his self_graph and memory as last saved. Or build it if first time.
    """
    if firstTime:
        blabla=[]
        phrase="Hatching self in process..."
        print(phrase)
        if audible_selfquest:
            client.emit(Message('speak', data={'utterance': phrase}))
        self_graph, memory, description=coreQuest.hatchSelf(n_search_new_concept)
        print(description)
        if audible_selfquest:
            client.emit(Message('speak', data={'utterance': description}))

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

#***********************************************************************PROCEDURES for SELF MAPPING ***************************************************************************


def wonder(word):
    """
    Generate a sentence wondering about word, depending on choice of wonders.
    """
    phrase=""
    sentence=random.choice(wonders)#pick one
    words=sentence.split()
    newwords=[word if x=="W" else x for x in words]
    phrase=" ".join(newwords)
    return phrase


def askVA(question):
    """
        Ask a question to VA, say & record the answer:
    """
    message=Message("recognizer_loop:utterance", {'utterances':[question],'lang':'en-us'})
    #time.sleep(sleepTime) #ok Work ?
    client.emit(message)
    answer="Mycroft said {}".format(message.data.get('utterance'))
    print("Answer:", answer)
    return answer


def oneMLDrift(context, lengthML): 
    """
        One ML drift with gpt-2, with a context. Printed and said by VA.
    """
    process = tokenizer.encode(context, return_tensors = "pt")
    generator = model.generate(process, max_length = lengthML, temperature = 1.0, repetition_penalty = 2)
    drift = tokenizer.decode(generator.tolist()[0])
    client.emit(Message('speak', data={'utterance': drift})) #does it say this or just will answer?
    print(drift)
    return drift

def walkOnNetwork(self_graph, start_word, length_walk):
    """
         Do a walk on the self_graph, starting from a concept, during length_walk steps, or unless end up at a deadend of the graph
    """
    n_step=0
    deadEnd=False
    word=start_word
    while n_step<length_walk and not deadEnd:
        if  len(list(self_graph[word][1].keys()))>0: #reminder: self_graph[word][1] is a dictionnary of the neighbors.
            next_word=random.choice(self_graph[word][1].keys())
            statement= "Path  "+ str(round(self_graph[word][1][next_word],2)) + " towards "+ next_word + ", "+ str(round(self_graph[next_word][0],3)) + ". "
            print(statement)
            client.emit(Message('speak', data={'utterance': statement})) #or all answer ?
            word=next_word
            n_step+=1
        else:
            deadEnd=True
            client.emit(Message('speak', data={'utterance': "It is a dead end of myself."})) #or all answer ?
    if not deadEnd:
        client.emit(Message('speak', data={'utterance': "Walk ended here."})) #or all answer ?


def selfMapping(word, self_graph, memory, ifMLDrift=False, lengthML=100, n_search_sim_concept=5, length_walk=10, walk_network=False, audible_selfquest=False):
    """
        Self Mapping where look if a specific word is related to his selfm and possibly grow his self_graph.
        This can be audible, and integrate or not a ML drift and a walk on the network
    """
    answer=""
    drift=""

    ###(1) Ask Chris about a work on wikipedia
    if audible_selfquest:
        question="Tell me about " + word +"." #Dont need wake up word ?
        phrase=wonder(word) #Phrase to be heard. Can generate Others>>>
        client.emit(Message('speak', data={'utterance': phrase}))
        print(phrase)
        answer = askVA(question)  #VA answer and read wikipedia page here

    ###(2) Possible ML Drift from the last sentence, case where audibleSelf Quest only.
    if ifMLDrift:
        drift=oneMLDrift(answer, lengthML) 

    ##(3) Self Awareness Quest: look if this word is related to Self. May have modified the self graph here!
    print("Looking if {} is related to Self...".format(word))
    self_graph, if_added_concept, simWord, similarity_score=coreQuest.isSelf(self_graph, word, n_search_sim_concept)
    nSelf=len(list(self_graph.keys()))

    #(4) State the progress of his selfAwareness quest, aloud if audible Self quest, else only print
    if if_added_concept:   #Case where the word was found related to self
        selfAwareness="Oh, "+ word +" is similar to " + simWord+ "and hence to me at "+  str(round(similarity_score,2)) + "Now I know more about myself. "
        print(selfAwareness)
    else: #Case where the word was not found related to self
        selfAwareness= "Whatever, "+ word + ", may not be very related to myself. "
        print(selfAwareness)
    if audible_selfquest:
        client.emit(Message('speak', data={'utterance': selfAwareness}))

    #(5) Walk on the network if stated and added the word
    if walk_network and if_added_concept:
        walkOnNetwork(self_graph, word, length_walk)

    #(6) Add word looked for Memory. Just beware if memory full.
    if len(memory)==maxmemory+1: #Memory Full, erase the older one.
        if memory[0]==str(len(memory)-1):
            memory[0]=str(1)
        else:
            memory[0]=str(int(memory[0])+1)
        memory[memory[0]]=word
    else:
        memory.append(word.lower()) #Add word to memory when has wiki checked it. Only lowered words here
        memory[0]=str(int(memory[0])+1) #in 0 element keep track

    return self_graph, memory, answer, drift, if_added_concept

def selfMapLoops(heard, self_graph, ifMLDrift, lengthML, n_search_sim_concept, memory, n_search_new_concept, walk_network=False, length_walk=10, audible_selfquest=False):
   
    """
        VA try to grows his self_graph from an inital blabla with possible ML drifts, walks on the network, audible Quest, etc.
    """
    blabla=""
    addedWords=[]

    #(0) If selfQuest not audible, no ML drift no walk on Network
    if not audible_selfquest:
        ifMLDrift=False
        walk_network=False

    #(1) Look at words for which exist wikipedia Page and not in self_graph nor in memory. n_search_new_concept is the Nb word max will look for in Wikipedia
    OKWikipedia, self_graph=coreQuest.extractWiki(heard, self_graph, memory, n_search_new_concept)#actually real n_search_new_concept may double because of composed words.
 
    #(2A) If no words to look, will drift with ML first to have a new text to loop from.
    if len(OKWikipedia)==0: #If the list is empty
        phrase="No new concepts to grow from."
        print(phrase)
        if audible_selfquest:
            client.emit(Message('speak', data={'utterance': phrase}))

   #(2B) Look for one concept after another
    else:
        for word in OKWikipedia:
            print("Current look up word:", word)

            self_graph, memory, answer, drift, if_added_concept=selfMapping(word, self_graph, memory, ifMLDrift, lengthML, n_search_sim_concept, length_walk, walk_network, audible_selfquest)
          
            if if_added_concept:
                addedWords.append(word)
                blabla=blabla+ "\n"+ answer + "\n"+ drift
    
    return self_graph, memory, addedWords, blabla



#*********************************************************************** MAIN PROCEDURE*************************************************************************


def selfQuest(firstTime=False, walk_network=False, audible_selfquest=False, visualizeGraph=True, ifMLDrift=False, lengthML=100, n_search_sim_concept=50, n_search_new_concept=100, length_walk=10, finetuned_ML_model=True, path_finetuned_ML_model='./chris/models/gpt-2'): #ifVisualize
    """
         Self Quest with possible ML drits, walks on the network, audible Quest, visualisation of the Graph, etc.
         The VA is aiming at growing his self Concept, from what he has heard (in the file heard). 
    """
   
    # Initialize machine learning
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    if finetuned_ML_model:
        model=GPT2LMHeadModel.from_pretrained(path_finetuned_ML_model)
    else:
        model=GPT2LMHeadModel.from_pretrained("gpt2")

    
    #(0) Load SELF, memory, and what the VA has heard since last time.
    ## SelfGraph is a dictionnary, whose keys are concepts, and values are couple (weight, neighbors).
    self_graph, memory, heard=loadSelf(firstTime, audible_selfquest, n_search_new_concept)


    #(1) Self Quest, with possible walk on the network, possible ML drifts, and parameters, from the text heard
    #If not first time (if first time, assume heard is empty)
    if not firstTime:
        self_graph, memory, addedWords, blabla_quest=selfMapLoops(whatVAHear, self_graph, ifMLDrift, lengthML, n_search_sim_concept,  memory, n_search_new_concept, walk_network, length_walk, audible_selfquest)

    #(2) State new Self
    nN=len(list(self_graph.keys()))
    phrase= "Self has now " + str(nN) + " nodes."+ "Self is made of:"+ ', '.join(list(self_graph.keys()))
    print(phrase)
    if audible_selfquest:
        client.emit(Message('speak', data={'utterance': phrase}))

    #(3) Update the self_graph and the memory
    with open('./chris/data/selfgraph.txt', 'w') as outfile:
        json.dump(self_graph, outfile)

    with open('./chris/data/memory.txt', "w") as f:
        f.write("\n".join(memory))

    #(4) Visualize if want
    if visualizeGraph:
        graph, descriptionSelf=coreQuest.createGraph(self_graph)
        coreQuest.drawGraph(graph)
        if audible_selfquest: #Description of himself. Could comment out if too annoying.
            client.emit(Message('speak', data={'utterance': descrptionSelf}))

#Direct Launch Interact
if __name__ == '__main__':
    fire.Fire(selfQuest)
