
import fire
import nltk
import numpy as np
import random
from parameters import *

##SEED Sentence generators (incorporating a contextual seed)
path="./chris/data/" #Modify when...


#LOAD text files
wordsDic = {} #Dictionnary of list words
filenames=["A", "Ad1", "Ad2", "Ad3", "V", "Vt", "P", "Pf", "P0", "PR0", "PR0a", "PR1a", "PR1", "N", "N2", "Nf", "Na", "Aa", "Va", "Nfa", "ism", "Duo", "Nf", "Ma", "S", "Sc", "ESS", "ASA", "ABL", "QU", "Tion", "Duoa"]
for filename in filenames:
    wordsDic[filename] = [line.rstrip('\n') for line in open(path+filename+'.txt')]
#list structure
structures = [line.rstrip('\n') for line in open(path+'structures.txt')]
#IF OPENNED fp = open('path/to/file.txt', 'r')  THEN CLOSE FILE: fp.close()
#read method will read in all the data into one text string.
#readline which is one useful way to only read in individual line incremental amounts at a time and return them as strings.
#readlines, will read all the lines of a file and return them as a list of strings.

def readUnit(unit, seedWord):
    if unit=="SEED":
        bla=seedWord
    elif unit in wordsDic.keys():
        bla=read(random.choice(wordsDic[unit]), seedWord) #random element in it
    elif unit=="Ns":
        bla=readUnit("N", seedWord)
    elif unit=="X":
        bla=read("N//Na//N/and/N//N2/P0/N//Pf/Na//Na/P0/N//A/A/N//A/N//Ns/N2//N2//N//A/N//Ns/N2//N2//N//A/N//Ns/N2//N//A/N//Ns/N2//N//A/N//Ns/N2//N//A/N//Ns/N2//N//A/N//Ns/N2//N//A/N//Ns/N2//N//A/N//Ns/N2//A/N2//A/N2//A/N2//D//Da", seedWord)
    elif unit=="Xs":
        bla=read("Ns//A/Ns//Ns/N2s//Na/P0/Ns//A/Na", seedWord)
    elif unit=="Xp":
        bla=read("Np//A/Np//Ns/N2p//Np/P0/Na", seedWord)
    elif unit=="Y":
        bla=read("Nf//Nfa//Nf//Nfa//the/A/N//the/Na/P/N//the/Na/P/X//the/Ns/N2//the/A/Ns/N2//the/X/P/X//the/X/P0/X//the/Vg/X//X/,/X/and/X//both/X/and/X", seedWord)
    elif unit=="W":
        bla=read("V//Vt/X", seedWord)
    else:
        bla=unit
    return bla

def read(structure, seedWord):
    sentence=""
    things=structure.split(" ")
    for thg in things:
        elements=thg.split("//")
        element=random.choice(elements)
        units=element.split("/")
        for unit in units:
            sentence+=" "+ readUnit(unit.strip(), seedWord)#Strip to remove if spaces
    return sentence

#Extract a seed from a sentence>>>
##NNP is a proper Noun, NNPS, proper noun plural, NN is a noun, NNS when plural
def extract(blabla):#case where blabla none type?
    if blabla=="" or blabla is None: #may have issue ?
        return 'infrastructure'
    else:
        listS=blabla.split(".")
        index=len(listS)-1
        foundNoun=False
        while not foundNoun and index>=0:
            sentence=listS[index]
            nouns=[]
            for word,pos in nltk.pos_tag(nltk.word_tokenize(sentence)):
                if (pos == 'NN' or pos == 'NNS'):
                     nouns.append(word)
            index+=-1
            if len(nouns)>0:
                foundNound=True
        if foundNoun:
            return random.choice(nouns)
        else:
            return 'network'


def generate(blabla):
    seedWord=extract(blabla)
    structure=random.choice(structures)
    return read(structure, seedWord)



#if __name__ == '__main__':
#    fire.Fire(generate)
