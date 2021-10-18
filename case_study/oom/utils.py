
import json
import math
import numpy as np
import random
import matplotlib.pyplot as plt
from string import punctuation
import re
import seaborn as sns


# =============================================================================
########### INIT CONSTANT
# =============================================================================

# --init constants
FILENAMES = [
    "A",
    "Ad1",
    "Ad2",
    "Ad3",
    "V",
    "Vt",
    "V2",
    "V+",
    "P",
    "Pf",
    "P0",
    "PR0",
    "PR0a",
    "PR1a",
    "PR1",
    "N",
    "N2",
    "Nf",
    "Nfa",
    "Na",
    "Aa",
    "Va",
    "Nfa",
    "ism",
    "Duo",
    "Nf",
    "Ma",
    "S",
    "Sc",
    "ESS",
    "ASA",
    "ABL",
    "QU",
    "Tion",
    "Duoa",
]


# =============================================================================
########### INIT PROCEDURES
# =============================================================================

def initialize(graph_path, words_path, embeddings_path, embeddings2D_path):
    """ 
    Load files, embeddings, etc.
    """
    #load self self_graph
    with open(graph_path) as json_file:
        self_graph = json.load(json_file)

    #load dictionary
    wordsDic={}
    for filename in FILENAMES:
        wordsDic[filename] = [line.rstrip('\n') for line in open(words_path+filename+'.txt')]
    
    #load templates
    with open(words_path+'haiku.txt', "r") as f:
        templates  = f.read().split(">>>") #LIST for each Haiku

    #load world embeddings
    with open(embeddings_path) as json_file:
        self_embeddings = json.load(json_file)

    ne=len(list(self_embeddings.keys()))
    embeddings2D= np.load(embeddings2D_path)
    assert list(embeddings2D.shape)==[ne,2]
    print("Retrieved {} embeddings ".format(ne))
    idx=list(self_embeddings.keys()).index("acid")
    return self_graph, wordsDic, templates, self_embeddings, embeddings2D


# =============================================================================
########### VECTOR PROCEDURES
# =============================================================================

