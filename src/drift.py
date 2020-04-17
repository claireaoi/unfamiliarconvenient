



######Before launching this code, the self Graph of Chris should be initialized (with initGraph is not already saved), and saved in a file named selfgraph.


#***********************************************************************INITIALIZATION***************************************************************************

#PARAMETERS:
# Should tune parameters according to our experiments. or event vary them, or make them probabilistic (some of them).
counter=0
thresholdSim=0.6 #threshold when Consider 2 concepts as similar
memory=[] # memory of concepts he checked on wikipedia, he 'knows about'
fuckedUp=0
maxFuckedUp=0.3#max ration of fucked up lines
waitingList=[]
lengthPath=11 #length walk on the network
nSearch=8

###IMPORT general
import fire
import numpy as np
import re
import random
import json
import string
import time
#from gtts import gTTS ######TEXT to SPEECH. this module needs internet (google). Dont need it anymore ?
#import os
#IMPORT NLP
import nltk #https://www.guru99.com/pos-tagging-chunking-nltk.html type nltk
from nltk.corpus import words, wordnet
from nltk.stem.wordnet import WordNetLemmatizer
import urllib.request
from nltk import word_tokenize, sent_tokenize, pos_tag
from sematch.semantic.similarity import WordNetSimilarity
wns = WordNetSimilarity()
#IMPORT other scripts coded
import wiki
import conditional_samples as cs
import visualize as vis
#from parameters import *
#import ask
#import seed
###MYCROFT
from mycroft_bus_client import MessageBusClient, Message
###The Message object is a representation of the messagebus message, this will always contain a message type but can also contain data and context.
####Message('MESSAGE_TYPE', data={'meaning': 42}, context={'origin': 'A.Dent'})
print('Setting up client to connect to a local mycroft instance')
client = MessageBusClient() #The MycroftBusClient() object can be setup to connect to any host and port as well as any endpont on that host. #If no arguments are provided it will try to connect to a local instance of mycroftr core on the default endpoint and port.
client.run_in_thread()

##STEP 0; Load the self Graph
####selfGraph is a dictionnary, whose keys are concepts, and values are couple (weight, neighbors).
##Neighbors is a dictionnary whose keys are related concepts and values are weights
with open('/home/christopher/mycroft-core/chris/data/selfbirth.txt') as json_file:
    selfGraph = json.load(json_file)
print("Self is Here.")
print("Initial Concepts within Self:", list(selfGraph.keys()))
memory=list(selfGraph.keys()) #Init memory. Memory is all word has looked for ? Forget sometimes, as when grow network, could be actually connected with it again..>>>

#***********************************************************************PROCEDURES*************************************************************************

def nonLetters(inputString):
    count=0
    if inputString=="":
        return 0
    else:
        for char in inputString:
            if char.isalpha():
                count+=1
        return count/len(inputString)

# One Drift with GPT2, seeded with a string. Printed and said by Chris.
#Could modify parameters as lengthML etc.
def MLDrift(seedSentence):
    lengthML=100
    drift= cs.cond_model(model_name='124M',seed=None, nsamples=2, batch_size=1,length=lengthML,temperature=1.0,top_k=0,top_p=1, models_dir='./chris/models', blabla = seedSentence)
    # drift, fuckedUp=cleanText(drift)
    global fuckedUp
    while fuckedUp>maxFuckedUp:
        print("Fucked Up ML. Try again.")
        drift= cs.cond_model(model_name='124M',seed=None, nsamples=1, batch_size=1,length=lengthML,temperature=1.0,top_k=0,top_p=1, models_dir='./chris/models', blabla = seedSentence)
        drift, fuckedUp=cleanText(drift)
    client.emit(Message('speak', data={'utterance': drift})) #does it say this or just will answer?
    print(drift)
    return drift

#Several successive drifts with GPT2, seeded with a string
nbDrift = 2
def MLDrifts(seedSentence='Are we human?', nDrift=nbDrift):
    counter=0
    blabla=""
    lastbla=""
    for i in range(nDrift):
        lastbla= MLDrift(seedSentence)
        listS=lastbla.split(".") #listS = re.split('! |. |?',lastbla) #List sentences.
        lastblacut='.'.join(listS[0 : len(listS)-2])#Remove last one because may be uncomplete...>
        seedSentence=listS[len(listS)-2]
        blabla+= "\n"+ "NEW DRIFT"+ lastblacut +"\n" #remove then the NEW DRIFT
        counter+=1
    return blabla

