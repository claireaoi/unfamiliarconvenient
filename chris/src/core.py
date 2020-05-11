



#***********************************************************************PARAMETERS for the SCRIPT**************************************************************************

# Should tune parameters according to our experiments. or event vary them, or make them probabilistic (some of them).
#>>>>CHANGE and parameters separate? put them in interact ??? HAS TO TEST! lengthML, selfAwareness sentence can change too>>>
thresholdSim=0.6 #threshold when Consider 2 concepts as similar
maxFuckedUp=0.9#max ration of fucked up lines
maxWordsMemory=200#max memory VA when remember words he has looked up. The first element of memory tells the index of the last element added. To avoid looking for same element repeatedly.
sleepTime=30
wonders=["I wonder about W ", "Maybe it is worth for me to look into W ", "What W is all about?", "W still makes me confused."]

#***********************************************************************INITIALIZATION***************************************************************************

###IMPORT general
import fire
import numpy as np
import re
import random
import json
import string
import time
import Levenshtein as lev
import nltk #For NLP
from nltk.corpus import words, wordnet
from nltk.stem.wordnet import WordNetLemmatizer
import urllib.request
from nltk import word_tokenize, sent_tokenize, pos_tag
from sematch.semantic.similarity import WordNetSimilarity #To check Word Similarity
wns = WordNetSimilarity()

#IMPORT other scripts
import wiki #for wikipedia self Mapping
import conditional_samples as cs #to run the ML script
import visualize as vis #to visualize the selfGraph

###MYCROFT. MessageBus will enable us to control Mycroft through this script (trigger skills, etc.)
from mycroft_bus_client import MessageBusClient, Message
###The Message object is a representation of the messagebus message, this will always contain a message type but can also contain data and context.
####Message('MESSAGE_TYPE', data={'meaning': 42}, context={'origin': 'A.Dent'})
#The MycroftBusClient() object can be setup to connect to any host and port as well as any endpont on that host. #If no arguments are provided it will try to connect to a local instance of mycroftr core on the default endpoint and port.
client.run_in_thread()
print('Setting up client to connect to a local mycroft instance')
client = MessageBusClient()


#***********************************************************************PROCEDURES for ML Drift*************************************************************************


def MLDrift(seedSentence, lengthML=100):
#One ML Drift with GPT2, seeded with a string. Printed and said by Chris.
    drift= cs.cond_model(model_name='124M',seed=None, nsamples=2, batch_size=1,length=lengthML,temperature=1.0,top_k=0,top_p=1, models_dir='./chris/models', blabla = seedSentence)
    drift, fuckedUp=cleanText(drift)
    print(drift)
    while fuckedUp>maxFuckedUp:
        print("Fucked Up ML. Try again.")
        drift= cs.cond_model(model_name='124M',seed=None, nsamples=1, batch_size=1,length=lengthML,temperature=1.0,top_k=0,top_p=1, models_dir='./chris/models', blabla = seedSentence)
        drift, fuckedUp=cleanText(drift)
    client.emit(Message('speak', data={'utterance': drift})) #does it say this or just will answer?
    print(drift)
    return drift

def MLDrifts(seedSentence, nDrift, lengthML):
    #Several successive drifts with GPT2, seeded with a string
    blabla=""
    lastbla=""
    for i in range(nDrift):
        lastbla= MLDrift(seedSentence, lengthML)
        listS=lastbla.split(".") #listS = re.split('! |. |?',lastbla) #List sentences.
        lastblacut='.'.join(listS[0 : len(listS)-2]) #Remove last one because may be uncomplete...>
        seedSentence=listS[len(listS)-2]
        blabla+= "\n"+ lastblacut +"\n"
    return blabla


def alphabetRatio(inputString):
    #Count alphabet letter ratio in a string.
    count=0
    for char in inputString:
        if char.isalpha():
            count+=1
    if len(inputString)==0:
         return 0
    else:
        return count/len(inputString)