def approximately_colinear(p1,p2,p3, threshold=0.05):
    """
        Determine if 3 points approximately colinear. Here, look if angle between 2 vectors small enough
        #TODO: More efficient way.
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


def nearest_concept(points, ref, excluded_id):
    """
        Find nearest point from a list to a point, which are not in excluded_id
        Inputs:
            points: list of point
            ref: one point compare to
            excluded_id: list of idx
        Outputs:
            idx: index of this point in points
            dist[idx]: distance of this point to ref
    """
    #-0---turn excluded_ids into a np array
    excluded_ids=np.array(excluded_id)

    #-1---compute distance of points in points with trajectory ref
    dist=[np.linalg.norm(point - ref) for point in points]
    
    #-2---change all value dist in the excluded ids to very high value to be sure they are not picked by min later
    HORIZON=1000000000
    dist=np.array(dist)
    excluded_ids=excluded_ids.astype(int)
    dist[excluded_ids]=HORIZON

    #-3-----take min
    idx = np.argmin(dist)

    #4---check if id is new or not
    neue = not(idx in excluded_id)
    return idx, dist[idx], neue

# TEST :
# points=[np.random.rand(2), np.random.rand(2)]
# ref=np.random.rand(2)
# excluded_id=[1]
# idx, d=nearest_concept(points, ref, excluded_id)
# print(idx, d)


# =============================================================================
########### HAIKU PROCEDURES
# =============================================================================

def pick_template(templates):
    """
    Pick a template for the Haiku
    NOTE: has different choice for different lines too
    """
    template_=random.choice(templates)
    template=template_.split("\n\n")
    final_template=[]
    for el in template:
        lines=el.split("\n")
        line=random.choice(lines)
        final_template.append(line)
    return final_template

def read(line, seeds=[], dico=None):
    """
    Reading a line;
    Decoding the template line picked into words.
    """
    sentence=""
    things=line.split(" ")
    for thg in things:
        elements=thg.split("//")#// means an or
        element=random.choice(elements)
        units=element.split("/")#/ means an AND
        for unit in units:
            bla, seeds=readUnit(unit.strip(), seeds=seeds, dico=dico)
            try: 
                sentence+=" "+ bla.strip()#Strip to remove if spaces
            except:
                print(bla)
    return sentence, seeds

def readUnit(unit, seeds=[], dico=None):
    """
    Reading a unit;
    this may be a word or a "code" denoting a word type
    """
    #-----may use seeds----
    if unit in ["S", "N","N2", "Ns", "N2s", "N2p", "Np"]:
        #NOTE: here dont care about plural !
        if len(seeds)>0:
            bla=seeds[0]
            seeds.pop(0)
        else:
            unit=unit.replace("s","")
            unit=unit.replace("p","")
            bla, w=read(random.choice(dico[unit]), dico=dico)
    #---------composite structures
    elif unit=="X" or unit=="Xs" or unit=="Xp":
        #has removed Duo//Duoa// compoared to old haiku
        bla, seeds=read("N//Na//Na/N2//N/and/N//N2/P0/N//Pf/Na//Na/P0/N//A/A/N//A/N//Ns/N2//N2//N//A/N//Ns/N2//N2//N//A/N//Ns/N2//N//A/N//Ns/N2//N//A/N//Ns/N2//N//A/N//Ns/N2//N//A/N//Ns/N2//N//A/N//Ns/N2//N//A/N//Ns/N2//A/N2//A/N2//A/N2", seeds=seeds, dico=dico)
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
    elif unit=="XWg": #NEED ?
        bla, seeds=read("X/Wg", seeds=seeds, dico=dico)
    elif unit=="PRO":
        bla, seeds=read("S/V//S/Vt/X//X/V//N/Vt/X//S/V/P0/X", seeds=seeds, dico=dico)
    #---not affecting seeds
    elif unit=="A":#removed A0//A0/A0//A0/A0//A0/A0/A0//
        bla, w=read("A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//Ad2/A0//A0//Ad2/A0//Ad2/A0//still/A0//A0/yet/A0//yet/A0//soon/A0//somehow/A0//already/A0", dico=dico)
    elif unit=="A0":
        bla, w=read(random.choice(dico["A"]), dico=dico)
    elif unit=="PR10":
        bla, w=read(random.choice(dico["PR1"]), dico=dico)
    elif unit=="PR1":
        bla, w=read("PR10//PR10//PR10//PR10//PR10//PR10//Ad1/PR10//Ad2/PR10//Ad2/PR10", dico=dico)
    #--------verbs
    elif unit=="Vd" or unit=="Vad" or unit=="Vtd" or unit=="V2d":
        verb=random.choice(dico[unit.replace("d", "")]).split(" ")
        bla=verb[0]+"ed" #okay as after use grammar corrector
        if len(verb)>0:
            bla+=" "+' '.join(verb[1:])
        # bla=lexeme(verb[0])[4] #past
    elif unit=="Vag" or unit=="Vg" or unit=="Vtg" or  unit=="V2g":
        verb=random.choice(dico[unit.replace("g", "")]).split(" ")
        bla=verb[0]+"ing" #okay as after use grammar corrector
        if len(verb)>0:
            bla+=" "+' '.join(verb[1:])
        ## bla=lexeme(verb[0])[2] #present participe
    #----for the other categories
    elif unit in dico.keys():
        bla, w=read(random.choice(dico[unit]), dico=dico)

    else: #---in case just a word
        bla=unit

    return bla, seeds


def generate_one_haiku(seeds, templates, dico, grammarParser):

    """
    Args: 
        seeds: 3 words with which to generate an haiku
        templates: templates for Haiku
        dico: dictionnary of words, by genre (noun, adjective etc)
        grammarParser: to parse grammar mistakes
    """
    remaining_seeds=seeds
    
    #-1--chose a template for the Haiku
    template = pick_template(templates)
    print("Picked a template", template)

    #-2---generate Haiku line by line
    haiku=""
    for line in template:
        bla, remaining_seeds=read(line, seeds=remaining_seeds, dico=dico)#return non used seeds
        haiku+=bla + "\n"
    print("Generated Haiku: \n", haiku)

    return haiku, remaining_seeds

def generate_haiku(seeds, templates, dico, grammarParser):

    """
    Args: 
        seeds: 3 words with which to generate an haiku
        templates: templates for Haiku
        dico: dictionnary of words, by genre (noun, adjective etc)
        grammarParser: to parse grammar mistakes

    Output: haiku (string)
    """
    assert len(seeds)==3

    #-1---generate haiku until use at least 2 seeds (so remain less than 1, because 3 seeds originally):
    remaining_seeds=seeds
    while len(remaining_seeds)>1:
        haiku, remaining_seeds=generate_one_haiku(seeds, templates, dico, grammarParser)

    #-2---correct grammmar mistakes, verb conjugations etc.
    haiku=grammarParser.parse(haiku)['result']
    print("Grammarly corrected Haiku: \n", haiku)

    #-3---reformat
    haiku=haiku.replace("\n", ";")
    print("Formatted Haiku:", haiku)

    return haiku


#--------------------------------------------
#--------SEMANTIC SPACE REDEFINE PROCEDURES------------------
#---------------------------------------

def redefine_embeddings(embeddings, trinity):
    """
    Redefine embeddings of the 3 concepts coming from the reading.
    The embeddings of these 3 words get pulled towards the gravity center.
    Inputs:
        embeddings: dictionary, with the words and vectors. 
        #NOTE: beware, here vector saved as list, may be dim [1,x], [2,x], [3,x]
        #TODO: how treat the rows? for now ignore other rows when they appear
        trinity: 3 concepts (i.e. string)
    """
    #-1--compute center of gravity
    gravity_pull=0.2 #TBD
    gravity_center=np.array(embeddings[trinity[0]][0])+np.array(embeddings[trinity[1]][0])+np.array(embeddings[trinity[2]][0])
    gravity_center=gravity_center / 3
    #-2---move embeddings towards gravity center
    for i in range(3):
        shifted_embedding=(1-gravity_pull)*np.array(embeddings[trinity[i]][0])+gravity_pull*gravity_center
        embeddings[trinity[i]][0]=shifted_embedding.tolist()
    return embeddings



#--------------------------------------------
#--------DRAWING PROCEDURES------------------
#---------------------------------------

def visualize_event_chart(trajectory, trinity_trajectory, haiku, output_path="./000.png"):
    """
    Final drawing
    #TODO: Better rendering: only figure here save separately haiku w/ same id.
    """
    trajectory_vct=np.array(trajectory)
    trinity_trajectory.append(trinity_trajectory[0])
    trinity_trajectory_vct=np.array(trinity_trajectory)
    fig=plt.figure(figsize=(5,10))
    plt.axis('off')

    #NOTE: here inverse coordinates compared to before to have vetical plot
    plt.plot(trajectory_vct[:,1],trajectory_vct[:,0], color="limegreen", linewidth=2, marker="2",markevery=1, markersize=12, markeredgecolor="limegreen")
    plt.plot(trinity_trajectory_vct[:,1],trinity_trajectory_vct[:,0], color="deeppink",linewidth=6, marker="1",markevery=1, markersize=24, markeredgecolor="deeppink")
    
    bottom0, left = .05, 0.01 #to be adjusted
    bottom1, left = .03, 0.01 #to be adjusted
    bottom2, left = .01, 0.01 #to be adjusted

    haikuList=haiku.split(";")#split along verse

    #add Haiku to the plo
    ax = fig.add_axes([0, 0, 1, 1])
    ax.text(left, bottom0, haikuList[0],
    horizontalalignment='left',
    verticalalignment='bottom',
    transform=ax.transAxes,
    color="deeppink")
    
    ax.text(left, bottom1, haikuList[1],
    horizontalalignment='left',
    verticalalignment='bottom',
    transform=ax.transAxes,
    color="deeppink")

    ax.text(left, bottom2, haikuList[2],
    horizontalalignment='left',
    verticalalignment='bottom',
    transform=ax.transAxes,
    color="deeppink")

    ax.set_axis_off()


    #show
    plt.savefig(output_path)
    #plt.close()
