from mycroft.skills.core import FallbackSkill

#Parameter AI Drift:
global lenghtML
lengthML=200

# Initialize machine learning
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
model = GPT2LMHeadModel.from_pretrained("./workshop/models/gpt-2") #>CHANGE PATH!

class AIdriftsFallback(FallbackSkill):
    """
        A Fallback skill running some ML drits with gpt2, and a mood.
    """
    def __init__(self):
        super(AIdriftsFallback, self).__init__(name='AIdrifts')

    def initialize(self):
        """
            Registers the fallback skill
            a FallbackSkill can register any number of fallback handlers

        """
        self.register_fallback(self.handle_AIdrift, 1)
        # Any other initialize code goes here


#The method that will be called to potentially handle the Utterance
#The method implements logic to determine if the Utterance can be handled and shall output speech if itcan handle the query.
    def handle_AIdrift(self, message):
        """
            gpt-2 drift from the last utterance
        """
        utterance = message.data.get("utterance")

        #ML part
        process = tokenizer.encode(utterance, return_tensors = "pt")
        generator = model.generate(process, max_length = lenghtML, temperature = 1.0, repetition_penalty = 2)
        drift = tokenizer.decode(generator.tolist()[0])

        # get keywords for current language
        #everything = self.dialog_renderer.render('everything') # everything is here 'everything'

        return True

#the Skill creator must make sure the skill handler is removed when the Skill is shutdown by the system.
    def shutdown(self):
        """
            Remove this skill from list of fallback skills.
        """
        self.remove_fallback(self.handle_fallback)
        super(AIdriftsFallback, self).shutdown()


def create_skill():
    return MeaningFallback()