#Ask a question to Chris, say & record the answer:
def askChris(question):
    message=Message("recognizer_loop:utterance", {'utterances':[question],'lang':'en-us'})
    time.sleep(30)
    client.emit(message)
    time.sleep(30)
    answer="Mycroft said {}".format(message.data.get('utterance'))
    print("Answer:", answer)
    return answer

#Do a walk on the selfGraph, starting from startWord, and for length lengthPath unless end up in a leaf of the graph.
def walkOnNetwork(startWord, lengthPath):
    nStep=0
    deadEnd=False
    word=startWord
    while nStep<lengthPath and not deadEnd:
        if  len(selfGraph[word][1].keys())>0: #reminder: selfGraph[word][1] is a dictionnary of the neighbors.
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


def selfAwarenessQuest(word):
    #Check if a word is related to his selfGraph.
    #This word shall not belong to his selfGraph already. (for now)
    #When selfGraph would be too big and too long to check, could check only for a few words and only for a limited nb (50) of selfWord randomly chosen or the initial ones
    selfGraph[word]=[0,dict()]   #Add entry to dictionary for now
    ifConnected=False
    maxSim=0
    simWord=""
    #Check similarity with other concepts in Self
    for wordSelf in list(selfGraph.keys()):
        simScore= semanticSimilarity(word,wordSelf)
        if simScore>thresholdSim:
            selfGraph[word][1][wordSelf]=simScore#Add a connection if related enough.
            selfGraph[wordSelf][1][word]=simScore#Symmetric
            ifConnected=True
            #Retain the more connected concept
            if simScore>maxSim:
                maxSim=simScore
                simWord=wordSelf
    #Conclude if related
    if not ifConnected: #Not related, ie no connection with SelfConcept was above a fixed threshold.
        del selfGraph[word] #delete entry from SelfGraph if so
    else: # Related
        selfGraph[word][0]=maxSim*selfGraph[simWord][0] #weigth node
    return ifConnected, simWord, simScore

#Generate a sentence wondering wbout word
wonders=["I wonder about W ", "Maybe it is worth for me to look into W ", "What W is all about?", "W still makes me confused."]
def wonder(word):
    phrase=""
    sentence=random.choice(wonders)#pick one
    words=sentence.split()
    newwords=[word if x=="W" else x for x in words]
    phrase=" ".join(newwords)
    return phrase

#A wikipedia Loop
def wikiDrifts(word, nDrift):
    ###(0) Question to Chris / word
    question="Christopher, tell me about " + word +"." #For Chris
    phrase=wonder(word) #Phrase to be heard. Generate Others.>>>
    print("Question:", phrase)
    memory.append(word.lower()) #Add word to memory when check it. Only lowered words here
    client.emit(Message('speak', data={'utterance': phrase}))
    ###(1) Chris Answer
    answer = askChris(question)     #Ask question to Chris, and answer
    ###(2) ML Drifts from the last sentence
    #From the answer, extract a seed for the ML drift. Could modify this seed later >>
    seeds= re.split('[?.!]', answer)
    if len(seeds)>1:#Take last full sentence. Only ?
        seed=seeds[-2]
    else:
        seed=seeds[0]
    lastdrift=MLDrifts(seed, nDrift) #ML DRIFT#
    ##(3) Self Awareness Quest: look if this word is related to Self
    ifadded, simWord, simScore=selfAwarenessQuest(word)
    #State out loud the progress of his selfAwareness quest.
    #Could change and vary this sentence>
    if ifadded:   #Case where word related to a word in SelfGraph.
        #selfAwareness="Oh, "+ word +"is similar to " + simWord+ "and hence to Self at "+  str(round(simScore,2)) + ". I know more about myself. "
        selfAwareness="Oh, "+ word +"is similar to " + simWord+ "and therefore to my un understanding of Self" + ". Now I know more about myself. "
        print(selfAwareness)
        client.emit(Message('speak', data={'utterance': selfAwareness}))
    else: #Could also Make Mycroft state it loud in case of failure>
        selfAwareness= "Whatever, "+ word + ", does not seem very related to myself. "
        print(selfAwareness)
        client.emit(Message('speak', data={'utterance': selfAwareness}))
    return answer, lastdrift, ifadded

