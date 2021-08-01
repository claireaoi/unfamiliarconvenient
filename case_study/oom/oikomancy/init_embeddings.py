import random

import json
import math
import numpy as np
import random
import matplotlib.pyplot as plt
from sklearn.manifold import TSNE
import re
import seaborn as sns
import pandas as pd
import os.path
from os import path

from transformers import GPT2LMHeadModel, GPT2Tokenizer

#------------------PATHS----------
EMBEDDINGS_PATH="./oikomancy/custom_embeddings.json" #where save words embeddings
EMBEDDINGS2D_PATH="./oikomancy/custom_embeddings2D.npy" #where save words embeddings
GRAPH_PATH = "./oikomancy/graph.json"# This path is temporary, it should refer to the fallbackassociative skill folder: /home/unfamiliarconvenient/.mycroft/fallback-associative/graph.json"
PATH_ML_MODEL=""  #path to your fine tuned model, If empty, would use default model #NOTE: UPDATE this to actual model.


########## TO MIGRATE WITHIN FALLBACK SKILL VA #################

#TODO: 
# 1- PLace file init_embeddings in skill folder
# 2- Update the path used here depending on where are these things
# 3- Add the import in our fallback skill: from init_embeddings import update_embeddings
# 4- Add the following line in the initialisation of the skill once loaded model and tokenizer
#   update_embeddings(model, tokenizer, self_graph)


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

    return embeddings_2D


def get_missing_words_embeddings(model, tokenizer, concepts, custom_embeddings):
    """
    Get Missing words embeddings.
    Inputs:
        concepts: list of string
        custom_embeddings: dictionnary whose keys are strings, values are the embeddings (encoded here as list size [m,N])
    Input

    """
    keys=list(custom_embeddings.keys())
    
    # retrieve missing embeddings #TODO: CHeck different root.
    for concept in concepts:
        if concept not in keys: #missing concept in embeddings...
            #index of the token
            index = tokenizer.encode(concept, add_prefix_space=True)
            #vector size [x,768], x being 1,2, 3 ...
            custom_embeddings[concept]= model.transformer.wte.weight[index,:].tolist()#as tensor not serializable
    assert len(concepts)==len(keys)

    return custom_embeddings



# =============================================================================
########### MAIN UPDATE EMBEDDINGS And 2D EMBEDDINGS
# =============================================================================


def update_embeddings(model, tokenizer, self_graph, bound=1, visualize=False):
    """
    Main procedure would update the embeddings of all the words in the self graph in a json file,
    and compute their 2D projection via tsne.
    Project the concepts of the self graph, once retrieved the embeddings vectors used for gpt2
    Input:
        self_graph: self graph
        custom_embeddings: dictionary of words & vectors in high dimension 

    Outputs:
        concepts: list of keys of the graph
        scaled_embeddings2D: 2D embeddings of each of concepts in self concept

    """
    
    #---- load  embeddings
    print("1--load embeddings")
    if path.exists(EMBEDDINGS_PATH):
        with open(EMBEDDINGS_PATH) as json_file:
            custom_embeddings = json.load(json_file)
    else:
        custom_embeddings={}
    # retrieve missing embeddings, here use bound 1, scale later


    concepts=list(self_graph.keys())
    num_concepts=len(concepts)

    #-1--retrieve missing words embeddings attached to these concepts
    print("2---retrieve missing embeddings")
    custom_embeddings=get_missing_words_embeddings(model, tokenizer, concepts, custom_embeddings)
    #concepts_vectors=list(custom_embeddings.values())
    #TODO: For now, neglect other dimensions of the tensor which in some case is [2,768] ou [3,768]
    concepts_vectors=[tsr[0][:] for tsr in list(custom_embeddings.values())]

    #-2---turn these vectors into a 2D embedding
    print("3---tsne 2D projection")
    #TODO could avoid recompute, by loading it
    embeddings2D=tsne_embedding(concepts_vectors)
   
    #-3---rescale between max and min values
    print("4---rescale embeddings")
    scaled_embeddings2D=np.interp(embeddings2D, (embeddings2D.min(), embeddings2D.max()), (-bound, bound))
    
    #--4--save these embeddings
    print("5---save embeddings")
    with open(EMBEDDINGS2D_PATH, 'wb') as f: #save as npy file
        np.save(f, scaled_embeddings2D)
    with open(EMBEDDINGS_PATH, 'w+') as outfile:
        json.dump(custom_embeddings, outfile)

    #-5--- Visualize them
    if visualize:
        data = pd.DataFrame(scaled_embeddings2D, columns=["x", "y"])# columns = concepts)
        sns.set_context("notebook", font_scale=1.1)
        sns.set_style("ticks")
        #sns.color_palette("hls", 8) #TODO: color palette need column...
        #each column is a variable and each row is an observation.
        sns.lmplot(x="x", y="y", palette=sns.color_palette("pastel", n_colors=num_concepts), data=data, truncate=False).set(xlim=(-bound-2, bound+2), ylim=(-bound-2, bound+2))
        #x,y should be column name in data
        plt.title('2D Embeddings',weight='bold').set_fontsize('14')
        plt.show()



#--1--- load gpt2 model and tokenizer, and self graph
print("0--load models and graphs")
# #NOTE: Just temporary for test, once migrate this in the skill, we can use the loaded model!
model = GPT2LMHeadModel.from_pretrained('gpt2')  # or any other checkpoint
tokenizer = GPT2Tokenizer.from_pretrained('gpt2')
#model, tokenizer=load_gpt2(path_finetuned_ML_model)
with open(GRAPH_PATH) as json_file:
    self_graph = json.load(json_file)
    
update_embeddings(model, tokenizer, self_graph, visualize=True)




    #  
    #Test get the embedding of a word:
    #word_index = tokenizer.encode('acid',add_prefix_space=True)
    #vector = model.transformer.wte.weight[word_index,:].squeeze()
    #print(vector.shape)





   # Word Token Embeddings :
    #model_word_embeddings = model.transformer.wte.weight
    # Word Position Embeddings :
    #model_position_embeddings = model.transformer.wpe.weight