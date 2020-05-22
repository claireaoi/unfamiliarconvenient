#To initialize self Graph

#***********************************************************************INITIALIZATION***************************************************************************

import numpy as np
import wiki
import json

from sematch.semantic.similarity import WordNetSimilarity


#######PARAMETERS:
# Should tune parameters according to our experiments. or event vary them, or make them probabilistic (some of them).
global startingWeight
startingWeight=0.5
global thresholdSim
thresholdSim=0.6 # threshold when to consider 2 concepts as similar
global nSearch
nSearch=50

global wns
wns = WordNetSimilarity()

global memory
memory=[]


#***********************************************************************PROCEDURES****************************************************************************

def connectNodes():
    # Check if concepts in selfGraph are related to each other.
    # If similarity goes above the threshold, update the edges of the graph accordingly in selfGraph. Return the number of edges.
    # Return the number of added edges.

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


    nEdge=0
    for word1 in selfGraph.keys():
        for word2 in selfGraph.keys():
            if not word1==word2:
                simScore=semanticSimilarity(word1,word2)
                if simScore>thresholdSim:
                    selfGraph[word1][1][word2]=simScore #Add a connection if related enough.
                    nEdge+=1
    nEdge/2 # as counted double edges
    return nEdge


#***********************************************************************INIT Self GRAPH**************************************************************************

### STEP 1: Initial list of words to seed Chris Self Graph
# They are written on the file wiki.txt
# (0) Read starting text corresponding to Chris and Roomba.
print('Opening Hatch File')
with open('../data/hatchVA.txt') as f:
   rawChris= ''.join(f.readlines()) #Text with list words
#(1) Extract wikipedia-ble words from these texts and put them in a waiting List, and start a selfGraph which is a dictionnary in Python
# For now, only with Wikipedia. Could add wiktionary and DuckDuck Go >
chrisWikipedia,chrisWiktionary,VoidGraph=wiki.extract(rawChris, dict(), memory, nSearch)
#Record this in a text file
fileW = open("../data/wiki.txt","w")
print('writing wiki files')
fileW.writelines(elt + "\n" for elt in chrisWikipedia)
fileW.close()

### STEP 2: Initialize the selfGraph
### selfGraph is a dictionnary, whose keys are concepts, and values are WEIGHT, NEIGHBOURS.
## Neighbors is a dictionnary whose keys are related, concepts and values are weights
waitingList= [line.rstrip() for line in open("../data/wiki.txt")] #Text with list of initial words

global selfGraph
selfGraph=dict.fromkeys(waitingList)

# Init graph: each node is initialised with weight startingWeight=0.5. This weight can evolve (increase, though always between 0 and 1)
for key in selfGraph.keys(): #[weight, neighbors]
    selfGraph[key]= [startingWeight, dict()]

nNode=len(selfGraph.keys())
print("Self is Born. It is not yet associative.")
print("Initial Concepts within Self:", waitingList)


#***********************************************************************BUILD Connection Self GRAPH**************************************************************************



##STEP 3: Build the connections in the selfGraph
#Try to see if concepts are related. This step may take time, according the length of the list.
nEdge=connectNodes()
mesh=(nEdge-nNode+1) / (2*nNode-5)

print("Self is now a Graph!")
print("My Meshedness coefficient is:", round(mesh,3))

#STEP 4: SAVE it in a file selfbirth.txt.
with open('../data/selfbirth.txt', 'w') as outfile:
    json.dump(selfGraph, outfile)
