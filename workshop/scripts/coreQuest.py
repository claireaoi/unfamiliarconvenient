# !/usr/local/bin/python3
# -*- coding: utf-8 -*-


#***********************************************************************PARAMETERS***************************************************************************


###These parameters could be tuned possibly.
global startingWeight # Starting weights for every node of the graph. Between 0 and 1
startingWeight=0.5
global thresholdSim
thresholdSim=0.6 # threshold when to consider 2 concepts as similar

#***********************************************************************INITIALIZATION***************************************************************************

###IMPORT general
import numpy as np
import json
import fire
import re
import random
import string
import time
import operator
import urllib.request as ur

#To visualize graph
import networkx as nx #networkx need install the library: pip install networkx
import pylab as plt
from networkx.drawing.nx_agraph import graphviz_layout, to_agraph
import pygraphviz as pgv
from PIL import Image

#For semantic similarity
from sematch.semantic.similarity import WordNetSimilarity
wns = WordNetSimilarity()

#For NLP and Wikipedia
import nltk
from nltk import word_tokenize, sent_tokenize, pos_tag
from nltk.corpus import wordnet
from nltk.stem.wordnet import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()
import wikipediaapi
wikipedia = wikipediaapi.Wikipedia('en')

#***********************************************************************PROCEDURES for wikipedia SearchH***************************************************************************


def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)

def disambiguationPage(word):
    """
        Check if a word is a disambiguation Page on wikipedia
    """
    page=wikipedia.page(word)
    categories=page.categories
    disambPage=False
    for title in categories.keys():#dictionary
        if title=="Category:Disambiguation pages":
            disambPage=True
    print(str(page) + " is a disambiguation Page on Wikipedia: " + str(disambPage))
    return disambPage

excluded=['a', 'the', 'an', 'I', 'to', 'are', 'not', 'for', 'best','you', 'they', 'she', 'he', 'if', 'me', 'on', 'is', 'are', 'them', 'why', 'per', 'out', 'with', 'by'] #exclude these words to be looked upon

def extractWiki(blabla, selfGraph, memory,  nSearch):
    """
        Extract wikipediable words from a blabla, which are not on the memory, nor on the selGraph, nor in excluded
        Self Quest bounded to a maximum of nSearch to avoid too long wait. Beware, of found wikipediable word!
        Beware of upper or lower letters which can create conflicts.
    """
    OKWikipedia=[]
    if len(blabla)==0: #empty
        print("No new words to grow from.")
        return OKWikipedia, selfGraph
    else:
        counter=0#count words added
        print(blabla)
        print(word_tokenize(blabla))
        print(nltk.pos_tag(word_tokenize(blabla))))
        for word, pos in nltk.pos_tag(word_tokenize(blabla)):
            if counter<nSearch:#Stop once has enough words
                if not word.isupper():#To avoid turning words like AI lower case. Else turn to lower case. Ex: donald_trump 
                    word=word.lower()
                #Below, keep mostly noun words. Could also take verbs (VBP) and other type if want.
                if not word is None and len(word)>1 and not hasNumbers(word) and (pos == 'NN' or pos == 'NNS' or pos == 'NNP'):
                    pos2=[]
                    word=lemmatizer.lemmatize(word) #Does it even for NNP ?? What will happen? #word=wordnet.morphy(word)
                    for tmp in wordnet.synsets(word): #Take all tags corresponding to exactly the name
                        if tmp.name().split('.')[0] == word:
                            pos2.append(tmp.pos())
                    if wikipedia.page(word).exists() and (pos == 'NNP' or (len(pos2)>0 and pos2[0]=='n')) and not (word in OKWikipedia) and not word.lower() in memory and not disambiguationPage(word):#up to capital:
                        if word in selfGraph.keys():#Word is there, augment its weight.
                            selfGraph[word][0]=selfGraph[word][0]*1.1
                        elif word.lower() in selfGraph.keys():
                            selfGraph[word.lower()][0]=selfGraph[word.lower()][0]*1.1
                        else: #Add word !
                            OKWikipedia.append(word)
                            counter+=1
        #Spacial case of duo words for wikipedia, such as global_warming https://en.wikipedia.org/wiki/Global_warming
        wordList=blabla.split()
        counter=0
        for i, word in enumerate(wordList):
            if counter<nSearch:#Stop once has enough words
                word= word.strip(string.punctuation)
                if not word.isupper(): #lower letter unless fully upper letter
                    word=word.lower() #Could also lemmatize.
                if i<len(wordList)-1:
                    nextword=wordList[i+1]
                    nextword=nextword.strip(string.punctuation)
                    if not nextword.isupper():  #lower letter unless fully upper letter
                        nextword=nextword.lower()
                    duo=word+" "+nextword
                    if len(word)>1 and len(nextword)>1 and word not in excluded and nextword not in excluded and not hasNumbers(word) and not hasNumbers(nextword) and wikipedia.page(duo).exists() and not (duo in OKWikipedia) and not disambiguationPage(duo):
                        if duo in selfGraph.keys():
                            selfGraph[duo][0]=selfGraph[duo][0]*1.1
                        elif duo.lower() in selfGraph.keys():
                            selfGraph[duo.lower()][0]=selfGraph[duo.lower()][0]*1.1
                        else:
                            OKWikipedia.append(duo)
                            counter+=1
        print("New words to learn from", OKWipedia)
        return OKWikipedia, selfGraph


