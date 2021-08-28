
import re


def cut_extract(extract, maximum_char):
    """
    Cut a text extract if above a certain nb character
    """
    #TODO: Choose bigger paragraph from page 
    extract=" ".join(extract.split())#remove extra white space
    bound_extract=extract[:maximum_char] #trim if longer than wanted #TODO:take beginning or end?
    bound_extract=crop_unfinished_sentence(bound_extract)
    return bound_extract


def crop_unfinished_sentence(text):
    """
    Remove last unfinished bit from text. 
    """
    #TODO: better?
    #SELECT FROM THE RIGHT rindex s[s.rindex('-')+1:]  
    stuff= re.split(r'(?<=[^A-Z].[.!?]) +(?=[A-Z])', text)
    print(stuff)
    new_text=""
    for i in range(len(stuff)):
        if i<len(stuff)-1:
            new_text+= " " + stuff[i]
        elif len(stuff[i])>0 and (stuff[i][-1] in [".", ":", "?", "!", ";"]):#only if last character ounctuation keep
            new_text+= " " + stuff[i]

    return new_text

print(cut_extract("Bsshkslal. shdgsjk; shshsj ! djka", 23))