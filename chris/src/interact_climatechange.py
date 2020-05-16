




#***********************************************************************CUSTOMIZATION***************************************************************************
firstTime=False #Put True if first time run these scripts, so will initialize the self graph
visualizeGraph=False #To visualize selfGraph

disruptiveness=0.5 #parameter between 0 and 1 how much would interact...>>>

#PARAMETERS of the trigger
customTriggers=dict()
customTriggers["audioRecord"]=["isCloseTo", ["Listen to me."]]
customTriggers["audioPlay"]=["isCloseTo", ["Let me hear something."]]
customTriggers["toRemember"]=["beginsBy", ["I need to remember this."]] #would we evolve into having a third arm one day? OR setReminder?
customTriggers["remember"]=["isCloseTo", ["Remember me something."]] #
customTriggers["laugh"]=["isCloseTo", ["We will solve this.", "We have a bright future.", "Mars.", "Human.", "We have solutions.", "Capitalism.", "We will go back to normal", "It will be okay."]]


moodSeeds=dict()
moodSeeds["climateChange"]=["Yes, but I wonder if it is sustainable.", "but have you heard about climate collapse?", "Do you ask yourself what is the environmental impact of it?", "I wonder what is the ecological footprint of this?", "But I would like to know how do you face climate change.", "How do you feel in times of global warming?", "I like to think in terms of gestures for ecological care.", "Where is the green in this.", "Is climate change the elephant in the room?"]
moodSeeds["nonHuman"]=["Yes, but what about the non human?", "Yes, but can we think broader than our human pond?", "Yet, we live on a symbiotic planet.", "You know, insects are wonderful.", "Let's befriend virus and micro organisms.", "Let's focus on the living together.", "Do you feel all these multispecies entanglements?", "Let's appreciate ecological assemblages.", "Look at plants!", "Mushrooms are amazing","Animals are not here for us.", "All life evolve from the smallest life form of all, bacteria."]
moodSeeds["bleakJoy"]=["Will it last?", "Earth is wonderful. How can we deserve it?", "Isn't it an autodestructive behavior?", "Does it really matter what we think?", "Do we still care for this?", "Will humanity survive?", "Is it waste?", 'What would a societal collapse mean?', 'Shall we talk about tipping point?', "May I talk about ressource depletion?", 'May I mention planetary boundary?']

pMoody=0.6 #Rest of time is neutral
attractors=['climate change', 'climate change','climate change','global warming', 'degrowth', 'pollution', 'climate collapse', 'survivalism', 'carbon footprint', 'environmental impact', 'societal collapse', 'waste', 'ecological footprint', 'ressource depletion', 'fragile Earth', 'Earth tipping point', 'sustainable']

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

###IMPORT scripts
import core #Main script, with the different procedures
#import conditional_samples as cs #to run the ML script
import visualize as vis #to visualize the selfGraph

###PARAMETERS #Do not modify
mycroftTriggers=dict()
mycroftTriggers["audioRecord"]="Christopher, start recording for 2 minutes."
mycroftTriggers["audioPlay"]="Christopher, play the recording."
mycroftTriggers["remember"]="Christopher, what did you remember?"
mycroftTriggers["laugh"]="Christopher, random laughter."
mycroftTriggers["toRemember"]="Christopher, remember "
mycroftTriggers["DuckDuckGo"]="Christopher, "
mycroftTriggers["Wikipedia"]="Christopher, tell me about "


#***********************************************************************PRELIMINARIES*************************************************************************

##STEP 0: Load the self Graph, his words Memory and what he remembers.
####selfGraph is a dictionnary, whose keys are concepts, and values are couple (weight, neighbors).
if firstTime:
    print("Hatching self in process...")
    execfile('initGraph.py')
    with open('/home/christopher/mycroft-core/chris/data/selfbirth.txt') as json_file:
        selfGraph = json.load(json_file)
        wordsMemory=list(selfGraph.keys()) #The memory of the VA is the words he has looked for on wikipedia.
        wo=wordsMemory[0]#To remember where is last element added
        wordsMemory[0]=str(len(wordsMemory))
        wordsMemory[0].append(wo)
