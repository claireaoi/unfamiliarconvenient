# !/usr/local/bin/python3
# -*- coding: utf-8 -*-


######Description############
#
# FallBack Skill where the VA do ML drifts, from a gpt-2 model, and the parameters registered in parametersDrift.py
#
######About############
# This script was created for the workshop Unfamiliar Virtual Convenient - Growing your Voice Assistant
# led by Vytautas Jankauskas and Claire Glanois through School of Machines, Make & believe, in spring 2020.
#
# Feel free to tune, or reshape it according to your project.

#**********************************************************************PARAMETERS for the ML Drift***************************************************************************

##Parameters for the gpt-2 parameters
finetuned_ML_model= True  #If do have a fine-tuned model
#global path_finetuned_ML_model
path_finetuned_ML_model='/gpt2'  #path to your fine tuned model
nDrift=1 #number of ML Drifts (successive generation can be triggered)

######Classic gpt-2 parameters:
#More parameters are available and more detail about gpt-2 parameters can be found here: https://huggingface.co/blog/how-to-generate
lengthDrift= 90 #Maximum length of the generated answer, counted in character
temperature = 0.9 #temperature. A classic parameter for language models. Increase the likelihood of high probability words and decreasing the likelihood of low probability words) by lowering the temperature and conversely.
repetition_penalty = 2 #Repetition Penalty drift
randomMode= True #if decide randomize moods
defaultMode='neutral' #If not, here is the mode chosen

######## To slightly influence the gpt-2 outcome, so-called 'Mode'.
#Below are only saturated example for better illustration. But you can tune them
#Possible Modes for the ML Drift, with their probabilities.
#Keeping the category neutral as such, with an empty string only, enable have the possibility of a neutral Mode, so unaltered ML drift.
modeSeeds=dict()
modeSeeds["curious"]=["Why are they", "Why do they", "How could we", "I wonder if", "I wonder how", "Why are there still", "What should we think of", "Is there something like"]
modeSeeds["confrontational"]=["Maybe not.", "Yet, I feel this is wrong. ", "I would argue against this.", "I would prefer not to.", "What if this is bullshit?", "I don't believe in this. Listen,"]
modeSeeds["thrilled"]=["Amazing.", "That is wonderful.", "How beautiful is this.", "That is incredible."]
modeSeeds["emotional"]=["It makes me feel", "I feel like"]
modeSeeds["appreciative"]=["Let us appreciate how", "Let us contemplate the", "Now, let us breathe and take a moment for", "Let us welcome the", "Let us appreciate what", "Instead of opposing, we shoud embrace", "I would like to thank the world for what"]
modeSeeds["thrilled"]=["Amazing.", "That is wonderful.", "How beautiful is this.", "That is incredible."]
modeSeeds["neutral"]=[""]

#RProbabilities of the different Modes
probaMode=dict()
probaMode["curious"]=0.2
probaMode["confrontational"]=0.2
probaMode["thrilled"]=0.1
probaMode["emotional"]=0.1
probaMode["appreciative"]=0.1
probaMode["thrilled"]=0.1
probaMode["neutral"]=0.2

#***********************************************************************INITIALIZATION***************************************************************************

from mycroft.skills.core import FallbackSkill
import random
#For the ML Drift
import transformers
import torch
from transformers import GPT2Tokenizer, GPT2LMHeadModel

#For NLP
import nltk
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('wordnet_ic')

from nltk import word_tokenize, sent_tokenize, pos_tag
from nltk.corpus import wordnet
from nltk.stem.wordnet import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()

global maxNonAlpha
maxNonAlpha=5

global maxRatio
maxRatio=0.3

#***********************************************************************PRELIMINARIES***************************************************************************

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


def filterText(blabla, maxNonAlpha, maxRatio):
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
    for i, sentence in enumerate(sentences):
        ratio, count=alphabetRatio(sentence) #ratio non letter elements
        if len(sentence)>3 and ratio<maxRatio and count<maxNonAlpha and i<len(sentences)-1:   #Test if not to many symbols and grammar ok
                filtered_bla+=sentence
    filteredRatio = len(filtered_bla)/len(blabla) #. Ideally it's close to 1
    print(filtered_bla)
    return filtered_bla


