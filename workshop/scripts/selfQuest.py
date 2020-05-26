#####Here the VA is doing a self Quest from what he previously heard.

# !/usr/local/bin/python3
# -*- coding: utf-8 -*-
#***********************************************************************PARAMETERS**************************************************************************


global maxWordsMemory
maxWordsMemory=200 #max memory VA when remember words he has looked up. The first element of memory tells the index of the last element added. To avoid looking for same element repeatedly.

global sleepTime
sleepTime=30 # Dont need a priori

wonders=["I wonder about W ", "Maybe it is worth for me to look into W ", "What W is all about?", "W still makes me confused."]
wakeUpWord="Christopher, "

#***********************************************************************INITIALIZATION***************************************************************************
###IMPORT Library
import fire
import json

###IMPORT scripts
from . import coreQuest #Main script for the selfQuest, with the different procedures

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

def loadSelf(firstTime, audibleSelfQuest, nSearch):
    """
        The VA loads his selfGraph and memory as last saved. Or build it if first time.
    """
    if firstTime:
        blabla=[]
        phrase="Hatching self in process..."
        print(phrase)
        if audibleSelfQuest:
            client.emit(Message('speak', data={'utterance': phrase}))
        selfGraph, wordsMemory, description=coreQuest.hatchSelf(nSearch)
        print(description)
        selfConcepts=list(selfGraph.keys())
        description2="I am made of:" + ", ".join(selfConcepts)
        print(description2)
        if audibleSelfQuest:
            client.emit(Message('speak', data={'utterance': description}))
            client.emit(Message('speak', data={'utterance': description2}))

    else:
        with open('./workshop/data/selfgraph.txt', 'r') as json_file:
            #selfGraph = json.load(json_file)
            selfGraph = eval(json_file.read()) # which one RIGHT ?
        with open('./workshop/data/wordsMemory.txt', "r") as f:
            wordsMemory=f.readlines() #List of words concepts he looked up
        with open('./workshop/data/whatVAHeard.txt', "r") as f: #Last historics before Chris learned
            blabla=f.readlines()
        phrase="I am here. Self Quest can begin."
        print(phrase)
        if audibleSelfQuest:
            client.emit(Message('speak', data={'utterance': phrase}))
  
    return selfGraph, wordsMemory, blabla

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

def walkOnNetwork(selfGraph, startWord, lengthWalk):
    """
         Do a walk on the selfGraph, starting from a concept, during lengthWalk steps, or unless end up at a deadend of the graph
    """
    nStep=0
    deadEnd=False
    word=startWord
    while nStep<lengthWalk and not deadEnd:
        if  len(list(selfGraph[word][1].keys()))>0: #reminder: selfGraph[word][1] is a dictionnary of the neighbors.
            nextWord=random.choice(selfGraph[word][1].keys())
            statement= "Path  "+ str(round(selfGraph[word][1][nextWord],2)) + " towards "+ nextWord + ", "+ str(round(selfGraph[nextWord][0],3)) + ". "
            print(statement)
            client.emit(Message('speak', data={'utterance': statement})) #or all answer ?
            word=nextWord
            nStep+=1
        else:
            deadEnd=True
            client.emit(Message('speak', data={'utterance': "It is a dead end of myself."})) #or all answer ?
    if not deadEnd:
        client.emit(Message('speak', data={'utterance': "Walk ended here."})) #or all answer ?


def selfMapping(word, selfGraph, wordsMemory, ifMLDrift=False, lengthML=100, nSimMax=5, lengthWalk=10, walkNetwork=False, audibleSelfQuest=False):
    """
        Self Mapping where look if a specific word is related to his selfm and possibly grow his selfGraph.
        This can be audible, and integrate or not a ML drift and a walk on the network
    """
    answer=""
    drift=""

    ###(1) Ask Chris about a work on wikipedia
    if audibleSelfQuest:
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
    selfGraph, ifadded, simWord, simScore=coreQuest.isSelf(selfGraph, word, nSimMax)
    nSelf=len(list(selfGraph.keys()))

    #(4) State the progress of his selfAwareness quest, aloud if audible Self quest, else only print
    if ifadded:   #Case where the word was found related to self
        selfAwareness="Oh, "+ word +" is similar to " + simWord+ "and hence to me at "+  str(round(simScore,2)) + "Now I know more about myself. "
        print(selfAwareness)
    else: #Case where the word was not found related to self
        selfAwareness= "Whatever, "+ word + ", may not be very related to myself. "
        print(selfAwareness)
    if audibleSelfQuest:
        client.emit(Message('speak', data={'utterance': selfAwareness}))

    #(5) Walk on the network if stated and added the word
    if walkNetwork and ifadded:
        walkOnNetwork(selfGraph, word, lengthWalk)

    #(6) Add word looked for Memory. Just beware if memory full.
    if len(wordsMemory)==maxWordsMemory+1: #Memory Full, erase the older one.
        if wordsMemory[0]==str(len(wordsMemory)-1):
            wordsMemory[0]=str(1)
        else:
            wordsMemory[0]=str(int(wordsMemory[0])+1)
        wordsMemory[wordsMemory[0]]=word
    else:
        wordsMemory.append(word.lower()) #Add word to memory when has wiki checked it. Only lowered words here
        wordsMemory[0]=str(int(wordsMemory[0])+1) #in 0 element keep track

    return selfGraph, wordsMemory, answer, drift, ifadded