#GRAMMAR To Implement grammar check?>>>>
def makeSense(blabla):
    okGrammar=True
    #https://pypi.org/project/grammar-check/ pip install grammar-check ? if see outcome...
    return okGrammar

#To Clean output of ML Drift.
def cleanText(blabla):
    sentences=nltk.tokenize.sent_tokenize(blabla)
    blabli=""
    for sentence in sentences:
        alphabetic=alphabetRatio(sentence) #ration non letter elements
        if len(sentence)>3 and alphabetic>0.7 and makeSense:   #Test if not to many symbol and grammar ok
                blabli+=sentence
    fuckedUp = (len(blabli) + len(blabla))/len(blabla)
    return blabli, fuckedUp


#***********************************************************************PROCEDURES for SELF QUEST*************************************************************************

#walkOnNetwork, Do a walk on the selfGraph, starting from startWord, and for length lengthWalk unless end up in a leaf of the graph.
def walkOnNetwork(selfGraph, startWord, lengthWalk):
    nStep=0
    deadEnd=False
    word=startWord
    while nStep<lengthWalk and not deadEnd:
        if  len(selfGraph[word][1].keys())>0: #reminder: selfGraph[word][1] is a dictionnary of the neighbors.
            nextWord=random.choice(selfGraph[word][1].keys())
            statement= "Path  "+ str(round(chrisGraph[word][1][nextWord],2)) + " towards "+ nextWord + ", "+ str(round(selfGraph[nextWord][0],3)) + ". "
            print(statement)
            client.emit(Message('speak', data={'utterance': statement})) #or all answer ?
            word=nextWord
            nStep+=1
        else:
            deadEnd=True
            client.emit(Message('speak', data={'utterance': "It is a dead end of myself."})) #or all answer ?
    if not deadEnd:
        client.emit(Message('speak', data={'utterance': "Walk ended here."})) #or all answer ?


def isSelf(selfGraph, word, nSimMax):
    #Check if a word (not belonging to his self) is related to his selfGraph.
    indices=random.sample(range(0, nSelf), min(nSimMax, nSelf)) #Generate random list of indices where will look for
    selfGraph[word]=[0,dict()]   #Add entry to dictionary for now
    ifConnected=False
    maxSim=0
    simWord=""
    #Check similarity with other concepts in Self
    for i, wordSelf in list(selfGraph.keys()):
        if i in indices:
            simScore= semanticSimilarity(word,wordSelf)
            if simScore>thresholdSim:
                selfGraph[word][1][wordSelf]=simScore#Add a connection if related enough.
                selfGraph[wordSelf][1][word]=simScore#Symmetric
                ifConnected=True
                #Retain the closer concept that have found
                if simScore>maxSim:
                    maxSim=simScore
                    simWord=wordSelf
    #Conclude if related
    if not ifConnected: #Not related, ie no connection with SelfConcept was above a fixed threshold.
        del selfGraph[word] #delete entry from SelfGraph therefore
    else: # if related
        selfGraph[word][0]=maxSim*selfGraph[simWord][0] #adjust the weight of the node
    return selfGraph, ifConnected, simWord, simScore

def wonder(word):
    #Generate a sentence wondering about word, depending on choice of wonders.
    phrase=""
    sentence=random.choice(wonders)#pick one
    words=sentence.split()
    newwords=[word if x=="W" else x for x in words]
    phrase=" ".join(newwords)
    return phrase