#***********************************************************************MAIN CLASS***************************************************************************

class MLdriftFallback(FallbackSkill):
    """
        A Fallback skill running some ML drits with gpt2, and a mode.
    """
    def __init__(self):
        super(MLdriftFallback, self).__init__(name='MLdrift')
        self.moodySeed=""
        # Initialize machine learning
        self.tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        if finetuned_ML_model:
            print("loading custom model")
            self.model = GPT2LMHeadModel.from_pretrained(path_finetuned_ML_model)
        else:
            self.model=GPT2LMHeadModel.from_pretrained("gpt2")


    def initialize(self):
        """
            Registers the fallback handler.
            The second Argument is the priority associated to the request.
            Lower is higher priority. But number 1-4 are bypassing other skills.
        """
        self.register_fallback(self.handle_MLdrift, 6)
        # Could register several handle


    def pickMoodySeed(self):
        """
           Choose a seed to potentially add as contaxt for the gpt-2 Drift
        """
        if randomMode: #if random Mode chosen only
            #From the dictionnary probaMode randomly pick a mode following their probability
            currentMode=random.choices(population=list(probaMode.keys()), weights=list(probaMode.values()), k=1)[0]
        else:
            currentMode=defaultMode
        if currentMode in modeSeeds.keys():#in case mode entered wrong by human to avoid error
            self.moodySeed=random.choice(modeSeeds[currentMode])

    def handle_One(self, blabla):
        """
            One gpt-2 drift from the last blabla
        """

        #(1) Choose the mode and possible seed and add it after the blabla
        self.pickMoodySeed()
        blabla=blabla+ " " + self.moodySeed

        #(2) ML Drift according to parameters
        #BEAM
        #model.generate(input_ids,max_length=50,num_beams=5,no_repeat_ngram_size=2, early_stopping=True)
        #OR **top_k** – (optional) int The number of highest probability vocabulary tokens to keep for top-k-filtering. Between 1 and infinity. Default to 50.
        #model.generate(input_ids, do_sample=True, max_length=50, top_k=50) 
        #also num_return_sequences=3
        #OR **top_p** – (optional) float The cumulative probability of parameter highest probability vocabulary tokens to keep for nucleus sampling. Must be between 0 and 1. Default to 1.
        #model.generate(input_ids, do_sample=True, max_length=50, top_k=0, top_p=0.95, num_return_sequences=3)
        #NORMAL_         #generator = self.model.generate(process, max_length = lengthDrift, temperature = temperature, repetition_penalty = repetition_penalty)

        #num_beams: 
        process = self.tokenizer.encode(blabla, return_tensors = "pt")
        generator = self.model.generate(process, max_length = lengthDrift, temperature = temperature, repetition_penalty = repetition_penalty, do_sample=True, top_k=50)
        drift = self.tokenizer.decode(generator.tolist()[0])



        i=0
        while i < 1:
            drift = drift.replace(str(blabla), "")
            i+=1

        #(3) Filter the Drift. Here a small filtering procedure.
        #Yet you are free to change the parameters, make it your own, by pass this step (comment out)
        filtered_drift=filterText(drift, maxNonAlpha, maxRatio)

        #(4) Say the drift out loud
        self.speak(filtered_drift)

        return filtered_drift

    #The method that will be called to potentially handle the Utterance
    #The method implements logic to determine if the Utterance can be handled and shall output speech if itcan handle the query.
    #For now, will handle all query.
    def handle_MLdrift(self, message):
        """
            Several gpt-2 drifts from the last utterance, with a possible mode
        """
        #(0) Get the human utterance
        utterance = message.data.get("utterance")
        #(1) Choose the mode and possible seed and add it
        loopCount=0
        blabla=utterance
        while loopCount<nDrift:
            loopCount+=1
            print("Drift n° {loopCount}")
            blabla=self.handle_One(blabla) #Only keep last part as context else too big? >>>

        return True


    #the Skill creator must make sure the skill handler is removed when the Skill is shutdown by the system.
    def shutdown(self):
        """
            Remove this skill from list of fallback skills.
        """
        self.remove_fallback(self.handle_MLdrift)
        super(MLdriftFallback, self).shutdown()

#***********************************************************************create SKILL***************************************************************************

def create_skill():
    return MLdriftFallback()
