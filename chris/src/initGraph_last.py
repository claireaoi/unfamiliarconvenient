
#To initialize self Graph

#***********************************************************************INITIALIZATION***************************************************************************

#######PARAMETERS:
# Should tune parameters according to our experiments. or event vary them, or make them probabilistic (some of them).
startingWeight=0.5
thresholdSim=0.6 #threshold when Consider 2 concepts as similar
#######IMPORT
import numpy as np
import wiki
import json

from sematch.semantic.similarity import WordNetSimilarity
wns = WordNetSimilarity()
######INIT
memory=[]


#***********************************************************************INIT Self GRAPH**************************************************************************

### STEP 1: Initial list of words to seed Chris Self Graph
#Here, words are extracted from the Chris & roomba manuals. Could update this, and in this case relaunch the procedures
#They are written on the file wiki.txt
#(0) Read starting text corresponding to Chris and Roomba.
with open('./chris/data/chris.txt') as f:
   rawChris= ''.join(f.readlines()) #Text with list words
with open('./chris/data/roo.txt') as f:
   rawRoo= ''.join(f.readlines()) #Text with list words
#(1) Extract wikipedia-ble words from these texts and put them in a waiting List, and start a selfGraph which is a dictionnary in Python
#For now, only with Wikipedia. Could add wiktionary and DuckDuck Go >
chrisWikipedia,chrisWiktionary=wiki.extract(rawChris, dict(), memory, 50) #for initial graph look for a lot
rooWikipedia,rooWiktionary=wiki.extract(rawRoo, dict(), memory, 50)
waitingList = chrisWikipedia + list(set(rooWikipedia) - set(chrisWikipedia))  #Concatenate both without duplicate
#Record this in a text file
fileW = open("./chris/data/wiki.txt","w")
fileW.writelines(waitingList)
fileW.writelines("%s\n" % elt for elt in waitingList) #Ok different lines ?
fileW.writelines(elt + "\n" for elt in waitingList) #Ok different lines ? and this ?
fileW.close()


###STEP 2: Initialize the selfGraph
###selfGraph is a dictionnary, whose keys are concepts, and values are couple (weight, neighbors).
##Neighbors is a dictionnary whose keys are related concepts and values are weights
waitingList= [line.rstrip() for line in open('./chris/data/wiki.txt')] #Text with list of initial words
selfGraph=dict.fromkeys(waitingList)
#Init graph: each node is initialised with weight startingWeight=0.5. This weight can evolve (increase, though always between 0 and 1)
for key in selfGraph.keys(): #[weight, neighbors]
    selfGraph[key]= [startingWeight, dict()]

nNode=len(selfGraph.keys())
print("Self is Born. It is not yet associative.")
print("Initial Concepts within Self:", waitingList)

#***********************************************************************PROCEDURES****************************************************************************

def connectNodes():
    #Check if concepts in selfGraph are related to each other.
    #If similarity above a threshold, Update the edges of the graph accordingly in selfGraph. Return the number of edges.
    #Can update as symmetric here run twice each edges. Return the number of added edges.
    nEdge=0
    for word1 in selfGraph.keys():
        for word2 in selfGraph.keys():
            if not word1==word2:
                simScore= semanticSimilarity(word,word2)
                if simScore>thresholdSim:
                    selfGraph[word][1][word1]=simScore #Add a connection if related enough.
                    nEdge+=1
    nEdge/2#as counted double edges
    return nEdge


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


#***********************************************************************BUILD Connection Self GRAPH**************************************************************************



##STEP 3: Build the connections in the selfGraph
#Try to see if concepts are related. This step may take time, according the length of the list.
nEdge=connectNodes()
mesh=(nEdge-nNode+1) / (2*nNode-5)

print("Self is now a Graph!")
print("My Meshedness coefficient is:", round(mesh,3))
print("My Clustering coefficient is:")
print("My Algebraic Connectivity Coefficient is:")

#STEP 4: SAVE it in a file selfbirth.txt.
with open('./chris/data/selfbirth.txt', 'w') as outfile:
    json.dump(selfGraph, outfile)
