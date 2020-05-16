

#Main Script for the Interaction between you and your voice assistant



#***********************************************************************CUSTOMIZATION***************************************************************************
firstTime=False #Put True if first time run these scripts, so will initialize the self graph
wakeUpWord="Christopher, "

#PARAMETERS of the trigger
customTriggers=dict()
customTriggers["audioRecord"]=[False, "isCloseTo", ["I feel being listened to."]]
customTriggers["audioPlay"]=[False, "isCloseTo", ["Let me hear."]]
customTriggers["toRemember"]=[False, "beginsBy", ["I wonder "]] #would we evolve into having a third arm one day? OR setReminder?
customTriggers["remember"]=[False, "isCloseTo", ["Remember something."]] #
customTriggers["laugh"]=[False, "isCloseTo", ["I'm free.", "I love you."]]
customTriggers["DuckDuckGo"]=[True, "beginsBy",["Why", "How"]] #how do i twerk? Why people google?
customTriggers["Wikipedia"]=[True, "beginsByCut", ["I know about "]] #I know about ... #Special case, as will cut out I know about...


moodSeeds=dict()
moodSeeds["curious"]=["Why are they", "Why do they", "How could we", "I wonder if", "I wonder how", "Why are there still", "What should we think of", "Is there something like"]
moodSeeds["confrontational"]=["Maybe not.", "Yet, I feel this is wrong. ", "I would argue against this.", "I would prefer not to.", "What if this is bullshit?", "I don't believe in this. Listen,"]
moodSeeds["thrilled"]=["Amazing.", "That is wonderful.", "How beautiful is this.", "That is incredible."]
moodSeeds["emotional"]=["It makes me feel", "I feel like"]
moodSeeds["appreciative"]=["Let us appreciate how", "Let us contemplate the", "Now, let us breathe and take a moment for", "Let us welcome the", "Let us appreciate what", "Instead of opposing, we shoud embrace", "I would like to thank the world for what"]
moodSeeds["thrilled"]=["Amazing.", "That is wonderful.", "How beautiful is this.", "That is incredible."]
moodSeeds["neutral"]=[""]

#Randomize the Moods:
probaMood=dict()
probaMood["curious"]=0.2
probaMood["confrontational"]=0.2
probaMood["thrilled"]=0.1
probaMood["emotional"]=0.1
probaMood["appreciative"]=0.1
probaMood["thrilled"]=0.1
probaMood["neutral"]=0.2

#***********************************************************************INITIALIZATION***************************************************************************

###IMPORT libraries
import fire
import numpy as np
import random
import re
import nltk #For NLP
from nltk.corpus import words, wordnet
from nltk.stem.wordnet import WordNetLemmatizer
import urllib.request
from nltk import word_tokenize, sent_tokenize, pos_tag
import keyboard  # using module keyboard

###IMPORT scripts
import core #Main script, with the different procedures
import visualize as vis #to visualize the selfGraph

#Import for Mycroft
import os.path
from os import path
from mycroft_bus_client import MessageBusClient, Message
from mycroft.audio import wait_while_speaking

###PARAMETERS
#Do not modify
lastHumanBla="I like trees. Trees are green. They can burn. I can burn too. I'm free. "
loopCount=0
mycroftTriggers=dict()
mycroftTriggers["audioRecord"]=wakeUpWord+"start recording for 2 minutes."
mycroftTriggers["audioPlay"]=wakeUpWord+"play the recording."
mycroftTriggers["remember"]=wakeUpWord+"what did you remember?"
mycroftTriggers["laugh"]=wakeUpWord+"random laughter."
mycroftTriggers["toRemember"]=wakeUpWord+"remember "
mycroftTriggers["DuckDuckGo"]=wakeUpWord
mycroftTriggers["Wikipedia"]=wakeUpWord+"tell me about "


#Mycroft Catching what human say
print('Setting up client to connect to a local mycroft instance. ')
client = MessageBusClient()
print('Conversation may start.')
client.on('recognizer_loop:utterance', record_human_utterance)
wait_while_speaking() #wait for Mycroft to finish speaking. Useless now, but will be helpful later
client.run_forever()

#***********************************************************************PRELIMINARIES*************************************************************************