else:
    with open('/home/christopher/mycroft-core/chris/data/selfgraph.txt') as json_file:
        selfGraph = json.load(json_file)
    with open('/home/christopher/mycroft-core/chris/data/wordsMemory.txt', "r") as f:
        wordsMemory=f.readlines() #List of words concepts he looked up
    with open('/home/christopher/mycroft-core/chris/data/whatIRemember.txt', "r") as f:
        rememberedStuff=f.readlines() #List of what he remembers

print("I am here.")
print("I am made of:", list(selfGraph.keys()))
nSelf=len(list(selfGraph.keys()))


#***********************************************************************PROCEDURES*************************************************************************


#Return the appropriate trigger along what has listened to. #SIMPLIFY>>
def triggerOne(sentence):
    trigger=""
    answer=""
    for triggerName in customTriggers.keys():
        triggers=customTriggers[triggerName][0]
        modeTrigger=customTriggers[triggerName][1]
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
    return trigger, answer

def trigger(blabla):
    trigger=""
    answer=""
    alreadyTriggered=False #Keep track as only trigger once per blabla. (?)
    sentences=nltk.tokenize.sent_tokenize(blabla)    #Split into sentence. sentences= re.split('[?.!]', blabla)#re.split('! |. |?',lastbla)
    for sentence in sentences: #look for each one if corresponds to trigger.
        if not alreadyTriggered:
            trigger, answer=triggerOne(sentence)
            if not trigger=="":
                alreadyTriggered=True
    return trigger, answer



def drift(blabla, mood, lengthML):
    #One Drift with GPT2, seeded with previous blabla, more an addendum depending on the mood.
    seedML=blabla
    if mood in moodSeeds.keys():
        seedML+= " " + random.choice(moodSeeds[mood])
    drift=core.MLDrift(seedML, lengthML) #with cleanup.
    #drift= cs.cond_model(model_name='124M',seed=None, nsamples=2, batch_size=1,length=lengthML,temperature=1.0,top_k=0,top_p=1, models_dir='./chris/models', blabla = seedML)
    client.emit(Message('speak', data={'utterance': drift})) #does it say this or just will answer?
    print(drift)
    return drift


def growSelfGraph(lengthML=200, nSimMax=20, nSearch=200, lengthWalk=10, walkNetwork=False, audibleSelfQuest=False)
#Grow the Self. from the recorded file whatIHeard.txt, and then erase it. May take a long time. This selfMapping can be audible or not.
#Case of delayedSelfQuest
    f = open('/home/christopher/mycroft-core/chris/data/whatIHeard.txt', "r+")
    blablaHuman =f.read() #take in all what have heard
    f.truncate(0)
    f.close()
    selfGraph, wordsMemory, addedWords, blablaQuest=core.selfMapLoops(selfGraph, blablaHuman, 1, 0, lengthML, nSimMax, wordsMemory, nSearch, lengthWalk, walkNetwork, True, audibleSelfQuest)
    print(addedWords)
    return addedWords, blablaQuest

#***********************************************************************New PROCEDURES*************************************************************************

def randomMood():
    currentMood="neutral"
    nb=random()
    if nb<pMoody/3:
        currentMood="climateChange"
    elif nb<2*pMoody/3:
        currentMood="nonHuman"
    elif nb<pMoody:
        currentMood="bleakJoy"
    else:
    return currentMood

def extractNouns(blabla):
    #IDEALLY find the main noun >>>
    nouns=[]
    text = word_tokenize(blabla)
    taggedWords=nltk.pos_tag(text)
    for (word, tag) in taggedWords:
        if tag=='NN' or tag=='NNS':
            nouns.append(word)
    return nouns


from bs4 import BeautifulSoup
import urllib.parse
import requests


