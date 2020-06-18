###Whistle Test Skill
from adapt.intent import IntentBuilder # adapt intent parser
from mycroft import MycroftSkill, intent_handler #padatious intent parser
from mycroft.skills.audioservice import AudioService


class WhistleSkill(MycroftSkill):
    def __init__(self):
        """ The __init__ method is called when the Skill is first constructed.
        It is often used to declare variables or perform setup actions, however
        it cannot utilise MycroftSkill methods as the class does not yet exist.
        """
        super().__init__()
        #self.learning = True 

    def initialize(self):
        """ Perform any final setup needed for the skill here.
        This function is invoked after the skill is fully constructed and
        registered with the system. Intents will be registered and Skill
        settings will be available."""
        self.audio_service = AudioService(self.bus) #instantiate an AudioService object:
        my_setting = self.settings.get('my_setting')

    #What happen when detect like Intent. PADATIOUS: use .intent file
    @intent_handler('play.intent')
    def handle_how_are_you_intent(self, message):
        """ This is a Padatious intent handler.
        It is triggered using a list of sample phrases."""
        word = message.data.get('thing') #Catch what has been said for thing. Can use it later
        #(1) Play a track. (after can randomize or make it dependent utterance>>)
        self.audio_service.play('./data/birds.wav') #'file:///path/to/my/track.mp3') #wav work or mp3 ?
        #self.speak("Why an algorithm should have an opinion on"+ word) #here do not use .dialog, speak directly
        #self.speak_dialog("play")
        #Play a list of tracks
        #self.audio_service.play(['file:///path/to/my/track.mp3', 'http://tracks-online.com/my/track.mp3'])

    def stop(self):
        pass


def create_skill():
    return WhistleSkill()
