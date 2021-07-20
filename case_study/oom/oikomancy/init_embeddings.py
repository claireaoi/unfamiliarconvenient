import random

import json
import math
import numpy as np
import random

from transformers import GPT2LMHeadModel, GPT2Tokenizer

##########ONLY TO INIT EMBEDDINGS FIRST TIME...NOT USED LATER ON


########## ABOUT GPT 2 EMBEDDINGS
print("load models")
model = GPT2LMHeadModel.from_pretrained('gpt2')  # or any other checkpoint
# Word Token Embeddings :
#model_word_embeddings = model.transformer.wte.weight
# Word Position Embeddings :
#model_position_embeddings = model.transformer.wpe.weight

#tokenizer
tokenizer = GPT2Tokenizer.from_pretrained('gpt2')

########### INIT EMBEDDINGS

with open("graph.json") as json_file:
    self_graph = json.load(json_file)

print("retrieve init embeddings")
custom_embeddings={}
for concept in self_graph.keys():
    #TODO: check different roots?
    word_index = tokenizer.encode(concept,add_prefix_space=True)#WHY add_prefix_space ?
    tsr= model.transformer.wte.weight[word_index,:]
    custom_embeddings[concept]=tsr.tolist()#as tensor not serializable

print("save embeddings")
with open("custom_embeddings.json", 'w+') as outfile:
        json.dump(custom_embeddings, outfile)

#Test get the embedding of a word:
#word_index = tokenizer.encode('acid',add_prefix_space=True)
#vector = model.transformer.wte.weight[word_index,:].squeeze()
#print(vector.shape)
