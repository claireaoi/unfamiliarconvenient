
import json
import math
import numpy as np
import random
import matplotlib.pyplot as plt
from string import punctuation
import re
from sklearn.manifold import TSNE
import seaborn as sns
import pandas as pd

# =============================================================================
########### INIT PROCEDURES
# =============================================================================

def approximately_colinear(p1,p2,p3, threshold=0.05):
    """
        Determine if 3 points approximately colinear. Here, look if angle between 2 vectors small enough
        #TODO: More efficient way? 
        Inputs: 
            p1,p2,p3: 2D points
        Output: boolean
    """
    #--define 2 vectors from these 3 points
    vector_1=[p2[0]-p1[0], p2[1]-p1[1]]
    vector_2=[p3[0]-p1[0], p3[1]-p1[1]]
    #--compute angle between 2 vectors
    unit_vector_1 = vector_1 / np.linalg.norm(vector_1)
    unit_vector_2 = vector_2 / np.linalg.norm(vector_2)
    dot_product = np.dot(unit_vector_1, unit_vector_2)
    angle = np.arccos(dot_product)
    #if colinear
    colinear= angle < threshold
    return colinear


def nearest_concept(points, ref):
    """
        Find nearest point from a list to a point
        Inputs:
            points: list of point
            ref: one point compare to
        Outputs:
            idx: index of this point in points
            dist[idx]: distance of this point to ref
    """
    dist=[np.linalg.norm(point - ref) for point in points]
    idx = np.argmin(dist)
    return idx, dist[idx]

# def load_data_json(filename, folderpath):
#     """
#     Load json data
#     """
#     folderpath="/home/unfamiliarconvenient/.mycroft/fallback-associative/"
#     with open(filepath+filename) as json_file:
#         data = json.load(json_file)
#     return data


def initialize(filenames, graph_path, words_path):
    """ """

    #load self self_graph
    with open(graph_path) as json_file:
        self_graph = json.load(json_file)

    #load dictionary
    wordsDic={}
    for filename in filenames:
        wordsDic[filename] = [line.rstrip('\n') for line in open(words_path+filename+'.txt')]
    
    #load structures
    with open(words_path+'haiku.txt', "r") as f:
        structures  = f.read().split(">>>") #LIST for each Haiku

    return self_graph, wordsDic, structures
# =============================================================================
########### EMBEDDINGS PROCEDURES
# =============================================================================


def tsne_embedding(points):
    """
    Projection of a list of points in high dimensional space into 2D
    Inputs:
        points: list of points in High Dimensional space (as numpy array or tensors?)
    Output:
        embeddings: 2D embeddings of each of these points, after a tSNE projection (or other dimensionality reduction technique )
    """
    num_points=len(points)
    array=np.array(points)
    
    #---1 compute 2D embeddings with TSNE
    embeddings_2D=TSNE(n_components=2).fit_transform(array)
    #NOTE: may tweak param such as perplexity, early_exaggeration, learning_rate etc, https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html
    #NOTE: This is trajectory of point between -1 and 1, else as to change normalization other points...
    print(np.max(np.abs(embeddings_2D)))
    embeddings_2D= embeddings_2D/np.max(embeddings_2D, axis=0)#TODO this currently place them often on cirlce>>change!
    print(embeddings_2D)
    return embeddings_2D

def get_words_embeddings(concepts):
    #TODO: from gpt2 vocabulary but then from own model vocabulary !
    words_embeddings={}
    for concept in concepts:
        words_embeddings[concept]=np.random.rand((50)) #temporary

    return words_embeddings

def self_graph_embeddings(self_graph):
    """
    Project the concepts of the self graph, once retrieved the embeddings vectors used for gpt2
    Input:
        words_embeddings: dictionary of words & vectors in high dimension 
    Outputs:
        concepts: list of keys of the graph
        embeddings: 2D embeddings of each of concepts in self concept
    """
    print("***compute self_graph_embeddings**")
    
    # -1--get concepts in self
    concepts=self_graph.keys()    
    num_concepts=len(concepts)

    #-2--retrieve gpt2 words embeddings attached to these concepts
    words_embeddings=get_words_embeddings(concepts)
    concepts_vectors=list(words_embeddings.values())

    #-3---turn these vectors into a 2D embedding
    embeddings2D=tsne_embedding(concepts_vectors)
    
    #-4---rescale between max and min values
    #TODO: this depending size room or about depends scale use for other
    MAX=20
    scaled_embeddings2D=np.interp(embeddings2D, (embeddings2D.min(), embeddings2D.max()), (-MAX, MAX))
    
    #-5--- Visualize it
    data = pd.DataFrame(scaled_embeddings2D, columns=["x", "y"])# columns = concepts)
    sns.set_context("notebook", font_scale=1.1)
    sns.set_style("ticks")
    #sns.color_palette("hls", 8) #TODO: color palette need column...
    #each column is a variable and each row is an observation.
    sns.lmplot(x="x", y="y", palette=sns.color_palette("pastel", n_colors=num_concepts), data=data, truncate=False).set(xlim=(-MAX-2, MAX+2), ylim=(-MAX-2, MAX+2))
    #x,y should be column name in data
    plt.title('Self 2D Embeddings',weight='bold').set_fontsize('14')
    plt.show()

    return concepts, scaled_embeddings2D


