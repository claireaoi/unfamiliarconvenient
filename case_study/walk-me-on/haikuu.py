
#Launch it via:
#python3 blabla.py --seed="What is singularity?" --nLine=50


import fire
import nltk
from nltk.corpus import wordnet
import numpy as np
import re
import random
# import spacy
# nlp = spacy.load('en')

from pattern3.text.en import conjugate, lemma, lexeme, PRESENT, SG #pip3 install pattern3 !
#TODO: seems need python3.6 !! https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-python.html


##SEED Sentence generators (incorporating a contextual seed)
path="/Users/lou/BOTS/Haikuu/data/" #Modify when...

#TODO: TUNE: more structure ? // Simpler
#TODO: CORRECT: avoid 2 consecutive seedWords? Sometimes only 2 lines?


#----------------------LOAD TEXT FILES & STRUCTURE ------------------

wordsDic = {} #Dictionnary of list words
filenames=["A", "Ad1", "Ad2", "Ad3", "V", "Vt", "V2", "V+", "P", "Pf", "P0", "PR0", "PR0a", "PR1a", "PR1", "N", "N2", "Nf","Nfa", "Na", "Aa", "Va", "Nfa", "ism", "Duo", "Nf", "Ma", "S", "Sc", "ESS", "ASA", "ABL", "QU",  "Tion", "Duoa"]
for filename in filenames:
    wordsDic[filename] = [line.rstrip('\n') for line in open(path+filename+'.txt')]
#load structures
f=open(path+'haiku.txt', "r")
structures_ = f.read()
f.close()
structures=structures_.split(">>>")

#-----------------------PATTERN LIBRARY ------------------
# print("Prelude, conjugation tests")
# print("Past", conjugate("throw", tense = "past",  person = 3,  number = "singular",  mood = "indicative", aspect = "imperfective",negated = False))
# print("Present participe", conjugate("throw", tense = "present",  person = 3,  number = "singular",  mood = "indicative", aspect = "progressive",negated = False))
# print (lexeme('threw'))#['throw', 'throws', 'throwing', 'threw', 'thrown']
#//CONJUGATE PATTERN TENSE INFINITIVE, PRESENT, PAST, FUTURE  # MOOD INDICATIVE, IMPERATIVE, CONDITIONAL, SUBJUNCTIVE  
# ASPECT # IMPERFECTIVE, PERFECTIVE, PROGRESSIVE 


#-----------------------PICK a STRUCTURE ------------------

def pick_structure():
    structure_=random.choice(structures)
    structure=structure_.split("\n\n")
    final_structure=[]
    for el in structure:
        lines=el.split("\n")
        line=random.choice(lines)
        final_structure.append(line)

    return final_structure
#pick_structure()

#-----------------------READ PROCEDURE------------------

def read(structure, seeds=[]):
    sentence=""
    things=structure.split(" ")
    for thg in things:
        elements=thg.split("//")#// means an or
        element=random.choice(elements)
        units=element.split("/")#/ means an AND
        for unit in units:
            bla, seeds=readUnit(unit.strip(), seeds)
            sentence+=" "+ bla.strip()#Strip to remove if spaces
    return sentence, seeds



