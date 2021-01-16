import re



def crop_unfinished_sentence(text):
    """
    Remove last unfinished bit from text. 
    """
    #SELECT FROM THE RIGHT rindex s[s.rindex('-')+1:]  
    stuff= re.split(r'(?<=[^A-Z].[.!?]) +(?=[A-Z])', text)

    new_text=""
    for i in range(len(stuff)):
        if i<len(stuff)-1:
            new_text+= " " + stuff[i]
        elif stuff[i][-1] in [".", ":", "?", "!", ";"]:#only if last character ounctuation keep
            new_text+= " " + stuff[i]

    return new_text