

# !/usr/local/bin/python3
# -*- coding: utf-8 -*-

######Description############
#
# Behind the scene of some procedures related to Self Quest
#
#***********************************************************************PARAMETERS***************************************************************************

global INITIAL_WEIGHT # Starting weights for every node of the graph. Between 0 and 1
INITIAL_WEIGHT=0.5
#***********************************************************************INITIALIZATION***************************************************************************

###IMPORT general
import numpy as np
import json
import re
import random
import string
import time
import operator
import urllib.request as ur
#To visualize graph
import networkx as nx #networkx need install the library: pip install networkx
import matplotlib.pylab as plot
from networkx.drawing.nx_agraph import graphviz_layout, to_agraph
import pygraphviz as pgv
from PIL import Image
#For semantic similarity
from sematch.semantic.similarity import WordNetSimilarity
wns = WordNetSimilarity()
#For NLP and Wikipedia
import nltk
from nltk import word_tokenize, sent_tokenize, pos_tag
from nltk.corpus import words, wordnet
from nltk.stem.wordnet import WordNetLemmatizer
nltk.download('wordnet')#first_time only
nltk.download('wordnet_ic')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
lemmatizer = WordNetLemmatizer()
import wikipediaapi
wikipedia = wikipediaapi.Wikipedia('en')

#TODO: CLEAN THIS CODE

#***********************************************************************PROCEDURES for FILTERING**************************************************************************


def crop_unfinished_sentence(text):
    """
    Remove last unfinished bit from text. 
    """
    #SELECT FROM THE RIGHT rindex s[s.rindex('-')+1:]  
    stuff= re.split(r'(?<=[^A-Z].[.!?]) +(?=[A-Z])', text)

    new_text=""
    for i in range(len(stuff)):
        if i<len(stuff)-1:
            new_text+= " " + stuff[i]
        elif stuff[i][-1] in [".", ":", "?", "!", ";"]:#only if last character ounctuation keep
            new_text+= " " + stuff[i]

    return new_text



#***********************************************************************PROCEDURES for wikipedia SearchH***************************************************************************


def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)

def disambiguationPage(word):
    """
        Check if a word is a disambiguation Pge on wikipedia
    """
    page=wikipedia.page(word)
    categories=page.categories
    disambPage=False
    for title in categories.keys():#dictionary
        if title=="Category:Disambiguation pages":
            disambPage=True
    #print(str(page) + " is a disambiguation Page on Wikipedia: " + str(disambPage))
    return disambPage

excluded=['a', 'the', 'an', 'I', 'to', 'are', 'not', 'for', 'best','you', 'they', 'she', 'he', 'if', 'me', 'on', 'is', 'are', 'them', 'why', 'per', 'out', 'with', 'by'] #exclude these words to be looked upon

