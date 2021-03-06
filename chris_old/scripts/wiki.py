
import re
import urllib.request as ur
import nltk
from nltk import word_tokenize, sent_tokenize, pos_tag
from nltk.corpus import wordnet
from nltk.stem.wordnet import WordNetLemmatizer
import string
import wikipediaapi
wikipedia = wikipediaapi.Wikipedia('en')

excluded=['a', 'the', 'an', 'I', 'to', 'are', 'not', 'for', 'best','you', 'they', 'she', 'he', 'if', 'me', 'on', 'is', 'are', 'them', 'why', 'per', 'out', 'with', 'by'] #exclude these words to be looked upon

lemmatizer = WordNetLemmatizer()

#Extract word which are in wikipedia from a text. For a word, use Lemmatizer to avoid plural and multiple same roots (does it ? Do we want it turn caring into care ? Or just for the check?). For compose word, take as it is.
#CF https://www.machinelearningplus.com/nlp/lemmatization-examples-python/
#When check if in the list, should check if the root is the same than another element (stem) and in this case, not add it, or if same even though capital/minors
#For now, also exclude if word have number
#https://pypi.org/project/Wikipedia-API/ check API


def hasNumbers(inputString):
    return any(char.isdigit() for char in inputString)

#Check if a disambiguation Page
def disambiguationPage(word):
    page = wikipedia.page(word)
    categories = page.categories
    disambPage=False
    for title in categories.keys():#dictionary
        if title=="Category:Disambiguation pages":
            disambPage=True
    print(disambPage)
    return disambPage

def extract(blabla, graph, memory,  nbWord):
    OKWikipedia=[]
    OKWiktionary=[]
    if len(blabla)==0: #may have issue ?
        return OKWikipedia, OKWiktionary
    else:
        counter=0
        for word, pos in nltk.pos_tag(word_tokenize(blabla)):
            if counter<nbWord:#Stop once has nbWord in wikipedia
                #also take verbs and others : VBP  later >>>
                if not word.isupper():#not for AI etc. Then turn it low. Should still work for wikipedia if Google donald_trump for instance
                    word=word.lower()
                #For Wikipedia
                if not word is None and len(word)>1 and not hasNumbers(word) and (pos == 'NN' or pos == 'NNS' or pos == 'NNP'):
                    pos2=[]
                    word=lemmatizer.lemmatize(word) #Does it even for NNP ?? What will happen? #word=wordnet.morphy(word)
                    for tmp in wordnet.synsets(word): #Take all tags corresponding to exactly the name
                        if tmp.name().split('.')[0] == word:
                            pos2.append(tmp.pos())
                    if wikipedia.page(word).exists() and (pos == 'NNP' or (len(pos2)>0 and pos2[0]=='n')) and not (word in OKWikipedia) and not word.lower() in memory and not disambiguationPage(word):#up to capital:
                        if word in graph.keys():#Word is there, augment its weight.
                            graph[word][0]=graph[word][0]*1.1
                        elif word.lower() in graph.keys():
                            graph[word.lower()][0]=graph[word.lower()][0]*1.1
                        else: #Add word !
                            OKWikipedia.append(word)
                            counter+=1
                #FOR WIKTIONARY, should CHECK BETTER if exist, take more verb etc. Also if rare
                #if not word is None and len(word)>1 and not hasNumbers(word) and (pos == 'NN' or pos == 'NNS' or pos=='JJ' or pos=='VBP'):
                    #if not word in OKWiktionary and not word in graph.keys() and not word.lower() in graph.keys() and not word.lower() in memory:#up to capital:
                        #OKWiktionary.append(word)
        #DUO WORDS for wikipedia:
        #For Duo Word (ADJ + Noun, or Noun + Noun or... second is a noun)
        #EX:  global_warming https://en.wikipedia.org/wiki/Global_warming
        wordList=blabla.split()
        counter=0
        for i, word in enumerate(wordList):
            if counter<nbWord:
                word= word.strip(string.punctuation)
                if not word.isupper():#not for AI etc.
                    word=word.lower() #Could also lemmatize >
                if i<len(wordList)-1:
                    nextword=wordList[i+1]
                    nextword=nextword.strip(string.punctuation)
                    if not nextword.isupper():#not for AI etc.
                        nextword=nextword.lower()
                    duo=word+" "+nextword
                    if len(word)>1 and len(nextword)>1 and word not in excluded and nextword not in excluded and not hasNumbers(word) and not hasNumbers(nextword) and wikipedia.page(duo).exists() and not (duo in OKWikipedia) and not disambiguationPage(duo):
                        if duo in graph.keys():
                            graph[duo][0]=graph[duo][0]*1.1
                        elif duo.lower() in graph.keys():
                            graph[duo.lower()][0]=graph[duo.lower()][0]*1.1
                        else:
                            OKWikipedia.append(duo)
                            counter+=1
        print("OKWikipedia: ", OKWikipedia)
        return OKWikipedia, OKWiktionary, graph