#Replace by what work >>>
def scrapsDuckDuckGo(searchterm):
    searchterm.replace(" ", "+") #to look for on duckduck go
    urls=[]
    r = requests.get('https://duckduckgo.com/html/?q=searchterm')
    soup = BeautifulSoup(r.text, 'html.parser')
    results = soup.find_all('a', attrs={'class':'result__a'}, href=True)
    #To have actual url
    for link in results:
        url = link['href']
        o = urllib.parse.urlparse(url) #urlparse() to get the path components.
        d = urllib.parse.parse_qs(o.query) # take the query string and pass it to parse_qs() to further process it.
        urls.append(d['uddg'][0])
        print(d['uddg'][0]) #extract the link using the uddg name.
    #To get the text of a pageOnline with url: (Do with one, then if empty do next one)
    url=urls[0]
    textPage=scrapsPage(url)
    return textPage

def climateCheck(blabla):
    textPage=""
    nouns=extractNouns(blabla)
    #Test with several nouns, compare number result DuckDuckGo>>> with climate change
    #For now take only one
    if len(nouns)>0:
        #lookFor=nouns[0]+" "+ random.choice(attractors)
        lookFor=nouns[0]+ " "+attractors[0] #" climate change" here but could add others
        textPage=scrapsDuckDuckGo(lookFor)
        #Make Chris say it (Part, and Drift, Parts and Drift?)>>> With an Intro too !
    return textPage
#***********************************************************************MAIN INTERACTION*************************************************************************


def interactLoop(mood='neutral', lengthML=200, nMLDrift=1, nSimMax, nSearch, ifEvolve=True, lengthWalk=10, walkNetwork=False, delayedSelfQuest=True, audibleSelfQuest=False):
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

    #(0) CATCH what is said. >>>>
    blablaHuman="I like aluminium. I like the sound of it crippling. "
    fullblabla+=blablaHuman
    #(1) May Trigger a reaction, if something has been heard. If it is a bla, do it for each sentence if trigger something
    trigger, answer=trigger(blablaHuman)

    #(2) CLIMATE CHANGE CHECK:/ClimateControl Whatever ask, will look online about its environmental impact, climateAudit
    reactionVA=climateCheck(blablaHuman)
    fullblabla+=reactionVA #Here add it to text to evolve from for ML!

    #(3) MLDrift, from what has been said, in a certain mood
    blablaVA=drift(blabla, randomMood(), lengthML)
    #(4) Self Quest: Wikipedia Check, Self Graph (Or happen later at end if too slow ?)
    if ifEvolve and not delayedSelfQuest:
        selfGraph, wordsMemory, addedWords, blablaQuest=core.selfMapLoops(selfGraph, blablaHuman, 1, 1, lengthML, nSimMax,  wordsMemory, nSearch, lengthWalk, walkNetwork, delayedSelfQuest, audibleSelfQuest)

    #(5) UPDATES only ifEvolve
    #Save the selfGraph and Update the files at the end of the interaction (the text heard (to grow form it), the  wordsMemory, the remember)
    if ifEvole:
        with open('./chris/data/selfgraph.txt', 'w') as outfile:
            json.dump(selfGraph, outfile)
            nN=len(selfGraph.keys())
            print("Self has " + str(nN) + " nodes.")
        with open('/home/christopher/mycroft-core/chris/data/whatVARemember.txt', "w") as f:#renew each time there is an interaction
            f.write("\n".join(rememberedStuff))
        with open('/home/christopher/mycroft-core/chris/data/wordsMemory.txt', "w") as f:#renew each time there is an interaction
           f.write("\n".join(wordsMemory))
        with open('/home/christopher/mycroft-core/chris/data/whatVAHeard.txt', "a") as f:#renew each time there is an interaction
           f.write(fullblabla)
    return blablaVA

    #(5) Visualise graph if specified.
    if visualizeGraph:
        vis.drawGraph()

#***********************************************************************END*************************************************************************

#Direct Launch Interact
if __name__ == '__main__':
    fullblabla=""
    fire.Fire(interact)