#A wikipedia Loop to grow his awareness of self, with possibly MLDrift, and the option for it to be audible or not.
def selfMapping(selfGraph, word, memory, nDrift=1, lengthML=200, nSimMax=5, lengthWalk=10, walkNetwork=False, audibleSelfQuest=False):
    ###(1) Ask Chris about a work on wikipedia
    if audibleSelfQuest:
            question="Christopher, tell me about " + word +"." #For Chris
            phrase=wonder(word) #Phrase to be heard. Generate Others.>>>
            client.emit(Message('speak', data={'utterance': phrase}))
            print("Question:", phrase)
            #Chris answer
            answer = askChris(question)
    else: #If are not asking the question, are not neither drifting.
        nDrift=0
    ###(2) Possible ML Drifts from the last sentence
    if nDrift>0:
        drift=MLDrifts(answer, nDrift, lengthML)
    ##(3) Self Awareness Quest: look if this word is related to Self
    selfGraph, ifadded, simWord, simScore=isSelf(word, nSimMax)
    nSelf=len(list(selfGraph.keys()))
    #State out loud the progress of his selfAwareness quest if audibleSelfQuest is True
    if ifadded:   #Case where word related to a word in SelfGraph.
        selfAwareness="Oh, "+ word +" is similar to " + simWord+ "and hence to me at "+  str(round(simScore,2)) + "Now I know more about myself. "
        print(selfAwareness)
        if audibleSelfQuest:
            client.emit(Message('speak', data={'utterance': selfAwareness}))
    #(4) Walk on the network if stated and added the word
        walkOnNetwork(word, lengthWalk)
    else: #Case where may not be related
        selfAwareness= "Whatever, "+ word + ", may not be very related to myself. "
        print(selfAwareness)
        if audibleSelfQuest:
            client.emit(Message('speak', data={'utterance': selfAwareness}))
    #(5) Add in Memory. Beware if memory full...
    if len(memory)==maxWordsMemory+1: #Memory Full, erase the older one.
        if memory[0]==len(memory)-1:
            memory[0]=str(1)
        else:
            memory[0]=str(int(memory[0])+1)
        memory[memory[0]]=word
    else:
        memory.append(word.lower()) #Add word to memory when has wiki checked it. Only lowered words here
        memory[0]=str(int(memory[0])+1) #in 0 element keep track
    return selfGraph, memory, answer, drift, ifadded

def selfMapLoops(selfGraph, blabla, nLoop, nDrift, lengthML, nSimMax, memory, nSearch, lengthWalk=10, walkNetwork=False, delayedSelfQuest=True, audibleSelfQuest=False):
    #(0) Look at words for which exist wikipedia Page and not in selfGraph nor in memory. nSearch  is the Nb word max will look for in Wikipedia
    OKWikipedia,OKWiktionary,selfGraph=wiki.extract(blabla, selfGraph, memory, nSearch)#actually real nSearch may double because of composed words.
    answer=""
    drift=""
    blabla=""
    ifadded=False
    addedWords=[]
    #(1A) If no words to look, will drift with ML first to have a new text to loop from.
    if len(OKWikipedia)==0: #If the list is empty
        blabla=MLDrifts(blabla, nDrift, lengthML)
        if nLoop>1:
            selfGraph, memory, addedWords, blabla=selfMapLoops(selfGraph, answer, nLoop-1, nDrift, lengthML, nSimMax,  memory, nSearch, lengthWalk, walkNetwork, delayedSelfQuest, audibleSelfQuest)
    elif delayedSelfQuest:#Take them all in OKWikipedia in that case, but ignore Loop
        for word in OKWikipedia:
            print("Look up word:", word)
            selfGraph, memory, answer, drift, ifadded=selfMapping(selfGraph, word, memory, nDrift, lengthML, nSimMax, lengthWalk, walkNetwork, audibleSelfQuest)
            blabla=answer + "\n"+ drift
            if ifadded:
                addedWords.append(word)
    else:
        word=random.choice(OKWikipedia)
        print("Look up word:", word)
        #(1B) else, pick a word and try to look it up
        selfGraph, memory, answer, drift, ifadded=selfMapping(selfGraph, word, memory, nDrift, lengthML, nSimMax, lengthWalk, walkNetwork, audibleSelfQuest)
        #(2B) then, ML drift from answer if added the world, or last drift
        if nLoop>1 and ifadded:
            selfGraph, memory, addedWords, blabla=selfMapLoops(selfGraph, answer, nLoop-1, nDrift, lengthML, nSimMax, memory, nSearch, lengthWalk, walkNetwork, delayedSelfQuest, audibleSelfQuest)
            addedWords.append(word)
            blabla="\n"+ answer + "\n"+ drift +"\n"+ blabla
        elif nLoop>1:
            selfGraph, memory, addedWords, blabla=selfMapLoops(selfGraph, drift, nLoop-1, nDrift, lengthML, nSimMax, memory, nSearch, lengthWalk, walkNetwork, delayedSelfQuest, audibleSelfQuest)
            blabla="\n"+ answer + "\n"+ drift +"\n"+ blabla
    return selfGraph, memory, addedWords, blabla

