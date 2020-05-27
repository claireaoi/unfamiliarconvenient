
#Script to filter a text according to the number of alphabetical character notably

##############################################################################################################################################
#For NLP and Wikipedia
import nltk
from nltk import word_tokenize, sent_tokenize, pos_tag
from nltk.corpus import wordnet
from nltk.stem.wordnet import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()


def alphabetRatio(inputString):
    """
        Return number and ratio of non alphabetic character (white spaces not included) in a sentence
    """
    count=0
    ratio=0
    for char in inputString:
        if not char.isalpha() and not char==" ":
            count+=1
    if not len(inputString)==0:
        ratio=count/len(inputString)
    return ratio, count


def filterText(blabla, maxNonAlpha=maxNonAlpha , maxRatio=maxRatio):
    """
        Filter a text: remove sentences with higher non alphabetic number of character than the indicated max.
       Remove sentence with higher non alphabetical character ratio too than the indicated one.
       Output: Filtered text with the filteredRatio (between 0 and 1) measuring the amount of text which remains.

       NB: Filtering procedures are a very specialised matter, and depend of the outcome you want to have. 
       You could check repetition of characters, or too long words. 
       Or even filter any sentence which does not make gramatical sense (yet, this may be too strong criteria).
       You can filter also unrecognised words (yet depend if you have proper noun), etc.
    """
    sentences=nltk.tokenize.sent_tokenize(blabla)
    filtered_bla=""
    for sentence in sentences:
        ratio, count=alphabetRatio(sentence) #ratio non letter elements
        if len(sentence)>3 and ratio<maxRatio and count<maxNonAlpha:   #Test if not to many symbol and grammar ok
                filtered_bla+=sentence
    filteredRatio = len(filtered_bla)/len(blabla) #. Ideally wish it close to 1 
    print(filtered_bla)
    return filtered_bla, filteredRatio