##STEP 0: Load the self Graph, his words Memory and what he remembers.
####selfGraph is a dictionnary, whose keys are concepts, and values are couple (weight, neighbors).
if firstTime:
    print("Hatching self in process...")
    execfile('./chris/src/initGraph.py')
    with open('./chris/data/selfbirth.txt') as json_file:
        selfGraph = json.load(json_file)
        wordsMemory=list(selfGraph.keys()) #The memory of the VA is the words he has looked for on wikipedia.
        wo=wordsMemory[0]#To remember where is last element added
        wordsMemory[0]=str(len(wordsMemory))
        wordsMemory[0].append(wo)
else:
    with open('./chris/data/selfgraph.txt') as json_file:
        selfGraph = json.load(json_file)
    with open('./chris/data/wordsMemory.txt', "r") as f:
        wordsMemory=f.readlines() #List of words concepts he looked up
    with open('./chris/data/whatVARemember.txt', "r") as f:
        rememberedStuff=f.readlines() #List of what he remembers

print("I am here.")
print("I am made of:", list(selfGraph.keys()))
nSelf=len(list(selfGraph.keys()))


#***********************************************************************PROCEDURES*************************************************************************


#Return the appropriate trigger along what has listened to. #SIMPLIFY>>
def triggerSkill(sentence):
    trigger=""
    answer=""
    for triggerName in customTriggers.keys():
        triggers=customTriggers[triggerName][2]
        modeTrigger=customTriggers[triggerName][1]
        ifSave=customTriggers[triggerName][0]
        if modeTrigger=="beginsByCut":
            begin, cutSentence=core.beginsByCut(sentence,triggers)
            if begin:
                trigger=mycroftTriggers[triggerName]+cutSentence.lower()
        elif modeTrigger=="isCloseTo" and core.isCloseTo(sentence,triggers):
            trigger=mycroftTriggers[triggerName]
        elif modeTrigger=="beginsBy" and core.beginsBy(sentence,triggers):
            trigger=mycroftTriggers[triggerName]+sentence.lower()
    #If one trigger has been activated
    if not trigger=="":
        answer=core.askChris(trigger)
        print("Answer", answer)
    return trigger, answer, ifSave

def trigger(blabla):
    trigger=""
    answer=""
    alreadyTriggered=False #Keep track as only trigger once per blabla. (?)
    sentences=nltk.tokenize.sent_tokenize(blabla)    #Split into sentence. sentences= re.split('[?.!]', blabla)#re.split('! |. |?',lastbla)
    for sentence in sentences: #look for each one if corresponds to trigger.
        if not alreadyTriggered:
            trigger, answer, ifSave=triggerSkill(sentence)
            if not trigger=="":
                alreadyTriggered=True
    return trigger, answer, ifSave


def drifts(blabla, mood, lengthML, nMLDrift):
    #Few Drift with GPT2, seeded with previous blabla, more an addendum depending on the mood.
    seedML=blabla
    if mood in moodSeeds.keys():
        seedML+= " " + random.choice(moodSeeds[mood])
    drift=core.MLDrift(seedML, lengthML) #with cleanup.
    #drift= cs.cond_model(model_name='124M',seed=None, nsamples=2, batch_size=1,length=lengthML,temperature=1.0,top_k=0,top_p=1, models_dir='./chris/models', blabla = seedML)
    client.emit(Message('speak', data={'utterance': drift})) #does it say this or just will answer?
    print(drift)
    if nMLDrift>1:
        drift+=drifts(drift, mood, lengthML, nMLDrift-1)
    return drift

def growSelfGraph(lengthML=200, nSimMax=20, nSearch=200, lengthWalk=10, walkNetwork=False, audibleSelfQuest=False):
#Grow the Self. from the recorded file whatVAHeard.txt, and then erase it. May take a long time. This selfMapping can be audible or not.
#Case of delayedSelfQuest
    f = open('./chris/data/whatVAHeard.txt', "r+")
    blablaHuman =f.read() #take in all what have heard
    f.truncate(0)
    f.close()
    selfGraph, wordsMemory, addedWords, blablaQuest=core.selfMapLoops(selfGraph, blablaHuman, 1, 0, lengthML, nSimMax, wordsMemory, nSearch, lengthWalk, walkNetwork, True, audibleSelfQuest)
    print(addedWords)
    return addedWords, blablaQuest


