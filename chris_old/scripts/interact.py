

#Main Script for the Interaction between you and your voice assistant



#***********************************************************************CUSTOMIZATION***************************************************************************
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

###IMPORT other scripts
import core #Main script, with the different procedures
import visualize as vis #to visualize the selfGraph
#Import for Mycroft
import os.path
from os import path
from mycroft_bus_client import MessageBusClient, Message
from mycroft.audio import wait_while_speaking

###PARAMETERS
mycroftTriggers=dict()
mycroftTriggers["audioRecord"]=wakeUpWord+"start recording for 2 minutes."
mycroftTriggers["audioPlay"]=wakeUpWord+"play the recording."
mycroftTriggers["remember"]=wakeUpWord+"what did you remember?"
mycroftTriggers["laugh"]=wakeUpWord+"random laughter."
mycroftTriggers["toRemember"]=wakeUpWord+"remember "
mycroftTriggers["DuckDuckGo"]=wakeUpWord
mycroftTriggers["Wikipedia"]=wakeUpWord+"tell me about "

lastHumanBla="I like trees. Trees are green. They can burn. I can burn too. I'm free. "

#***********************************************************************PRELIMINARIES*************************************************************************

#Mycroft init
print('Setting up client to connect to a local mycroft instance. ')
client = MessageBusClient()
print('Conversation may start.')
client.on('recognizer_loop:utterance', record_human_utterance)
wait_while_speaking() #wait for Mycroft to finish speaking. Useless now, but will be helpful later
client.run_forever()

#***********************************************************************PROCEDURES*************************************************************************

#Return the appropriate trigger along what has listened to.
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


#Record the utterance of the Human
def record_human_utterance(message):
    said = str(message.data.get('utterances')[0])
    print(f'Human said "{said}"')#is the f normal????
    lastHumanBla=said #record it in global variable
    #with open('learnings.txt', 'a+') as t: #
        #t.write(said + ' ')

#***********************************************************************MAIN INTERACTION*************************************************************************


def interactLoop(loopCount, rememberedStuff, mood='neutral', lengthML=200, nMLDrift=1, ifEvolve=True, randomizeMood=True):
    print('Interaction n°', loopCount)
    #(0) Catch what the human is saying
    client.on('recognizer_loop:utterance', record_human_utterance)
    print('Human said', humanBla)

    #(1) May Trigger a reaction, if something has been heard. If it is a bla, do it for each sentence if trigger something
    trigger, answer, ifSave=trigger(humanBla)
    #For some skills, may save what VA has said for the evolution.
    if ifSave and not trigger=="":
        savedBla=humanBla +" /n"+ answer
    else:
        savedBla=humanBla

    #(2) MLDrift, from what has been said, in a certain mood.
    #If has chosen to randomize mood, pick a mood according probabilities given.
    if randomizeMood:
        mood=core.whichMood(probaMood)
    blablaVA=drifts(humanBla, mood, lengthML, nMLDrift)

    #(3) ifEvolve, the VA records what has been said to later grow from it
    #Save the selfGraph and Update the files at the end of the interaction (the text heard (to grow form it),the remember)
    if ifEvole:
        with open('./chris/data/whatVAHeard.txt', "a") as f:#Last historics before Chris learned
           f.write(savedBla)
        with open('./chris/data/whatVARemember.txt', "w") as f:
            f.write("\n".join(rememberedStuff))

    return savedBla


def interact(mood='neutral', lengthML=200, nMLDrift=1, ifEvolve=True, randomizeMood=True, visualizeGraph=False):
    loopCount=0
    savedBla=""
    #Load what VA remembered stuff.
    with open('./chris/data/whatVARemember.txt', "r") as f:
        rememberedStuff=f.readlines() #List of what he remembers

    #Interact until press key 'q' on keyboard:
    while not keyboard.is_pressed('q'):
        loopCount++
        savedBla+=interactLoop(loopCount, rememberedStuff, mood, lengthML, nMLDrift, ifEvolve, randomizeMood)

    print('Human ended interaction.')

    #Visualise graph if specified.
    if visualizeGraph:
        vis.drawGraph()
    return savedBla


#***********************************************************************END*************************************************************************

#Direct Launch Interact
if __name__ == '__main__':
    fire.Fire(interact)
