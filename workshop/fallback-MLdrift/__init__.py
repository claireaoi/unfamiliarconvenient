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

#***********************************************************************INITIALIZATION***************************************************************************

from mycroft.skills.core import FallbackSkill
import random
#Parameters for the ML Drift
from . import parametersDrift
#For the ML Drift
import transformers
import torch
from transformers import GPT2Tokenizer, GPT2LMHeadModel

#For NLP
import nltk
from nltk import word_tokenize, sent_tokenize, pos_tag
from nltk.corpus import wordnet
from nltk.stem.wordnet import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()

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


#***********************************************************************MAIN CLASS***************************************************************************

class MLdriftFallback(FallbackSkill):
    """
        A Fallback skill running some ML drits with gpt2, and a mood.
    """
    def __init__(self):
        super(MLdriftFallback, self).__init__(name='MLdrift')
        #Parameters for the gpt2-drif, are uploaded from file parametersDrift.py
        self.mood=parametersDrift.currentMood
        self.lengthDrift=parametersDrift.lengthDrift
        self.nDrift=parametersDrift.nDrift
        self.randomizeMood=parametersDrift.randomizeMood
        self.moodSeeds=parametersDrift.moodSeeds
        self.probaMood=parametersDrift.probaMood
        self.temperature=parametersDrift.temperature
        self.repetition_penalty=parametersDrift.repetition_penalty
        self.moodySeed=""
        self.finetuned_ML_model=parametersDrift.finetuned_ML_model
        self.path_finetuned_ML_model=parametersDrift.path_finetuned_ML_model

        # Initialize machine learning
        self.tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        if self.finetuned_ML_model:
            self.model = GPT2LMHeadModel.from_pretrained(self.path_finetuned_ML_model) 
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
           Choose a moody seed to potentially add as contaxt for the gpt-2 Drift
        """
        if self.randomizeMood: #if randomize Mood chosen only
            #From the dictionnary probaMood randomly pick a mood following their probability
            self.mood=random.choices(population=list(self.probaMood.keys()), weights=list(self.probaMood.values()), k=1)[0]
        if self.mood in self.moodSeeds.keys():#in case mode entered wrong by human to avoid error
            self.moodySeed=random.choice(self.moodSeeds[self.mood])


    def updateParam(self):
        """
            Update the parameters from the file
        """
        self.mood=parametersDrift.currentMood
        self.lengthDrift=parametersDrift.lengthDrift
        self.nDrift=parametersDrift.nDrift
        self.randomizeMood=parametersDrift.randomizeMood
        self.moodSeeds=parametersDrift.moodSeeds
        self.probaMood=parametersDrift.probaMood
        self.temperature=parametersDrift.temperature
        self.repetition_penalty=parametersDrift.repetition_penalty
        self.moodySeed=""
        self.finetuned_ML_model=parametersDrift.finetuned_ML_model
        self.path_finetuned_ML_model=parametersDrift.path_finetuned_ML_model


    def handle_One(self, blabla):
        """
            One gpt-2 drift from the last blabla
        """
        #(0) Update the parameters from the file parametersDrift as they may have changed
        self.updateParam()

        #(1) Choose the mood and possible seed and add it after the blabla
        self.pickMoodySeed()
        blabla=blabla+ " " + self.moodySeed

        #(2) ML Drift according to parameters
        process = self.tokenizer.encode(blabla, return_tensors = "pt")
        generator = self.model.generate(process, max_length = self.lengthDrift, temperature = self.temperature, repetition_penalty = self.repetition_penalty)
        drift = self.tokenizer.decode(generator.tolist()[0])
        print(drift)

        #(3) Filter the Drift. Here a small filtering procedure. 
        #Yet you are free to change the parameters, make it your own, by pass this step (comment out)
        filtered_drift=filtering.filterText(drift, maxNonAlpha=15, maxRatio=0.3)
        
        #(4) Say the drift out loud
        self.speak(filtered_drift)

        return filtered_drift

    #The method that will be called to potentially handle the Utterance
    #The method implements logic to determine if the Utterance can be handled and shall output speech if itcan handle the query.
    #For now, will handle all query.
    def handle_MLdrift(self, message):
        """
            Several moody gpt-2 drifts from the last utterance
        """
        #(0) Get the human utterance
        utterance = message.data.get("utterance")
        #(1) Choose the mood and possible seed and add it
        loopCount=0
        blabla=utterance
        while loopCount<self.nDrift:
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