def readUnit(unit, seeds=[]):

    #-----may use seeds----
    if unit in ["N","N2", "Ns", "N2s", "Na"]:
        if len(seeds)>0:
            bla=seeds[0]
            seeds.pop(0)
        else:
            bla, w=read(random.choice(wordsDic[unit.replace("s","")]))

    #---------composite structures
    elif unit=="N2p" or unit=="Np":#Here dont caree about plural !
        bla, seeds=read("N//Na//Pf/Na", seeds)
    elif unit=="X" or unit=="Xs" or unit=="Xp":
        bla, seeds=read("Duo//Duoa//N//Na//Na/N2//N/and/N//N2/P0/N//Pf/Na//Na/P0/N//A/A/N//A/N//Ns/N2//N2//N//A/N//Ns/N2//N2//N//A/N//Ns/N2//N//A/N//Ns/N2//N//A/N//Ns/N2//N//A/N//Ns/N2//N//A/N//Ns/N2//N//A/N//Ns/N2//N//A/N//Ns/N2//A/N2//A/N2//A/N2", seeds)
    elif unit=="X+":#to add to "the X ""...Ex: which...
        bla, seeds=read("whose/Na/W0//which/W//better/Vtd/that/W0//than/Vtd//which/have/been/PR1a//which/have/been/PR1//which/W0//the/X/PR1//thought/as/Nfa//we/are/trying/to/Vt//that/W0//that/we/allow/to/W0//we/are/Vtg//that/Ad2/W0//that/V+//that/have/become/A//that/do/not/W0//that/you/should/not/Vt", seeds)
    elif unit=="Y":
        bla, seeds=read("Y0//Y0//Y0//Y0//Y0/PR1//Y0/PR1a//all/what/W//the/X/X+//everyone/X+//anything/X+//each/X/X+//X/Wg", seeds)
    elif unit=="Y0":
        bla, seeds=read("Nf//Nfa//Nf//Nfa//Nfa//Nfa//the/A/N//the/Na/P/N//the/Na/P/X//the/Ns/N2//the/A/Ns/N2//the/X/P/X//the/X/P0/X//the/Vg/X//X/,/X/and/X//both/X/and/X//the/X/that/W0", seeds)
    elif unit=="W":
        bla, seeds=read("W0//W0//W0//W0//W0//V+//V+//V+//could/W0//should/W0//would/W0//could/V+//Ad2/W0//Ad2/W0", seeds)
    elif unit=="W0":
        bla, seeds=read("V//V//Vt/X//Va//Va//V2//Vt/Y//Vt/Nfa", seeds)
    elif unit=="WA":
        bla, seeds=read("Ad2/V//Ad2/Vt/X//V/Ad3//Vt/X/Ad3", seeds)
    elif unit=="Wd":
        bla, seeds=read("Vd//Vd//Vtd/X//Vad//Vad//V2d//Vtd/Y//Vtd/Nfa", seeds)
    elif unit=="Wg":
        bla, seeds=read("Vg//Vg//Vtg/X//Vag//Vag//V2g//Vtg/Y//Vtg/Nfa", seeds)
    elif unit=="XWg":#NEED ?
        bla, seeds=read("X/Wg", seeds)
    elif unit=="PRO":
        bla, seeds=read("S/V//S/Vt/X//X/V//N/Vt/X//S/V/P0/X", seeds)
  
    #---not affecting seeds
    elif unit=="A":
        bla, w=read("A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0/A0//A0/A0//A0/A0/A0//Ad2/A0//A0//Ad2/A0//Ad2/A0//A0/A0//still/A0//A0/yet/A0//yet/A0//soon/A0//somehow/A0//already/A0")    
    elif unit=="A0":
        bla, w=read(random.choice(wordsDic["A"]))
    elif unit=="PR10":
        bla, w=read(random.choice(wordsDic["PR1"]))
    elif unit=="PR1":
        bla, w=read("PR10//PR10//PR10//PR10//PR10//PR10//Ad1/PR10//Ad2/PR10//Ad2/PR10")
    #--------verbs
    elif unit=="Vd" or unit=="Vad" or unit=="Vtd" or unit=="V2d":
        verb=random.choice(wordsDic[unit.replace("d", "")]).split(" ")
        bla=lexeme(verb[0])[4] #past
        if len(verb)>0:
            bla+=' '.join(verb[1:])
    elif unit=="Vag" or unit=="Vg" or unit=="Vtg" or  unit=="V2g":
        verb=random.choice(wordsDic[unit.replace("g", "")]).split(" ")
        bla=lexeme(verb[0])[2] #present participe
        #conjugate(verb[0], tense = "present",  person = 3,  number = "singular",  mood = "indicative", aspect = "progressive",negated = False)
        if len(verb)>0:
            bla+=' '.join(verb[1:])
    #----remaining stuff
    elif unit in wordsDic.keys():
        bla, w=read(random.choice(wordsDic[unit]))

    else:#mean just a word
        bla=unit

    return bla, seeds

#-----------------------MAIN  PROCEDURE------------------


def generate_haiku():
    #seedWord=extract(seed)
    seeds=["cotton pad", "internet", "bucket"]
    haiku=""
    structure=pick_structure()
    for line in structure:
        bla, seeds=read(line, seeds)#return non used seeds
        haiku+=bla + "\n"
    print(haiku)
    haiku= re.sub("\s\s+" , " ", haiku) #remove multiple blanks

    return haiku


generate_haiku()


# if __name__ == '__main__':
#     fire.Fire(generate)