def selfMapLoops(blabla, selfGraph, ifMLDrift, lengthML, nSimMax, wordsMemory, nSearch, walkNetwork=False, lengthWalk=10, audibleSelfQuest=False):
   
    """
        VA try to grows his selfGraph from an inital blabla with possible ML drifts, walks on the network, audible Quest, etc.
    """
    blabla=""
    addedWords=[]

    #(0) If selfQuest not audible, no ML drift no walk on Network
    if not audibleSelfQuest:
        ifMLDrift=False
        walkNetwork=False

    #(1) Look at words for which exist wikipedia Page and not in selfGraph nor in memory. nSearch is the Nb word max will look for in Wikipedia
    OKWikipedia, selfGraph=extractWiki(blabla, selfGraph, wordsMemory, nSearch)#actually real nSearch may double because of composed words.
 
    #(2A) If no words to look, will drift with ML first to have a new text to loop from.
    if len(OKWikipedia)==0: #If the list is empty
        phrase="No new concepts to grow from."
        print(phrase)
        if audibleSelfQuest:
            client.emit(Message('speak', data={'utterance': phrase}))

   #(2B) Look for one concept after another
    else:
        for word in OKWikipedia:
            print("Current look up word:", word)

            selfGraph, wordsMemory, answer, drift, ifadded=selfMapping(word, selfGraph, wordsMemory, ifMLDrift, lengthML, nSimMax, lengthWalk, walkNetwork, audibleSelfQuest)
          
            if ifadded:
                addedWords.append(word)
                blabla=blabla+ "\n"+ answer + "\n"+ drift
    
    return selfGraph, wordsMemory, addedWords, blabla



#*********************************************************************** MAIN PROCEDURE*************************************************************************


def selfQuest(firstTime=False, walkNetwork=False, audibleSelfQuest=False, visualizeGraph=True, ifMLDrift=False, lengthML=100, nSimMax=50, nSearch=100, lengthWalk=10, finetuned_ML_model=True, path_finetuned_ML_model='./workshop/models/gpt-2'): #ifVisualize
    """
         Self Quest with possible ML drits, walks on the network, audible Quest, visualisation of the Graph, etc.
         The VA is aiming at growing his self Concept, from what he has heard (in the file whatVAHeard). 
    """
   
    # Initialize machine learning
    tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
    if finetuned_ML_model:
        model=GPT2LMHeadModel.from_pretrained(path_finetuned_ML_model)
    else:
        model=GPT2LMHeadModel.from_pretrained("gpt2")

    
    #(0) Load SELF, memory, and what the VA has heard since last time.
    ## SelfGraph is a dictionnary, whose keys are concepts, and values are couple (weight, neighbors).
    selfGraph, wordsMemory, blabla=loadSelf(firstTime, audibleSelfQuest, nSearch)


    #(1) Self Quest, with possible walk on the network, possible ML drifts, and parameters, from the text blabla
    #If not first time (if first time, assume blabla is empty)
    if not firstTime:
        selfGraph, wordsMemory, addedWords, blablaQuest=selfMapLoops(blabla, selfGraph, ifMLDrift, lengthML, nSimMax,  wordsMemory, nSearch, walkNetwork, lengthWalk, audibleSelfQuest)

    #(2) State new Self
    nN=len(list(selfGraph.keys()))
    phrase= "Self has now " + str(nN) + " nodes."+ "Self is made of:"+ ', '.join(list(selfGraph.keys()))
    print(phrase)
    if audibleSelfQuest:
        client.emit(Message('speak', data={'utterance': phrase}))

    #(3) Update the selfGraph and the memory
    with open('./workshop/data/selfgraph.txt', 'w') as outfile:
        json.dump(selfGraph, outfile)

    with open('./workshop/data/wordsMemory.txt', "w") as f:
        f.write("\n".join(wordsMemory))

    #(4) Visualize if want
    if ifVisualize:
        graph, descriptionSelf=coreQuest.createGraph(selfGraph)
        coreQuest.drawGraph(graph)
        if audibleSelfQuest: #Description of himself. Could comment out if too annoying.
            client.emit(Message('speak', data={'utterance': descrptionSelf}))

#Direct Launch Interact
if __name__ == '__main__':
    fire.Fire(selfQuest)
