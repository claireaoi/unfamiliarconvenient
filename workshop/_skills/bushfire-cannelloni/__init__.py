###Bushfire and cannelloni Test Skill

#This is a basic Hello Word Skill that takes an _Utterance_ from the user and provides a voice response - a _Dialog_. 
#This Skill demonstrates the basic directory and file structure of a Mycroft Skill, and is a good first Skill to study 
#if you are interested in developing Skills for the Mycroft ecosystem.

from adapt.intent import IntentBuilder # adapt intent parser
from mycroft import MycroftSkill, intent_handler #padatious intent parser

class HelloWorldSkill(MycroftSkill):
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
        my_setting = self.settings.get('my_setting')


    #What happen when detect hell Intent. PADATIOUS: use .intent file
    @intent_handler('hell.intent')
    def handle_how_are_you_intent(self, message):
        """ This is a Padatious intent handler.
        It is triggered using a list of sample phrases."""
        self.speak_dialog("what.the.hell")

    #What happen when detect like Intent. PADATIOUS: use .intent file
    @intent_handler('like.intent')
    def handle_how_are_you_intent(self, message):
        """ This is a Padatious intent handler.
        It is triggered using a list of sample phrases."""
        word = message.data.get('thing') #Catch what has been said for thing
        self.speak("Why an algorithm should have an opinion on"+ word) #here do not use .dialog, speak directly

     #What happen when detect HelloWorld Intent. ADAPT Intent handler: require file in .voc
    @intent_handler(IntentBuilder('HelloWorldIntent').require('HelloWorldKeyword'))# need this line to tell Mycroft to which intent the function below correspond
    def handle_hello_world_intent(self, message): #what is actually doing
        """ Skills can log useful information. These will appear in the CLI and
        the skills.log file."""
        self.log.info("There are five types of log messages: "  #log info can add
                      "info, debug, warning, error, and exception.")
        self.speak_dialog("hello.world")


    def stop(self):
        pass


def create_skill():
    return HelloWorldSkill()