def extractWiki(blabla, self_graph, memory,  max_pick_word):
    """
        Extract wikipediable words from a blabla, which are not on the memory, nor on the selGraph, nor in excluded
        Self Quest bounded to a maximum of max_pick_word to avoid too long wait. Beware, of found wikipediable word!
        Beware of upper or lower letters which can create conflicts.
        #TODO: CLEANER PROCEDURE
       
    """
    OKWikipedia=[]
    
    if len(blabla)==0: #empty
        print("No new words to grow from.")
        return OKWikipedia, self_graph
    else:
        counter=0#count words added
        for word, pos in nltk.pos_tag(word_tokenize(blabla)):
            if counter<max_pick_word:#Stop once has enough words
                if not word.isupper():#To avoid turning words like AI lower case. Else turn to lower case. Ex: donald_trump
                    word=word.lower()
                #Below, keep mostly noun words. Could also take verbs (VBP) and other type if want.
                if not word is None and len(word)>1 and not hasNumbers(word) and (pos in ['NN', 'NNS','NNP']):
                    pos2=[]
                    word=lemmatizer.lemmatize(word) #Does it even for NNP ?? What will happen? #word=wordnet.morphy(word)
                    for tmp in wordnet.synsets(word): #Take all tags corresponding to exactly the name
                        if tmp.name().split('.')[0] == word:
                            pos2.append(tmp.pos())
                    if wikipedia.page(word).exists() and (pos == 'NNP' or (len(pos2)>0 and pos2[0]=='n')) and not (word in OKWikipedia) and not word.lower() in memory and not disambiguationPage(word):#up to capital:
                        if word in self_graph.keys():#Word is there, augment its weight.
                            self_graph[word][0]=self_graph[word][0]*1.1
                        elif word.lower() in self_graph.keys():
                            self_graph[word.lower()][0]=self_graph[word.lower()][0]*1.1
                        else: #Add word !
                            OKWikipedia.append(word)
                            counter+=1
        #Spacial case of duo words for wikipedia, such as global_warming https://en.wikipedia.org/wiki/Global_warming
        wordList=blabla.split()
        counter=0
        for i, word in enumerate(wordList):
            if counter<max_pick_word:#Stop once has enough words
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
                        if duo in self_graph.keys():
                            self_graph[duo][0]=self_graph[duo][0]*1.1
                        elif duo.lower() in self_graph.keys():
                            self_graph[duo.lower()][0]=self_graph[duo.lower()][0]*1.1
                        else:
                            OKWikipedia.append(duo)
                            counter+=1
        #print("New words to learn from", OKWikipedia)
        return OKWikipedia, self_graph


def extractWordnet(blabla, self_graph, memory,  max_pick_word):
    """
        Extract wordnet words from a blabla, which are not on the memory, nor on the selGraph, nor in excluded
        TAKE ALSO WIKIPEDIA STILL
        Self Quest bounded to a maximum of max_pick_word to avoid too long wait. Beware, of found wikipediable word!
        Beware of upper or lower letters which can create conflicts.
        #TODO: CLEANER PROCEDURE
       
    """
    OKWordnet=[]
    wn_lemmas = set(wordnet.all_lemma_names())#TODO: SHALL LOAD IT ONLY ONCE???
    if len(blabla)==0: #empty
        print("No new words to grow from.")
        return OKWordnet, self_graph
    else:
        counter=0#count words added
        for word, pos in nltk.pos_tag(word_tokenize(blabla)):
            if counter<max_pick_word:#Stop once has enough words
                if not word.isupper():#To avoid turning words like AI lower case. Else turn to lower case. Ex: donald_trump
                    word=word.lower()
                #Below, keep mostly noun words. Could also take verbs (VBP) and other type if want.
                if not word is None and len(word)>1 and not hasNumbers(word) and (pos in ['NN', 'NNS','NNP']):
                    pos2=[]
                    word=lemmatizer.lemmatize(word) #Does it even for NNP ?? What will happen? #word=wordnet.morphy(word)
                    for tmp in wordnet.synsets(word): #Take all tags corresponding to exactly the name
                        if tmp.name().split('.')[0] == word:
                            pos2.append(tmp.pos())
                    if ((word in wn_lemmas) or (wikipedia.page(word).exists())) and (pos == 'NNP' or (len(pos2)>0 and pos2[0]=='n')) and not (word in OKWordnet) and not word.lower() in memory and not disambiguationPage(word):#up to capital:
                        if word in self_graph.keys():#Word is there, augment its weight.
                            self_graph[word][0]=self_graph[word][0]*1.1
                        elif word.lower() in self_graph.keys():
                            self_graph[word.lower()][0]=self_graph[word.lower()][0]*1.1
                        else: #Add word !
                            OKWordnet.append(word)
                            counter+=1
        #Spacial case of duo words for wikipedia, such as global_warming https://en.wikipedia.org/wiki/Global_warming
        wordList=blabla.split()
        counter=0
        for i, word in enumerate(wordList):
            if counter<max_pick_word:#Stop once has enough words
                word= word.strip(string.punctuation)
                if not word.isupper(): #lower letter unless fully upper letter
                    word=word.lower() #Could also lemmatize.
                if i<len(wordList)-1:
                    nextword=wordList[i+1]
                    nextword=nextword.strip(string.punctuation)
                    if not nextword.isupper():  #lower letter unless fully upper letter
                        nextword=nextword.lower()
                    duo=word+" "+nextword
                    if len(word)>1 and len(nextword)>1 and word not in excluded and nextword not in excluded and not hasNumbers(word) and not hasNumbers(nextword) and ((word in wn_lemmas) or wikipedia.page(duo).exists()) and not (duo in OKWordnet) and not disambiguationPage(duo):
                        if duo in self_graph.keys():
                            self_graph[duo][0]=self_graph[duo][0]*1.1
                        elif duo.lower() in self_graph.keys():
                            self_graph[duo.lower()][0]=self_graph[duo.lower()][0]*1.1
                        else:
                            OKWordnet.append(duo)
                            counter+=1
        #print("New words to learn from", OKWikipedia)
        return OKWordnet, self_graph