#Compute semantic similarity score between 2 words.
#Could Try other possibilities for semabtic sim>>>  Beware then, score like 0.03 so adjust threshold>>>
def semanticSimilarity(word1, word2):
    score=0
    splitWord=word1.split()
    if len(splitWord)>1:  #If word is a composed word: average similarity of its both elements.
        for elt in splitWord:
            score+=semanticSimilarity(elt, word2)
        score/=len(splitWord)
    else:#word1 has 1 compo
        splitWord2=word2.split()
        if len(splitWord2)>1:#case word2 has 2 compo or more
            for elt in splitWord2:#Else could take the max but would be non symmetic
                score+=wns.word_similarity(word1, elt, 'li')
            score/=len(splitWord2)
        else:#case both only 1 element
            score=wns.word_similarity(word1, word2, 'li')
    print('Similarity score between ' + word1 + ' and ' + word2 , score)
    return score

#***********************************************************************PROCEDURES for TRIGGER*************************************************************************


def isCloseTo(sentence, triggers):
#Levenshtein Distance or fuzzy string matching fuzzywuzzy Check if fast>>
    isCloseTo=False
    for trigger in triggers:
        if not isCloseTo:
            similarity=lev.ratio(sentence.lower(),trigger.lower())
            isCloseTo=(similarity>=0.85)
    return isCloseTo

def beginsBy(sentence, triggers):
    beginsBy=False
    for trigger in triggers:
        beginsBy=beginsBy or (sentence.lower().startsWith(trigger.lower()))
    return beginsBy

def beginsByCut(sentence, triggers):
    beginsBy=False
    cutSentence=""
    for trigger in triggers:
        if not beginsBy:
            beginsBy=(sentence.lower().startsWith(trigger.lower()))
            if beginsBy:
                cutSentence=sentence.replace(trigger,'')
    return [beginsBy, cutSentence]

#***********************************************************************MAIN PROCEDURES*************************************************************************

#Ask a question to Chris, say & record the answer:
def askChris(question):
    message=Message("recognizer_loop:utterance", {'utterances':[question],'lang':'en-us'})
    time.sleep(sleepTime)
    client.emit(message)
    time.sleep(sleepTime)
    answer="Mycroft said {}".format(message.data.get('utterance'))
    print("Answer:", answer)
    return answer

def saveGraph():
    # Save selfGraph into file selfgraph.txt. Print number vertices
    with open('./chris/data/selfgraph.txt', 'w') as outfile:
        json.dump(selfGraph, outfile)
        nN=len(selfGraph.keys())
        print("Self has " + str(nN) + " nodes.")


def oneCycle(question,  answerHuman, nLoop, nDrift, lengthML, nSimMax, memory, nSearch, lengthWalk, walkNetwork, delayedSelfQuest, audibleSelfQuest=False):
    #(0) Ask Question. Add the part when this question is picked from audio
    print("Question:", question)
    #(1) Chris answer only if answerHuman
    if answerHuman:
        answer = askChris(question)
        print("Answer", answer)
    #(2) Self Mapping Loops involving Wikipedia loopup, similarity with Self checkup, walk on the network and possibly ML Drifts
    selfGraph, memory, addedWords, blabla=selfMapLoops(selfGraph, question, nLoop, nDrift, lengthML, nSimMax, memory, nSearch, lengthWalk, walkNetwork, delayedSelfQuest, audibleSelfQuest)
    #(3) Save and Visualize new self Graph
    saveGraph()
    vis.drawGraph()
    return selfGraph, memory, blabla
