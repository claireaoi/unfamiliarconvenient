
#***********************************************************************CUSTOMIZATION***************************************************************************

disruptiveness=0.5 #parameter between 0 and 1 how much would interact...>>>

#PARAMETERS of the trigger
customTriggers=dict()
customTriggers["audioRecord"]=["isCloseTo", ["I feel being listened to."]]
customTriggers["audioPlay"]=["isCloseTo", ["Let me hear."]]
customTriggers["toRemember"]=["beginsBy", ["I wonder "]] #would we evolve into having a third arm one day? OR setReminder?
customTriggers["remember"]=["isCloseTo", ["Remember something."]] #
customTriggers["laugh"]=["isCloseTo", ["I'm free.", "I love you."]]
customTriggers["DuckDuckGo"]=["beginsBy",["Why", "How"]] #how do i twerk? Why people google?
customTriggers["Wikipedia"]=["beginsByCut", ["I know about "]] #I know about ... #Special case, as will cut out I know about...


#PARAMETERS of the drift
nMLDrift=1
lengthMLDrift=200 #number character ML Drift >>>modify procedure to affect it

moodSeeds=dict()
moodSeeds["curious"]=["Why are they", "Why do they", "How could we", "I wonder if", "I wonder how", "Why are there still", "What should we think of", "Is there something like"]
moodSeeds["confrontational"]=["Maybe not.", "Yet, I feel this is wrong. ", "I would argue against this.", "I would prefer not to.", "What if this is bullshit?", "I don't believe in this. Listen,"]
moodSeeds["thrilled"]=["Amazing.", "That is wonderful.", "How beautiful is this.", "That is incredible."]
moodSeeds["emotional"]=["It makes me feel", "I feel like"]
moodSeeds["appreciative"]=["Let us appreciate how", "Let us contemplate the", "Now, let us breathe and take a moment for", "Let us welcome the", "Let us appreciate what", "Instead of opposing, we shoud embrace", "I would like to thank the world for what"]
moodSeeds["thrilled"]=["Amazing.", "That is wonderful.", "How beautiful is this.", "That is incredible."]


#PARAMETERS of the Self Quest
audibleSelfQuest=True # If Self Quest would be audible


#***********************************************************************INITIALIZATION***************************************************************************

###IMPORT libraries
import fire
import numpy as np
import random
import re
import Levenshtein as lev

###IMPORT scripts
import wiki


###PARAMETERS #Do not modify
mycroftTriggers=dict()
mycroftTriggers["audioRecord"]="Christopher, start recording for 2 minutes."
mycroftTriggers["audioPlay"]="Christopher, play the recording."
mycroftTriggers["remember"]="Christopher, what did you remember?"
mycroftTriggers["laugh"]="Christopher, random laughter."
mycroftTriggers["toRemember"]="Christopher, remember "
mycroftTriggers["DuckDuckGo"]="Christopher, "
mycroftTriggers["Wikipedia"]="Christopher, tell me about "

#***********************************************************************PROCEDURES*************************************************************************


def isCloseTo(sentence, triggers):
#Levenshtein Distance or fuzzy string matching fuzzywuzzy Check if fast>>
    isCloseTo=False
    for trigger in triggers:
        if not isCloseTo:
            similarity=lev.ratio(sentence.lower(),trigger.lower())
            isCloseTo=(similarity>=0.85)
    return isCloseTo

def beginsBy(sentence, triggers):
    beginsBy=False
    for trigger in triggers:
        beginsBy=beginsBy or (sentence.lower().startsWith(trigger.lower()))
    return beginsBy

def beginsByCut(sentence, triggers):
    beginsBy=False
    cutSentence=""
    for trigger in triggers:
        if not beginsBy:
            beginsBy=(sentence.lower().startsWith(trigger.lower()))
            if beginsBy:
                cutSentence=sentence.replace(trigger,'')
    return [beginsBy, cutSentence]


#Return the appropriate trigger along what has listened to. #SIMPLIFY>>
def triggerOne(sentence):
    trigger=""
    answer=""
    for triggerName in customTriggers.keys():
        triggers=customTriggers[triggerName][0]
        modeTrigger=customTriggers[triggerName][1]
        if modeTrigger=="beginsByCut":
            begin, cutSentence=beginsByCut(sentence,triggers)
            if begin:
                trigger=mycroftTriggers[triggerName]+cutSentence.lower()
        elif modeTrigger=="isCloseTo" and isCloseTo(sentence,triggers):
            trigger=mycroftTriggers[triggerName]
        elif modeTrigger=="beginsBy" and beginsBy(sentence,triggers):
            trigger=mycroftTriggers[triggerName]+sentence.lower()
    #If one trigger has been activated
    if not trigger=="":
        answer=askChris(trigger)
        print("Answer", answer)
    return trigger, answer

def trigger(blabla):
    trigger=""
    answer=""
    alreadyTriggered=False #Keep track as only trigger once per blabla. (?)
    #Split blabla into sentences:
    sentences= re.split('[?.!]', blabla)#re.split('! |. |?',lastbla)
    #Look for each one
    for sentence in sentences:
        if not alreadyTriggered:
            trigger, answer=triggerOne(sentence)
            if not trigger=="":
                alreadyTriggered=True
    return trigger, answer


def drift(blabla, mood='neutral'):
    #One Drift with GPT2, seeded with previous blabla, more an addendum depending on the mood.
    seedML=blabla #If too long, cut?
    if mood in moodSeeds.keys():
        seedML+= " " + random.choice(moodSeeds[mood])
    drift= cs.cond_model(model_name='124M',seed=None, nsamples=2, batch_size=1,length=lengthMLDrift,temperature=1.0,top_k=0,top_p=1, models_dir='./chris/models', blabla = seedML)
    # drift, fuckedUp=cleanText(drift) #Add Clean up part Later ??>>>
    client.emit(Message('speak', data={'utterance': drift})) #does it say this or just will answer?
    print(drift)
    return drift

#***********************************************************************MAIN*************************************************************************

#INTERACTION


def interactLoop(mood='neutral', ifEvolve=True):
    #(0) CATCH what is said. >>>>
    blablaHuman="I'm free."
    #(1) May Trigger a reaction, if something has been heard. If it is a bla, do it for each sentence if trigger something
    trigger, answer=trigger(blablaHuman)
    #(2) MLDrift, from what has been said, in a certain mood
    blablaVA=drift(blabla, mood)
    #(3) Self Quest: Wikipedia Check, Self Graph (Or happen later at end if too slow ?)
    if ifEvolve:
        answer, drift, ifadded=selfMapLoops(blablaHuman, 1, 1, audibleSelfQuest)
    #(4)Add the text heard in file, so later could grow from it.
    with open('/home/christopher/mycroft-core/chris/data/whatIHeard.txt', "a") as f:#renew each time there is an interaction
       f.write(blablaHuman)
    with open('/home/christopher/mycroft-core/chris/data/ALLwhatIHeard.txt', "a") as f:#cumulated
       f.write(blablaHuman)
    return blablaVA


#***********************************************************************END*************************************************************************

#direct Launch of interact
if __name__ == '__main__':
    fire.Fire(interact)
    #fire.Fire(acidLoops)