#***********************************************************************PROCEDURES to INIT GRAPH***************************************************************************


def connectNodes(self_graph, threshold_similarity):
    """
       Build the Edges of a self_graph given
       Check if concepts in self_graph are related to each other.
       If similarity above a threshold, update the edges of the graph accordingly, return the number of edges.
    """
    #Edit: Can update as symmetric here run twice each edges. Return the number of added edges.
    nEdge=0
    for word1 in self_graph.keys():
        for word2 in self_graph.keys():
            if not word1==word2:
                similarity_score= semanticSimilarity(word1,word2)
                if similarity_score>threshold_similarity:
                    self_graph[word1][1][word2]=similarity_score #Add a connection if related enough.
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



def hatchSelf(max_pick_word, threshold_similarity):
    """
         Hatch (build) the self Graph from hatchVA.txt
    """
    # (0) Load the Initial list of words to hatch the VA self_graph: in hatcHVA.txt
    with open('./data/hatchVA.txt') as f:
        rawVA= ''.join(f.readlines())

    #(1) Extract wikipedia-ble words from these texts and put them in a waiting List, and start a self_graph which is a dictionnary in Python
    # For now, only with Wikipedia. Could add wiktionary.
    selfConcepts, voidGraph=extractWiki(rawVA, dict(), [], max_pick_word)
    #Record this in a text file
    fileW = open("./data/wiki.txt","w")
    #print('writing wiki files')
    fileW.writelines(elt + "\n" for elt in selfConcepts)
    fileW.close()

    #(2) Initialize the self_graph
    ### self_graph is a dictionnary, whose keys are concepts, and values are WEIGHT, NEIGHBOURS.
    ## Neighbors is a dictionnary whose keys are related, concepts and values are weights
    self_graph=dict.fromkeys(selfConcepts)
    # Each node is initialised with weight INITIAL_WEIGHT. This weight can evolve later (increase, though always between 0 and 1)
    for key in self_graph.keys(): #[weight, neighbors]
        self_graph[key]= [INITIAL_WEIGHT, dict()]

    nNode=len(list(self_graph.keys()))
    print("Self is Born. It is not yet associative.")
    print("Initial Concepts within Self:" + ', '.join(selfConcepts))

    ##(3) Build the connections within the Self: the edges of the Graph, from semantic similarity.
    #This step may take time, according the length of the list.
    nEdge=connectNodes(self_graph, threshold_similarity)

    #(4) Save it, in both selfbirth.txt and selfgraph.txtm to keep always initial graph in memory.
    with open('./data/selfbirth.txt', 'w') as outfile:
        json.dump(self_graph, outfile)
    with open('./data/selfgraph.txt', 'w') as outfile:
        json.dump(self_graph, outfile)

   #(5) init Memory as the list of keys. With as first element an index to keep track to where we are writing in the memory.
   #As the memory will be bounded
    memory=list(self_graph.keys()) #The memory of the VA is the words it has looked for on wikipedia.
    wo=memory[0]#To remember where is oldest word
    memory[0] = str(len(memory))
    memory.append(wo)

    mesh=(nEdge-nNode+1) / (2*nNode-5)
    description="Self is born. Self is a network with {} concepts and {} connections. My meshedness coefficient is {} .".format(nNode, nEdge, round(mesh,3))

    return self_graph, memory, description