#Record the utterance of the Human
def record_human_utterance(message):
    said = str(message.data.get('utterances')[0])
    print(f'Human said "{said}"')
    lastHumanBla=said #record it in global variable
    #with open('learnings.txt', 'a+') as t: #
        #t.write(said + ' ')

#***********************************************************************MAIN INTERACTION*************************************************************************


def interact(mood='neutral', lengthML=200, nMLDrift=1, nSimMax=10, nSearch=1, ifEvolve=True, lengthWalk=10, walkNetwork=False, delayedSelfQuest=True, audibleSelfQuest=False, visualizeGraph=False, randomizeMood=True):
    ### PARAMETERS of ML Drift:
    #  mood will affect the beginning of the ML Drift, as a starting tone.
    #  nMLDrift is the number of ML drift
    #  lengthMLDrift is the default number of character of the ML Drift
    ### PARAMETERS of the Self Quest:
    # nSearch is the number of words he will loop for in wikipedia
    # nSimMax is the maximum number of words he will test for similarities
    # delayedSelfQuest=True: by default the selfQuest is not happening in the same time than the interaction (as it slows down the process a lot) but only if specified explicitly
    # audibleSelfQuest determine if the Self Quest would be audible (in case is not delayed)
    #  ifEvolve means the interaction is recorded, and Chris will grow it self from it, also ML will be trained on it. Else, can freeze the VA
    # walkNetwork is a boolean determining if the VA does a walk on the network after each found word, while lengthWalk is the length of this walk.
    loopCount++
    #(0) CATCH what Human say
    print('Interaction n°', loopCount)
    client.on('recognizer_loop:utterance', record_human_utterance)
    print('Human said', lastHumanBla)
    #(1) May Trigger a reaction, if something has been heard. If it is a bla, do it for each sentence if trigger something
    trigger, answer, ifSave=trigger(lastHumanBla)
    if ifSave and not trigger=="": #Save it for later
        saveBla=lastHumanBla +" /n"+ answer
    else:
        saveBla=lastHumanBla
    #(2) MLDrift, from what has been said, in a certain mood.
    #If has chosen to randomize mood, pick a mood according probabilities given.
    if randomizeMood:
        mood=core.whichMood(probaMood)
    blablaVA=drifts(lastHumanBla, mood, lengthML, nMLDrift)

    #(3) ifEvolve, the VA records what has been said to later grow from it
    #Save the selfGraph and Update the files at the end of the interaction (the text heard (to grow form it), the  wordsMemory, the remember)
    if ifEvole:
        with open('./chris/data/whatVAHeard.txt', "a") as f:#Last historics before Chris learned
           f.write(saveBla)
        with open('./chris/data/whatVARemember.txt', "w") as f:
            f.write("\n".join(rememberedStuff))
        with open('./chris/data/wordsMemory.txt', "w") as f:
            f.write("\n".join(wordsMemory))
    return blablaVA
        #(4) If Self Quest: Check some words heard on wikipedia, and grow his SelfGraph. Even though may be slow
        if not delayedSelfQuest:
            selfGraph, wordsMemory, addedWords, blablaQuest=core.selfMapLoops(selfGraph, lastHumanBla, 1, 1, lengthML, nSimMax,  wordsMemory, nSearch, lengthWalk, walkNetwork, delayedSelfQuest, audibleSelfQuest)
            with open('./chris/data/selfgraph.txt', 'w') as outfile:
                json.dump(selfGraph, outfile)
                nN=len(selfGraph.keys())
                print("Self has " + str(nN) + " nodes.")
    #(5) Visualise graph if specified.
    if visualizeGraph:
        vis.drawGraph()

    #(6) Go on unless press key 'q' on keyboard
    if not keyboard.is_pressed('q'):
        interact(mood, lengthML, nMLDrift, nSimMax, nSearch, ifEvolve, lengthWalk, walkNetwork, delayedSelfQuest, audibleSelfQuest, visualizeGraph, randomizeMood)


#***********************************************************************END*************************************************************************

#Direct Launch Interact
if __name__ == '__main__':
    fire.Fire(interact)
