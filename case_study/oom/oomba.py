
import json
import math
import numpy as np
import random
import matplotlib.pyplot as plt

from sklearn.manifold import TSNE
import seaborn as sns
import pandas as pd


GRAPH_FILE="graph.json"
#TODO: What trigger this ?
#TODO: Retrieve gpt2 embeddings and Modify gpt2 embeddings, save them for later use!
#TODO: Visualisation
#TODO Haiku gene

##************************************(0) PRELUDE to the READING **********

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
    #TODO: Shall normalize these poonts?
    return embeddings_2D


def self_graph_embeddings(words_embeddings):
    """
    Project the concepts of the self graph, once retrieved the embeddings vectors used for gpt2
    Input:
        words_embeddings: dictionary of words & vectors in high dimension 
    Outputs:
        concepts: list of keys of the graph
        embeddings: 2D embeddings of each of concepts in self concept
    """
    #TODO: Uncomment
    # #--0-load self graph
    # self_graph=load_data_json(GRAPH_FILE)
    
    # #-1--get concepts in self
    # concepts=self_graph.keys()

    concepts=["cotton pad", "oulala", "bucket"] #TEMPORARY while did not leoad, comment as soon as load self graoh

    #-2--retrieve the vectors attached to these concepts
    concepts_vectors=[words_embeddings[word] for word in concepts]

    #-3---turn these vectors into a 2D embedding
    embeddings2D=tsne_embedding(concepts_vectors)
    

    #-4--- Visualize it
    data = pd.DataFrame(embeddings2D, columns=["x", "y"])# columns = concepts)
    sns.set_context("notebook", font_scale=1.1)
    sns.set_style("ticks")
    #sns.color_palette("hls", 8)
    #each column is a variable and each row is an observation.
    sns.lmplot(x="x", y="y", palette="pastel", data=data)
    #x,y should be column name in data
    plt.title('Self 2D Embeddings',weight='bold').set_fontsize('14')
    plt.show()
    #TODO: Save...

    return concepts, embeddings2D



##*********************************** (1) READING **********

def reading(trajectory):
    """
    Reading of the trajectory, given in input
    Inputs:
        trajectory: list of points in 2D space send by roomba
    Output:
        trinity: 3 closer self concepts selected
        words_embeddings: redefined embedding dictionary
        
    """
    num_points_init=len(trajectory)

    #-0--retrieve gpt2 words embeddings. #TODO
    print("***Loading vocabulary and embeddings***")
    #for now, use random ones
    dim_words=50
    words_embeddings=dict()
    words_embeddings["cotton pad"]=np.random.rand((dim_words))
    words_embeddings["moonson"]=np.random.rand((dim_words))
    words_embeddings["bucket"]=np.random.rand((dim_words))
    words_embeddings["oulala"]=np.random.rand((dim_words))
    #--get only vectors from dictionary
    words_vectors=list(words_embeddings.values()) 

    #-1--compute self embeddings with tsne
    print("***Generating 2D embeddings of Self***")
    self_concepts, embeddings2D=self_graph_embeddings(words_embeddings)

    #TODO: picture points, maybe too far apart, has to rescale them between -1 and 1 ?

    #-2--- simplify pattern: if 3 consecutive points +/- aligned, remove the one in the middle
    print("***Simplifying trajectory***")
    i=0
    cleaned_trajectory=[trajectory[0]]
    while i<num_points_init-3:
        aligned=True
        count=i+1
        while aligned and count<num_points_init-1:
            p1, p2, p3=trajectory[i],trajectory[count], trajectory[count+1]
            ##check if p1,p2,p3 are colinear
            aligned=approximately_colinear(p1,p2,p3)
            count+=1
        cleaned_trajectory.append(trajectory[count]) 
        i=count
    num_points=len(cleaned_trajectory)
    print("Original trajectory length {} cleaned trajectory length {}".format( num_points_init,  num_points))

    #-3---extract subpattern if still too many points
    max_num_points=7 #TBD
    #NOTE: How choose which part extract? Random?
    extracted_trajectory=cleaned_trajectory
    if len(cleaned_trajectory)>max_num_points:
        start=random.randint(0,num_points-max_num_points)
        extracted_trajectory=cleaned_trajectory[start:start+max_num_points]
    print("Extracted a trajectory of length {}".format(max_num_points))

    #-4---find closer words to each of these points
    print("***Interpreting Trajectory; extracting closer concepts***")
    close_concepts=[]
    distances=[]
    for i, point in enumerate(extracted_trajectory):
        if (not (i == 0)) and (not (i == max_num_points-1)):
            idx, dist=find_nearest_concepts(embeddings2D, point)
            key=list(words_embeddings.keys())[idx] #get corresponding concept
            if key not in close_concepts:
                close_concepts.append(key)
                distances.append(dist)
            else:#update distance
                j=close_concepts.index(key)
                distances[j]=min(distances[j], dist)
    #TODO: save also point it is closer too 
    assert len(distances)==len(close_concepts)

    #-4---extract 3 closer concepts 
    indices=np.argsort(distances)[:3]
    trinity=[close_concepts[i] for i in indices]
    print("The 3 closer self concepts for this event are {}".format(trinity))
    #TODO check not same or 

    #-5---redefine embeddings of these 3 concepts
    print("***Reassessing Beliefs***")
    #TODO: modify the embeddings

    return trinity, words_embeddings

##*********************************** (2) INTERPRETATION **********
#TODO: HAIKU generatiom either generaive or ML train on haiku

##*********************************** (3) REDEFINING the SEMANTIC SPACE **********
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

##************************************ UTILS **********


def approximately_colinear(p1,p2,p3):
    """
        Determine if 3 points approximately colinear. Here, look if angle between 2 vectors small enough
        #TODO: More efficient way? 
        Inputs: 
            p1,p2,p3: 2D points
        Output: boolean
    """
    threshold=0.05 #TBD
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

def find_nearest_concepts(points, ref):
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
    idx = np.argsort(dist)[:1][0]
    return idx, dist[idx]

def load_data_json(filename):
    #TODO: Check path
    folder_skill="/home/unfamiliarconvenient/.mycroft/fallback-associative/"
    with open(folder_skill+filename) as json_file:
        data = json.load(json_file)
    return data



#----------TEST
trajectory=[]
for _ in range(10):
    trajectory.append(np.random.rand((2)))
reading(trajectory)