#***********************************************************************PROCEDURES to INIT GRAPH***************************************************************************


def connectNodes(selfGraph):
    """
       Build the Edges of a selfGraph given
       Check if concepts in selfGraph are related to each other. 
       If similarity above a threshold, update the edges of the graph accordingly, return the number of edges.
    """
    #Edit: Can update as symmetric here run twice each edges. Return the number of added edges.
    nEdge=0
    for word1 in selfGraph.keys():
        for word2 in selfGraph.keys():
            if not word1==word2:
                simScore= semanticSimilarity(word1,word2)
                if simScore>thresholdSim:
                    selfGraph[word1][1][word2]=simScore #Add a connection if related enough.
                    nEdge+=1
    nEdge/2  #Since has counted double edges
    return nEdge


def semanticSimilarity(word1, word2):
    """
       Compute the semantic similarity between two words, as define by the library wnsm, and return score. Of course this is subjective. If word1 cmposed word: average similarity of its both elements.
    """
    score=0
    splitWord=word1.split()
        #Case of concepts made of several words
    if len(splitWord)>1:
        for elt in splitWord:
            score+=semanticSimilarity(elt, word2)
        score/=len(splitWord)
    else:#word1 has 1 component
        splitWord2=word2.split()
        if len(splitWord2)>1:#case word2 has 2 component or more
            for elt in splitWord2:#Else could take the max but would be non symmetic
                score+=wns.word_similarity(word1, elt, 'li')
            score/=len(splitWord2)
        else:#case both concepts have only 1 word
            score=wns.word_similarity(word1, word2, 'li')
    print('Similarity score between ' + word1 + ' and ' + word2 , score)

    return score

def hatchSelf(nSearch):
    """
         Hatch (build) the self Graph from hatchVA.txt
    """
    # (0) Load the Initial list of words to hatch the VA selfGraph: in hatcHVA.txt
    with open('./workshop/data/hatchVA.txt') as f:
        rawVA= ''.join(f.readlines()) 

    #(1) Extract wikipedia-ble words from these texts and put them in a waiting List, and start a selfGraph which is a dictionnary in Python
    # For now, only with Wikipedia. Could add wiktionary.
    selfConcepts, voidGraph=extractWiki(rawVA, dict(), [], nSearch)
    #Record this in a text file
    fileW = open("./workshop/data/wiki.txt","w")
    print('writing wiki files')
    fileW.writelines(elt + "\n" for elt in selfConcepts)
    fileW.close()

    #(2) Initialize the selfGraph
    ### selfGraph is a dictionnary, whose keys are concepts, and values are WEIGHT, NEIGHBOURS.
    ## Neighbors is a dictionnary whose keys are related, concepts and values are weights
    selfGraph=dict.fromkeys(selfConcepts)
    # Each node is initialised with weight startingWeight. This weight can evolve later (increase, though always between 0 and 1)
    for key in selfGraph.keys(): #[weight, neighbors]
        selfGraph[key]= [startingWeight, dict()]

    nNode=len(list(selfGraph.keys()))
    print("Self is Born. It is not yet associative.")
    print("Initial Concepts within Self:" + ', '.join(selfConcepts))

    ##(3) Build the connections within the Self: the edges of the Graph, from semantic similarity.
    #This step may take time, according the length of the list.
    nEdge=connectNodes(selfGraph)
    
    #(4) Save it, in both selfbirth.txt and selfgraph.txtm to keep always initial graph in memory.
    with open('./workshop/data/selfbirth.txt', 'w') as outfile:
        json.dump(selfGraph, outfile)
    with open('./workshop/data/selfgraph.txt', 'w') as outfile:
        json.dump(selfGraph, outfile)

   #(5) init Memory as the list of keys. With as first element an index to keep track to where we are writing in the memory.
   #As the memory will be bounded
    wordsMemory=list(selfGraph.keys()) #The memory of the VA is the words it has looked for on wikipedia.
    wo=wordsMemory[0]#To remember where is oldest word
    wordsMemory[0] = str(len(wordsMemory))
    wordsMemory.append(wo)
    
    mesh=(nEdge-nNode+1) / (2*nNode-5)
    description="Self is born. Self is a network with {} concepts and {} connections. My meshedness coefficient is {} .".format(nNode, nEdge, round(mesh,3))

    return selfGraph, wordsMemory, description


#***********************************************************************PROCEDURES to GROW SELF***************************************************************************