#***********************************************************************PROCEDURES to LOAD SELF***************************************************************************


def loadSelf(first_run, max_pick_word, threshold_similarity):
    """
        The VA loads his self_graph, memory, lifetime, as last saved. Or build it if first time.
    """
    if first_run:
        print("Hatching self in process...")
        self_graph, memory, description=hatchSelf(max_pick_word, threshold_similarity)
        self_data=dict()
        self_data["lifetime"],self_data["memory"]=0, memory
    else:
        with open('./data/selfgraph.txt', 'r') as json_file:
            self_graph = json.load(json_file)
        with open('./data/selfdata.txt', "r") as json_file:
            self_data=json.load(json_file)
        print("I am here. My lifetime is {} interactions".format(str(self_data["lifetime"])))

    return self_graph, self_data


#***********************************************************************PROCEDURES to GROW SELF***************************************************************************


def isSelf(self_graph, word, n_sim_concept, threshold_similarity):
    """
    Check if a word (not belonging to his self) is related to his self_graph.
    And pick a similar concept (any above the threshold of similarity).
    """
    nSelf=len(list(self_graph.keys()))
    #CASE in case graph becomes too big:
    indices=random.sample(range(0, nSelf), min(n_sim_concept, nSelf)) #Generate random list of indices where will look for
    self_graph[word]=[0,dict()]   #Add entry to dictionary for now
    ifConnected=False
    maxSim=0
    possible_simWord=[]
    simWord=""
    #Check similarity with other concepts in Self
    for i, wordSelf in enumerate(list(self_graph.keys())):
        if i in indices:
            similarity_score= semanticSimilarity(word,wordSelf)
            if similarity_score>threshold_similarity:
                possible_simWord.append(wordSelf)
                self_graph[word][1][wordSelf]=similarity_score#Add a connection if related enough.
                self_graph[wordSelf][1][word]=similarity_score#Symmetric
                ifConnected=True
                #if similarity_score>maxSim:#IF WANT MAX SIMILARITY
                #    maxSim=similarity_score
                #    simWord=wordSelf
    
    #Conclude if related
    if not ifConnected: #Not related, ie no connection with SelfConcept was above a fixed threshold.
        del self_graph[word] #delete entry from SelfGraph therefore
    else: # if related
        #Pick a word above threshold similarity:
        simWord=random.choice(possible_simWord)
        self_graph[word][0]=maxSim*self_graph[simWord][0] #adjust the weight of the node
    return self_graph, ifConnected, simWord


#***********************************************************************PROCEDURES to VISUALIZE GRAPH***************************************************************************


def createGraph(self_graph):
    """
        Create graph, network entity with networkx library from self_graph (a dictionnary).
        Then look at his attributes, from a point of view of network theory
    """
    #(0) Create network (empty)
    G = nx.Graph()

    #(1) Add Nodes
    G.add_nodes_from(list(self_graph.keys()))

    #(2)) Add edges with weight specified directly
    #First, build edge set:
    edgesList=[]
    for node1 in self_graph.keys():
        for node2 in self_graph[node1][1]:
            weight12=self_graph[node1][1][node2]#weight of the edge, relatedness of 2 nodes
            if not [node2, node1, weight12] in edgesList: #as symmetric edges
                edgesList.append([node1, node2, weight12])
    G.add_weighted_edges_from(edgesList)    #G.add_edges_from()   #G.add_edge(2, 3, weight=0.9)

    #(3) Add Attributes Nodes:  attribute data to be in the form dictionary: keys: nodes name, values: attributes.
    #NB: can have different type attributes: nx.set_node_attributes(G, att_dic, 'name_att')
    weightNode={w: self_graph[w][0] for w in self_graph.keys()}
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
    A.draw('./data/self_graph.png')
    #Show Image
    img=Image.open('./data/self_graph.png')
    img.show()
