
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
#TODO: Haiku gene Simplification

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
    #NOTE: This is trajectory of point between -1 and 1, else as to change normalization other points...
    print(np.max(np.abs(embeddings_2D)))
    embeddings_2D= embeddings_2D/np.max(embeddings_2D, axis=0)#TODO this currently place them often on cirlce>>change!
    print(embeddings_2D)
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

    concepts=["cotton pad", "oulala", "bucket", "yellow submarine", "dragonfruit", "waste", "carioca", "amino acids"] #TEMPORARY while did not leoad, comment as soon as load self graoh
    
    num_concepts=len(concepts)

    #-2--retrieve the vectors attached to these concepts
    concepts_vectors=[words_embeddings[word] for word in concepts]

    #-3---turn these vectors into a 2D embedding
    embeddings2D=tsne_embedding(concepts_vectors)
    
    #4---rescale between max and min values
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
    words_embeddings["yellow submarine"]=np.random.rand((dim_words))
    words_embeddings["waste"]=np.random.rand((dim_words))
    words_embeddings["dragonfruit"]=np.random.rand((dim_words))
    words_embeddings["carioca"]=np.random.rand((dim_words))
    words_embeddings["amino acids"]=np.random.rand((dim_words))
    #--get only vectors from dictionary
    words_vectors=list(words_embeddings.values()) 

    #-1--compute self embeddings with tsne
    print("***Generating 2D embeddings of Self***")
    self_concepts, embeddings2D=self_graph_embeddings(words_embeddings)

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
    close_concepts, distances, trajectory_points=[], [], []
    for i, point in enumerate(extracted_trajectory):
        if (not (i == 0)) and (not (i == max_num_points-1)):
            idx, dist=nearest_concept(embeddings2D, point)
            key=list(words_embeddings.keys())[idx] #get corresponding concept
            print(i, point, idx, key)
            if key not in close_concepts:
                close_concepts.append(key)
                distances.append(dist)
                trajectory_points.append(point)#point from traj is closer to
            else:#TODO: currently too often same concept closer to all>>> change this! Rather ok if same?
                j=close_concepts.index(key)
                if dist<distances[j]:#update distance #although risk one closer to several
                    distances[j]=dist
                    trajectory_points[j]=point
    assert len(distances)==len(close_concepts)==len(trajectory_points)

    #-4---extract 3 closer concepts 
    indices=np.argsort(distances)[:3]
    trinity=[close_concepts[i] for i in indices]
    trinity_trajectory=[trajectory_points[i] for i in indices]
    print("The 3 closer self concepts for this event are {}".format(trinity))
    print("They correspond to the 3 points in the trajectory {}".format(trinity_trajectory))

    #--5-------draw trinity---
    draw(extracted_trajectory, trinity_trajectory, "Blip")
    #---6---redefine embeddings of these 3 concepts
    print("***Reassessing Beliefs***")
    #TODO: modify the embeddings

    return trinity, words_embeddings

##*********************************** (2) INTERPRETATION **********
#TODO: HAIKU generatiom either generaive or ML train on haiku


def haiku_generator(trinity):
    """
    Generate an haiku containing the words in trinity
    """
    

    return haiku



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

def load_data_json(filename):
    #TODO: Check path
    folder_skill="/home/unfamiliarconvenient/.mycroft/fallback-associative/"
    with open(folder_skill+filename) as json_file:
        data = json.load(json_file)
    return data




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


#--------------------------------
#----------TEST------------
#------------------------
trajectory=[]
for _ in range(20):
    trajectory.append(2*(-0.5+np.random.rand((2))))

reading(trajectory)
