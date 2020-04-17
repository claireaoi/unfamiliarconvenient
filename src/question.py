
import fire
import nltk
import numpy as np
import random
from parameters import *
###INITIALISATION SOME TRIGGERS
#DO WITH A DICTIONNARY>


#If not context provided, generate these with certain proba (sum)
def normalize(proba):
    pTotal=sum(proba)
    proba[:] = [ x / pTotal for x in proba]
    cumProba=np.cumsum(proba)
    return cumProba


def generateVoid():
    cumProba=normalize(probaTrigger)
    rnd=random.uniform(0, 1)
    question="What is the weather?"
    for i in range(len(cumProba)-1):
        if cumProba[i] < rnd and rnd <= cumProba[i+1]:
            question=sayTrigger[i+1]
        elif rnd<=cumProba[0] and rnd>0:
            question=sayTrigger[0]
    return question


#Generate a question for Chris from context.
def generate(context):
    cumProba=normalize(probaQu)
    if context=="":#If context empty
        return generateVoid()
    else:
        words=[]
        nouns=[]
        proper=[] #>>>
        rnd=random.uniform(0, 1)
        for word,pos in nltk.pos_tag(nltk.word_tokenize(context)):
            if (pos == 'NN' or pos == 'NNS'):
                nouns.append(word)
                words.append(word)
            elif (pos == 'JJ' or pos == 'VB' or pos == 'VBP' or pos == 'VBD' ):
                words.append(word)
        if 0<rnd and rnd<=cumProba[0]: #Trigger case
            question= generateVoid()
        elif cumProba[0]<rnd and rnd<=cumProba[1]: #Donald
            if len(nouns)>0:
                question="What does Tronald Dump think about "+random.choice(nouns)+"?"
            else:
                question="What does Tronald Dump think about infrastructures ?"#>>>
        elif cumProba[1]<rnd and rnd<=cumProba[2]: #DEFI
            if len(words)>0:
                question="Tell me the definition of "+ random.choice(words)+" ."
            else:
                question="Tell me the definition of infrastructure."#>>>
        elif cumProba[2]<rnd and rnd<=cumProba[3]: #DUCKDUCK Go
            question="Have we always been human?" #>>>
        else:#CHAT #>>>generate
            question="Is my room bigger than wikipedia?" #

        return question



#if __name__ == '__main__':
#    fire.Fire(generate)
