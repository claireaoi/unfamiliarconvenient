
import fire
import nltk
import numpy as np
import random
from parameters import *
from nltk import word_tokenize
import urllib.request
###INITIALISATION SOME TRIGGERS
#DO WITH A DICTIONNARY>


#Generate a question for Chris from context.
def generate(context):
    OKWikipedia, OKWiktionary =wikiExtract(context)
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

        return question, phrase

#Tell which words are in wikipedia or wiktionnary
def wikiExtract(blabla):
    OKWikipedia=[]
    OKWiktionary=[]
    if blabla=="" or blabla is None: #may have issue ?
        return OKWikipedia, OKWiktionary
    else:
        tokens= word_tokenize(blabla)
        #CHECK FOR ONE NOUN:
        for token in tokens:
            #word,pos= nltk.pos_tag(token)
            #if (pos == 'NN' or pos == 'NNS' or pos == 'NNP'):
            codeURL1 = urllib.urlopen("https://en.wikipedia.org/wiki/"+ token).getcode()
            codeURL2 = urllib.urlopen("https://en.wiktionary.org/wiki/"+ token).getcode()
            if codeURL1 == 200: #Else, if doesnt exist, code 404
                OKWikipedia.append(token)
            if codeURL2 == 200: #Else, if doesnt exist, code 404
                OKWiktionary.append(token)
        #should also take 2 words with adjective or 2 noun    #https://en.wikipedia.org/wiki/Global_warming   global_warming
        for token, i in enumerate(tokens):
            if i<len(tokens)-1:
                nexttoken=tokens[i+1]
                codeURL1 = urllib.urlopen("https://en.wikipedia.org/wiki/"+ token + "_"+ nexttoken).getcode()
                codeURL2 = urllib.urlopen("https://en.wiktionary.org/wiki/"+ token + "_"+ nexttoken).getcode()
                if codeURL1 == 200: #Else, if doesnt exist, code 404
                    together=token+" "+ nexttoken
                    OKWikipedia.append(together)
                if codeURL2 == 200: #Else, if doesnt exist, code 404
                    together=token+" "+ nexttoken
                    OKWiktionary.append(together)
        print("OKWikipedia: ", OKWikipedia )
        print("OKWiktionary: ", OKWiktionary)
        return OKWikipedia,OKWiktionary

#if __name__ == '__main__':
#    fire.Fire(generate)
