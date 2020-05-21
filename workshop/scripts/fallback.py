



class AIdriftsFallback(FallbackSkill):
    """
        A Fallback skill running some ML drits with gpt2, and a mood.
    """
    def __init__(self):
        super(AIdriftsFallback, self).__init__(name='AIdrifts')


     def initialize(self):
         """
             Registers the fallback handler
             a FallbackSkill can register any number of fallback handlers
         """
         self.register_fallback(self.handle_fallback, 10)


#The method that will be called to potentially handle the Utterance
#The method implements logic to determine if the Utterance can be handled and shall output speech if itcan handle the query.
     def handle_fallback(self, message):
        """
            Answers question about the meaning of life, the universe
            and everything.
        """
        utterance = message.data.get("utterance")
        if 'what' in utterance
            and 'meaning' in utterance
            and ('life' in utterance
                or 'universe' in utterance
                or 'everything' in utterance):
            self.speak('42')
            return True
        else:
            return False

#the Skill creator must make sure the skill handler is removed when the Skill is shutdown by the system.
    def shutdown(self):
        """
            Remove this skill from list of fallback skills.
        """
        self.remove_fallback(self.handle_fallback)
        super(MeaningFallback, self).shutdown()