# =============================================================================
########### HAIKU PROCEDURES
# =============================================================================

def pick_structure(structures):
    structure_=random.choice(structures)
    structure=structure_.split("\n\n")
    final_structure=[]
    for el in structure:
        lines=el.split("\n")
        line=random.choice(lines)
        final_structure.append(line)

    return final_structure

def read(line, seeds=[], dico=None):
    sentence=""
    things=line.split(" ")
    for thg in things:
        elements=thg.split("//")#// means an or
        element=random.choice(elements)
        units=element.split("/")#/ means an AND
        for unit in units:
            bla, seeds=readUnit(unit.strip(), seeds=seeds, dico=dico)
            sentence+=" "+ bla.strip()#Strip to remove if spaces
    return sentence, seeds

def readUnit(unit, seeds=[], dico=None):
    #-----may use seeds----
    if unit in ["N","N2", "Ns", "N2s", "Na"]:
        if len(seeds)>0:
            bla=seeds[0]
            seeds.pop(0)
        else:
            bla, w=read(random.choice(dico[unit.replace("s","")]))
    #---------composite structures
    elif unit=="N2p" or unit=="Np":#Here dont caree about plural !
        bla, seeds=read("N//Na//Pf/Na", seeds=seeds, dico=dico)
    elif unit=="X" or unit=="Xs" or unit=="Xp":
        bla, seeds=read("Duo//Duoa//N//Na//Na/N2//N/and/N//N2/P0/N//Pf/Na//Na/P0/N//A/A/N//A/N//Ns/N2//N2//N//A/N//Ns/N2//N2//N//A/N//Ns/N2//N//A/N//Ns/N2//N//A/N//Ns/N2//N//A/N//Ns/N2//N//A/N//Ns/N2//N//A/N//Ns/N2//N//A/N//Ns/N2//A/N2//A/N2//A/N2", seeds=seeds, dico=dico)
    elif unit=="X+":#to add to "the X ""...Ex: which...
        bla, seeds=read("whose/Na/W0//which/W//better/Vtd/that/W0//than/Vtd//which/have/been/PR1a//which/have/been/PR1//which/W0//the/X/PR1//thought/as/Nfa//we/are/trying/to/Vt//that/W0//that/we/allow/to/W0//we/are/Vtg//that/Ad2/W0//that/V+//that/have/become/A//that/do/not/W0//that/you/should/not/Vt", seeds=seeds, dico=dico)
    elif unit=="Y":
        bla, seeds=read("Y0//Y0//Y0//Y0//Y0/PR1//Y0/PR1a//all/what/W//the/X/X+//everyone/X+//anything/X+//each/X/X+//X/Wg", seeds=seeds, dico=dico)
    elif unit=="Y0":
        bla, seeds=read("Nf//Nfa//Nf//Nfa//Nfa//Nfa//the/A/N//the/Na/P/N//the/Na/P/X//the/Ns/N2//the/A/Ns/N2//the/X/P/X//the/X/P0/X//the/Vg/X//X/,/X/and/X//both/X/and/X//the/X/that/W0", seeds=seeds, dico=dico)
    elif unit=="W":
        bla, seeds=read("W0//W0//W0//W0//W0//V+//V+//V+//could/W0//should/W0//would/W0//could/V+//Ad2/W0//Ad2/W0", seeds=seeds, dico=dico)
    elif unit=="W0":
        bla, seeds=read("V//V//Vt/X//Va//Va//V2//Vt/Y//Vt/Nfa", seeds=seeds, dico=dico)
    elif unit=="WA":
        bla, seeds=read("Ad2/V//Ad2/Vt/X//V/Ad3//Vt/X/Ad3", seeds=seeds, dico=dico)
    elif unit=="Wd":
        bla, seeds=read("Vd//Vd//Vtd/X//Vad//Vad//V2d//Vtd/Y//Vtd/Nfa", seeds=seeds, dico=dico)
    elif unit=="Wg":
        bla, seeds=read("Vg//Vg//Vtg/X//Vag//Vag//V2g//Vtg/Y//Vtg/Nfa", seeds=seeds, dico=dico)
    elif unit=="XWg":#NEED ?
        bla, seeds=read("X/Wg", seeds=seeds, dico=dico)
    elif unit=="PRO":
        bla, seeds=read("S/V//S/Vt/X//X/V//N/Vt/X//S/V/P0/X", seeds=seeds, dico=dico)

    #---not affecting seeds
    elif unit=="A":
        bla, w=read("A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0/A0//A0/A0//A0/A0/A0//Ad2/A0//A0//Ad2/A0//Ad2/A0//A0/A0//still/A0//A0/yet/A0//yet/A0//soon/A0//somehow/A0//already/A0", dico=dico)
    elif unit=="A0":
        bla, w=read(random.choice(dico["A"]), dico=dico)
    elif unit=="PR10":
        bla, w=read(random.choice(dico["PR1"]), dico=dico)
    elif unit=="PR1":
        bla, w=read("PR10//PR10//PR10//PR10//PR10//PR10//Ad1/PR10//Ad2/PR10//Ad2/PR10", dico=dico)
    #--------verbs
    elif unit=="Vd" or unit=="Vad" or unit=="Vtd" or unit=="V2d":
        verb=random.choice(dico[unit.replace("d", "")]).split(" ")
        bla=verb
        #TODO: This library need Python3.6 or 2.7... find replacement...
        # bla=lexeme(verb[0])[4] #past
        # if len(verb)>0:
        #     bla+=' '.join(verb[1:])
    elif unit=="Vag" or unit=="Vg" or unit=="Vtg" or  unit=="V2g":
        verb=random.choice(dico[unit.replace("g", "")]).split(" ")
        bla=verb
        #TODO: This library need Python3.6 or 2.7...
        ## bla=lexeme(verb[0])[2] #present participe
        # #conjugate(verb[0], tense = "present",  person = 3,  number = "singular",  mood = "indicative", aspect = "progressive",negated = False)
        # if len(verb)>0:
        #     bla+=' '.join(verb[1:])
    #----remaining stuff
    elif unit in dico.keys():
        bla, w=read(random.choice(dico[unit]), dico=dico)

    else:#mean just a word
        bla=unit

    return bla, seeds