def wikiLoops(blabla, nLoop, nDrift):
    OKWikipedia,OKWiktionary=wiki.extract(blabla, selfGraph, memory, nSearch) #Words for which exist wikipedia Page and not in selfGraph. Bound search to beginning
    #Pick a random choice from list. If the list is empty, pick a word from the waiting list
    while len(OKWikipedia)==0: #No words to look for here, so will first drift with ML, and then start wikiloops
        blabla=MLDrifts(blabla, 1)
        OKWikipedia,OKWiktionary=wiki.extract(blabla, selfGraph, memory, nSearch)
    else:
        word=random.choice(OKWikipedia)
    print("Word chosen:", word)
    answer, drift, ifadded=wikiDrifts(word, nDrift)
    if nLoop>1 and ifadded: #Go on from answer. Transition sentence? >. Or always look from this ?
        answer, drift, ifadded=wikiLoops(answer, nLoop-1, nDrift)
    elif nLoop>1:#Go on from last drift. Transition sentence? >
        answer, drift, ifadded=wikiLoops(answer, nLoop-1, nDrift) #wikiLoops(drift, nLoop-1, nDrift)
    return answer, drift, ifadded


def saveGraph():
    # Save selfGraph into file selfgraph.txt. Print number vertices
    with open('./chris/data/selfgraph.txt', 'w') as outfile:
        json.dump(selfGraph, outfile)
        nN=len(selfGraph.keys())
        print("Self has " + str(nN) + " nodes.")

question="Christopher, tell me about acid rain."

def oneCycle(question, nLoop,  nDrift):
    #(0) Ask Question. Add the part when this question is picked from audio
    print("Question:", question)
    #(1) Chris answer: No, for now, dont answer. (?)
    #answer = askChris(question)
    #print("Answer", answer)
    #(2) Wikipedia Loops involving Wikipedia look at, self quest (update self graph), walk on the network and ML Drifts
    blabla=wikiLoops(question, nLoop, nDrift)
    #(3) Save and Visualize new self Graph
    saveGraph()
    vis.drawGraph()
    return blabla


##Acid Loops over Wikipedia Loops
def acidLoops(question="Christopher, tell me about acid rain.", nLoop=2, nDrift=2):
    #(0) Ask Question
    print("Question:", question)
    #(1) Chris answer
    answer = askChris(question)
    print("Answer", answer)
    #(2) ML Drifts with GPT2
    #First take seed for ML Drift. For now, last sentence. Could modify.>>
    #newSeed=seed.generate(answer)
    seeds=re.split('[?.!]', answer)
    #TAKE FULL answer as seed or  seeds[0] ?
    print("Seed:", seeds[0])
    client.emit(Message('speak', data={'utterance': seeds[0]})) #or all answer ?
    blabla=MLDrifts(seed, nDrift)
    #(3) Wikipedia Loops involving Wikipedia, ML Drifts and self quest
    blabla=wikiLoops(blabla, nLoop, nDrift)
    return blabla


#GRAMMAR To Implement grammar check?
def makeSense(blabla):
    okGrammar=True
    #https://pypi.org/project/grammar-check/ pip install grammar-check>>>>>>
    return okGrammar

#To Clean output of ML Drift.
def cleanText(blabla):
    sentences=rawChris.splitlines()
    # sentences= sentences= rawChris.splitlines()
    blabli=""
#    fuckedUp=0
#    ok=0
    for sentence in sentences:
        if sentence.endswith('?') or sentence.endswith('.') or sentence.endswith('!'):
            nonLett=nonLetters(sentence) #ration non letter elements
            if nonLett<0.3 and makeSense:   #Test if not to many symbol and grammar ok
                blabli+=sentence
#                ok+=1
#        elif not sentence=="":
#            fuckedUp+=1 #Count how many fuckedUp Lines, again ratio Then compared to other lines kept (non empty lines)
#    if ok>0:
#        fuckedUp/=ok
#    else:
#        fuckedUp=1
    fuckedUp = (len(blabli) + len(blabla))/len(blabla)
    return blabli, fuckedUp

#Compute semantic similarity score between 2 words.
#Could Try other possibilities for semabtic sim
def semanticSimilarity(word1, word2):
    #Test with this wns similarity, uncomment>. Beware then, score like 0.03 so adjust threshold
    #If word1 cmposed word: average similarity of its both elements.
    score=0
    splitWord=word1.split()
    if len(splitWord)>1:
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



#One cycle
if __name__ == '__main__':
    fire.Fire(oneCycle)
    #fire.Fire(acidLoops)