def isSelf(selfGraph, word, nSimMax):
    #Check if a word (not belonging to his self) is related to his selfGraph.
    nSelf=len(list(selfGraph.keys()))
    indices=random.sample(range(0, nSelf), min(nSimMax, nSelf)) #Generate random list of indices where will look for
    selfGraph[word]=[0,dict()]   #Add entry to dictionary for now
    ifConnected=False
    maxSim=0
    simWord=""
    #Check similarity with other concepts in Self
    for i, wordSelf in enumerate(list(selfGraph.keys())):
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


#***********************************************************************PROCEDURES to VISUALIZE GRAPH***************************************************************************


def createGraph(selfGraph):
    """
        Create graph, network entity with networkx library from selfGraph (a dictionnary).
        Then look at his attributes, from a point of view of network theory
    """
    #(0) Create network (empty)
    G = nx.Graph()

    #(1) Add Nodes
    G.add_nodes_from(list(selfGraph.keys()))

    #(2)) Add edges with weight specified directly
    #First, build edge set:
    edgesList=[]
    for node1 in selfGraph.keys():
        for node2 in selfGraph[node1][1]:
            weight12=selfGraph[node1][1][node2]#weight of the edge, relatedness of 2 nodes
            if not [node2, node1, weight12] in edgesList: #as symmetric edges
                edgesList.append([node1, node2, weight12])
    G.add_weighted_edges_from(edgesList)    #G.add_edges_from()   #G.add_edge(2, 3, weight=0.9)

    #(3) Add Attributes Nodes:  attribute data to be in the form dictionary: keys: nodes name, values: attributes.
    #NB: can have different type attributes: nx.set_node_attributes(G, att_dic, 'name_att')
    weightNode={w: selfGraph[w][0] for w in selfGraph.keys()}
    nx.set_node_attributes(G, weightNode, 'relevancy')   #To access them: G.nodes[node]['relevancy']

    #(4) Add Attributes Edges. Dont need for now, as already added the weight in the edges. But could add other attributes here.
    #nx.set_edge_attributes(G, weightEdge, 'relatedness')

    #(5) Look at properties related to self Graph
    descriptionSelf=nx.info(G) + "\n" 
    descriptionSelf+='Density of Self: {}'.format(nx.density(G)) + "\n" 
    descriptionSelf+='Am I connected Connected? '+ str(nx.is_connected(G)) + "\n" 
    components = nx.connected_components(G)
    descriptionSelf+='I have {} connected components'.format(nx.number_connected_components(G)) + "\n" 
    largest_component = max(components, key=len)
    subSelf = G.subgraph(largest_component) # Create a "subgraph" of just the largest component
    diameter = nx.diameter(subSelf)
    descriptionSelf+='The diameter of my largest Connected Component is:'+ str(diameter)  + "\n" 
    #Transitivity, like density, expresses how interconnected a graph is in terms of a ratio of actual over possible connections. 
    #Transitivity is the ratio of all triangles over all possible triangles. 
    descriptionSelf+="My transitivity coefficient is"+ str(nx.transitivity(G))  + "\n" 
    #Centrality node: Find which nodes are the most important ones in your network.
    degree_dict = dict(G.degree(G.nodes())) #degree is connectivity of each node: how many egde
    nx.set_node_attributes(G, degree_dict, 'degree') #First add degree each nodes as extra attribute
    sorted_degree = sorted(degree_dict.items(), key=operator.itemgetter(1), reverse=True) #sort this degree list
    descriptionSelf+= "The three bigger hubs in me are: " + ', '.join(sorted_degree[:3]) + "\n" 
    #Other centralities than just hubs:
    #EIgenvector Centrality is a kind of extension of degree—it looks at a combination of a node’s edges and the edges of that node’s neighbors. 
    #Eigenvector centrality cares if you are a hub, but it also cares how many hubs you are connected to. Like second order connectivity
    #Betweenness centrality looks at all the shortest paths that pass through a particular node (see above).
    betweenness_dict = nx.betweenness_centrality(G)
    eigenvector_dict = nx.eigenvector_centrality(G)
    nx.set_node_attributes(G, betweenness_dict, 'betweenness')     # Assign each to an attribute in your network
    nx.set_node_attributes(G, eigenvector_dict, 'eigenvector')
    sorted_betweenness = sorted(betweenness_dict.items(), key=operator.itemgetter(1), reverse=True)
    descriptionSelf+="Three most central concepts in me are:"+ ' , '.join(sorted_betweenness[:3])+ "\n" 
    #Could add other properties>>>
    #Community detection within Self: with modularity, different clusterm Clustered Self etc. >>>
    print(descriptionSelf)

    return G, descriptionSelf

def drawGraph(G):
    """
        Draw the Graph, display and save it.
    """
    #Conversion to be readable by graphviz #agraph is Interface to pygraphviz AGraph class.
    A = to_agraph(G) #agraph is Interface to pygraphviz AGraph class.
    #Rendering via Graphviz. >>Draw Attributes!
    A.layout('dot')
    #Saving
    A.draw('./workshop/data/selfGraph.png')
    #Show Image
    img=Image.open('./workshop/data/selfGraph.png')
    img.show()