def generate_haiku(words, structures, dico):

    """
    Args: 3 words with which to generate an haiku

    """

    #--chose a structure for the Haiku
    structure = pick_structure(structures)
    print("Picked a structure", structure)

    #--generate Haiku
    haiku=""
    for line in structure:
        bla, seeds=read(line, seeds=seeds, dico=dico)#return non used seeds
        haiku+=bla + "\n"
    print("Generated Haiku", haiku)

    #--clean&-speak it loud
    haiku= re.sub("\s\s+" , " ", haiku) #remove multiple blanks
    print("Formatted Haiku", haiku)

    return haiku

#--------------------------------------------
#--------SEMANTIC SPACE REDEFINE PROCEDURES------------------
#---------------------------------------

def redefine_embeddings(embeddings, trinity):
    """
    Redefine embeddings of the 3 concepts coming from the reading.
    The embeddings of these 3 words get pulled towards the gravity center.
    Inputs:
        embeddings: dictionary, with the words and vectors
        trinity: 3 concepts (i.e. string)
    """
    #-0--compute center of gravity
    gravity_pull=0.2 #TBD
    gravity_center=embeddings[trinity[0]]+embeddings[trinity[1]]+embeddings[trinity[2]]
    gravity_center=1/3*gravity_center
    #-1---move embeddings towards gravity center
    for i in range(3):
        embeddings[trinity[i]]=(1-gravity_pull)*embeddings[trinity[i]]+gravity_pull*gravity_center

    return embeddings

#--------------------------------------------
#--------DRAWING PROCEDURES------------------
#---------------------------------------

def update_event_data(new_closer_concept, dist, point_idx, event_data):

    if new_closer_concept not in list(event_data.keys()):
        #new concept, then add it with as values idx point trajectory and word
        event_data[new_closer_concept]=[dist, point_idx]
    elif dist<event_data[new_closer_concept][0]:
        #if distance smaller, update point index
        event_data[new_closer_concept]=[dist, point_idx]

    return event_data

#--------------------------------------------
#--------DRAWING PROCEDURES------------------
#---------------------------------------

def draw(trajectory, trinity_trajectory, title):
    """
    Draw the pattern given the list of points.
    #TODO: 3D rendering??
    """
    trajectory_vct=np.array(trajectory)
    trinity_trajectory.append(trinity_trajectory[0])
    trinity_trajectory_vct=np.array(trinity_trajectory)
    plt.figure(figsize=(10,5))
    plt.plot(trajectory_vct[:,0],trajectory_vct[:,1], color="limegreen", marker="2",markevery=1, markersize=6, markeredgecolor="limegreen")
    plt.plot(trinity_trajectory_vct[:,0],trinity_trajectory_vct[:,1], color="deeppink", marker="1",markevery=1, markersize=10, markeredgecolor="deeppink")
    #show
    plt.show()
    #or save it (have to choose)
    #plt.savefig(title+'.png')
    #plt.close()

