
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


from transformers import GPT2LMHeadModel, GPT2Tokenizer


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


def initialize(filenames, graph_path, words_path, embeddings_path):
    """ """

    #load self self_graph
    with open(graph_path) as json_file:
        self_graph = json.load(json_file)

    #load dictionary
    wordsDic={}
    for filename in filenames:
        wordsDic[filename] = [line.rstrip('\n') for line in open(words_path+filename+'.txt')]
    
    #load templates
    with open(words_path+'haiku.txt', "r") as f:
        templates  = f.read().split(">>>") #LIST for each Haiku

    #load world embeddings
    with open(embeddings_path) as json_file:
        self_embeddings = json.load(json_file)

    return self_graph, wordsDic, templates, self_embeddings

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
    #TODO: Better way bounding without this concentration?
    num_points=len(points)
    array=np.array(points)
    
    #---1 compute 2D embeddings with TSNE
    embeddings_2D=TSNE(n_components=2).fit_transform(array)
    #NOTE: may tweak param such as perplexity, early_exaggeration, learning_rate etc, https://scikit-learn.org/stable/modules/generated/sklearn.manifold.TSNE.html
    #NOTE: This is trajectory of point between -1 and 1, else as to change normalization other points...
    #print(np.max(np.abs(embeddings_2D)))
    embeddings_2D= embeddings_2D/np.max(embeddings_2D, axis=0)#TODO this currently place them often on cirlce>>change!
    #print(embeddings_2D)
    return embeddings_2D

def load_gpt2(path_finetuned_ML_model=""):
    """
    Load gpt2 & tokenizer
    """
    #--load model and tokenizer
    if path_finetuned_ML_model=="":
        print("loading gpt2 model")
        model=GPT2LMHeadModel.from_pretrained("gpt2")
    else:
        print("loading custom model")
        model = GPT2LMHeadModel.from_pretrained(path_finetuned_ML_model)
    # Word Token Embeddings :
    #model_word_embeddings = model.transformer.wte.weight
    # Word Position Embeddings :
    #model_position_embeddings = model.transformer.wpe.weight
    
    #load tokenizer
    tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
    return model, tokenizer

def get_missing_words_embeddings(concepts, custom_embeddings, path_finetuned_ML_model=""):
    """
    Get Missing words embeddings.
    Inputs:
        concepts: list of string
        custom_embeddings: dictionnary whose keys are strings, values are the embeddings (encoded here as list size [m,N])
        path_finetuned_ML_model: path to the ML model. If empty, take base gpt2 from transformers lib
    Input

    """
    loaded=False
    keys=list(custom_embeddings.keys())
    #---
    for concept in concepts:
        if concept not in keys: #missing concept in embeddings...
            if not loaded:
                model, tokenizer=load_gpt2(path_finetuned_ML_model)
                loaded=True
            #index of the token
            index = tokenizer.encode(concept, add_prefix_space=True)
            #vector size [x,768], x being 1,2, 3 ...
            custom_embeddings[concept]= model.transformer.wte.weight[index,:].tolist()#as tensor not serializable
    if not loaded:
        print("No missing embeddings.")
    assert len(concepts)==len(keys)

    return custom_embeddings

def self_graph_embeddings(self_graph, custom_embeddings, bound, path_finetuned_ML_model=""):
    """
    Project the concepts of the self graph, once retrieved the embeddings vectors used for gpt2
    Input:
        self_graph: self graph
        custom_embeddings: dictionary of words & vectors in high dimension 
        path_finetuned_ML_model: where is ML model, may be needed to retrieve extra embeddings

    Outputs:
        concepts: list of keys of the graph
        scaled_embeddings2D: 2D embeddings of each of concepts in self concept

    """
    
    concepts=list(self_graph.keys())
    num_concepts=len(concepts)

    #-1--retrieve missing words embeddings attached to these concepts
    print("retrieve missing embeddings")
    custom_embeddings=get_missing_words_embeddings(concepts, custom_embeddings, path_finetuned_ML_model)
    #concepts_vectors=list(custom_embeddings.values())
    #TODO: For now, neglect other dimensions of the tensor which in some case is [2,768] ou [3,768]
    concepts_vectors=[tsr[0][:] for tsr in list(custom_embeddings.values())]

    #-2---turn these vectors into a 2D embedding
    print("tsne 2D projection")
    embeddings2D=tsne_embedding(concepts_vectors)
    
    #-3---rescale between max and min values
    print("rescale embeddings")
    scaled_embeddings2D=np.interp(embeddings2D, (embeddings2D.min(), embeddings2D.max()), (-bound, bound))
    
    #-4--- Visualize it
    data = pd.DataFrame(scaled_embeddings2D, columns=["x", "y"])# columns = concepts)
    sns.set_context("notebook", font_scale=1.1)
    sns.set_style("ticks")
    #sns.color_palette("hls", 8) #TODO: color palette need column...
    #each column is a variable and each row is an observation.
    sns.lmplot(x="x", y="y", palette=sns.color_palette("pastel", n_colors=num_concepts), data=data, truncate=False).set(xlim=(-bound-2, bound+2), ylim=(-bound-2, bound+2))
    #x,y should be column name in data
    plt.title('2D Embeddings',weight='bold').set_fontsize('14')
    plt.show()

    return custom_embeddings, scaled_embeddings2D


