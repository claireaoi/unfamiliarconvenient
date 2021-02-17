import re
import coreQuest
import json




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



def loadSelf(first_run):
    """
        The VA loads his self_graph, memory, lifetime, as last saved. Or build it if first time.
    """
    if first_run:
        phrase="Hatching self in process..."
        print(phrase)
        self_graph, memory, description=coreQuest.hatchSelf(MAX_PICK_WORD, threshold_similarity)
        self_data=dict()
        self_data["lifetime"]=0
        print(description)
  
    else:
        with open('./case_study/data/selfgraph.txt', 'r') as json_file:
            self_graph = json.load(json_file)
        with open('./case_study/data/memory.txt', "r") as f:
            memory=f.readlines() #List of words concepts he looked up
        with open('./case_study/data/selfdata.txt', "r") as json_file:
            self_data=json.load(json_file)
        lifetime=self_data["lifetime"]
        phrase="I am here. My lifetime is "+ str(lifetime) + " interactions."
        print(phrase)
        #client.emit(Message('speak', data={'utterance': phrase}))#cannot put before run forever ?
  
    return self_graph, memory, self_data
