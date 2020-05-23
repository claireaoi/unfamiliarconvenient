from mycroft.skills.core import FallbackSkill
import random
#Parameter for the ML Drift
import parametersDrift

#For the ML Drift
import transformers
import torch
from transformers import GPT2Tokenizer, GPT2LMHeadModel
# Initialize machine learning
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("./workshop/models/gpt-2") #>CHANGE PATH!

class MLdriftFallback(FallbackSkill):
    """
        A Fallback skill running some ML drits with gpt2, and a mood.
    """
    def __init__(self):
        super(MLdriftFallback, self).__init__(name='MLdrift')
        #Parameters of the gpt2-drift taken from file
        self.mood=parametersDrift.currentMood
        self.lengthDrift=parametersDrift.lengthDrift
        self.nDrift=parametersDrift.nDrift
        self.randomizeMood=parametersDrift.randomizeMood
        self.moodSeeds=parametersDrift.moodSeeds
        self.probaMood=parametersDrift.probaMood
        self.moodySeed=""
        self.temperature=parametersDrift.temperature
        self.repetition_penalty=parametersDrift.repetition_penalty


    def initialize(self):
        """
            Registers the fallback skill
            a FallbackSkill can register any number of fallback handlers

        """
        self.register_fallback(self.handle_MLdrift, 1)
        # Any other initialize code goes here

   
    def pickMoodySeed(self):
        """
           Choose a moody seed to potentially add as contaxt for the gpt-2 Drift
        """
        if self.randomizeMood: #if randomize Mood chosen only
            #From the dictionnary probaMood randomly pick a mood following their probability
            self.mood=random.choices(population=list(self.probaMood.keys()), weights=list(self.probaMood.values()), k=1)[0]
        if self.mood in self.moodSeeds.keys():#in case mode entered wrong by human to avoid error
            self.moodySeed=random.choice(self.moodSeeds[self.mood])


    def handle_One(self, blabla):
        """
            One gpt-2 drift from the last blabla
        """
        #(1) Choose the mood and possible seed and add it
        self.pickMoodySeed()
        blabla=moodySeed+ " " + utterance

        #(2) ML Drift according to parameters
        process = tokenizer.encode(blabla, return_tensors = "pt")
        generator = model.generate(process, max_length = self.lenghtDrift, temperature = self.temperature, repetition_penalty = self.repetition_penalty)
        drift = tokenizer.decode(generator.tolist()[0])
        print(drift)

        #(3) Say the bla out loud
        self.speak(drift)

        return drift

#The method that will be called to potentially handle the Utterance
#The method implements logic to determine if the Utterance can be handled and shall output speech if itcan handle the query.
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
            loopCount++
            print("Drift n° {loopCount}")
            blabla=self.handle_One(blabla) #Only keep last part as context else too big?


        return True



#the Skill creator must make sure the skill handler is removed when the Skill is shutdown by the system.
    def shutdown(self):
        """
            Remove this skill from list of fallback skills.
        """
        self.remove_fallback(self.handle_MLdrift)
        super(MLdriftFallback, self).shutdown()


def create_skill():
    return MLdriftFallback()