# =============================================================================
########### HAIKU PROCEDURES
# =============================================================================

def pick_template(templates):
    template_=random.choice(templates)
    template=template_.split("\n\n")
    final_template=[]
    for el in template:
        lines=el.split("\n")
        line=random.choice(lines)
        final_template.append(line)

    return final_template

def read(line, seeds=[], dico=None):
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
    #-----may use seeds----
    if unit in ["N","N2", "Ns", "N2s", "Na"]:
        if len(seeds)>0:
            bla=seeds[0]
            seeds.pop(0)
        else:
            bla, w=read(random.choice(dico[unit.replace("s","")]), dico=dico)
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


def generate_haiku(seeds, templates, dico):

    """
    Args: 
        seeds: 3 words with which to generate an haiku
        templates: templates for Haiku
        dico: dictionnary of words, by genre (noun, adjective etc)

    """

    #--chose a template for the Haiku
    template = pick_template(templates)
    print("Picked a template", template)

    #--generate Haiku
    haiku=""
    for line in template:
        bla, seeds=read(line, seeds=seeds, dico=dico)#return non used seeds
        haiku+=bla + "\n"
    print("Generated Haiku \n", haiku)

    #--clean&-speak it loud
    haiku=haiku.replace("\n", ";")
    haiku= re.sub("\s\s+"," ", haiku) #remove multiple blanks
    #print("Formatted Haiku", haiku)

    return haiku

#--------------------------------------------
#--------SEMANTIC SPACE REDEFINE PROCEDURES------------------
#---------------------------------------

def redefine_embeddings(embeddings, trinity):
    """
    Redefine embeddings of the 3 concepts coming from the reading.
    The embeddings of these 3 words get pulled towards the gravity center.
    Inputs:
        embeddings: dictionary, with the words and vectors. #NOTE: beware, here vector saved as list, may be dim [1,x], [2,x], [3,x]
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

def update_event_data(new_closer_concept, dist, point_idx, event_data):
    """
    Update event data.
    Inputs:
        new_closer_concept: string
        dist: float, distance between concept & domesticoCosmic point (of the trajectory)
        point_idx: int, index of the domesticoCosmic point
        event_data: dictionnary whose keys are string (concepts) and values are list [float, int] (which are distances, reps. idx of corresponding trajectory point in our case)
    Output:
        event_data: dictionnary whose keys are string (concepts) and values are list [float, int] (which are distances, reps. idx of corresponding trajectory point in our case)
    """

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
def draw_event_chart(trajectory, trinity_trajectory, haiku, event_id="000"):
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
    plt.plot(trajectory_vct[:,1],trajectory_vct[:,0], color="limegreen", marker="2",markevery=1, markersize=6, markeredgecolor="limegreen")
    plt.plot(trinity_trajectory_vct[:,1],trinity_trajectory_vct[:,0], color="deeppink", marker="1",markevery=1, markersize=12, markeredgecolor="deeppink")
    
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
    plt.savefig('./outputs/event_chart_'+ event_id+ '.png')
    #plt.close()




def visualize_event_chart(trajectory, trinity_trajectory, haiku, event_id="000"):
    """
    Final visualisation...
    #for now same than drawing procedure above...
    """
    #draw & save the trajectory 
    draw_event_chart(trajectory, trinity_trajectory, haiku, event_id=event_id)







# ######### TESTS PROCEDURES ABOVE ###########



# FILENAMES=["A", "Ad1", "Ad2", "Ad3", "V", "Vt", "V2", "V+", "P", "Pf", "P0", "PR0", "PR0a", "PR1a", "PR1", "N", "N2", "Nf","Nfa", "Na", "Aa", "Va", "Nfa", "ism", "Duo", "Nf", "Ma", "S", "Sc", "ESS", "ASA", "ABL", "QU",  "Tion", "Duoa"]
# GRAPH_PATH = "graph.json"# This path is temporary, it should refer to the fallbackassociative skill folder: /home/unfamiliarconvenient/.mycroft/fallback-associative/graph.json"
# WORDS_PATH="./data/" #Modify when...
# EMBEDDINGS_PATH="custom_embeddings.json" #where save words embeddings

# ##INIT
# self_graph, wordsDic, templates, custom_embeddings=initialize(FILENAMES, GRAPH_PATH, WORDS_PATH, EMBEDDINGS_PATH)

# #TEST SELF GRAPH EMBEDDINGS
# # concepts, scaled_embeddings2D=self_graph_embeddings(self_graph, custom_embeddings, 10)
# # print(scaled_embeddings2D.shape)

# #TEST HAIKU
# #haiku=generate_haiku(["submarine", "lightbulb", "fetish"], templates, wordsDic)

















