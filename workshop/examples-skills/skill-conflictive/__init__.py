

from mycroft import MycroftSkill

class ConflictiveSkill(MycroftSkill):
    def __init__(self):
        #MycroftSkill.__init__(self)
        super(ConflictiveSkill, self).__init__(name='Conflictive') # if need register name

    def initialize(self):
        self.register_intent_file('what.is.intent', self.handle_what_is)
        self.register_intent_file('do.you.like.intent', self.handle_do_you_like)

    def handle_what_is(self, message):
        self.speak('A tomato is a big red thing')

    def handle_do_you_like(self, message):
        tomato_type = message.data.get('type')
        if tomato_type is not None:
            self.speak("Well, I'm not sure if I like " + tomato_type + " tomatoes.")
        else:
            self.speak('Of course I like tomatoes!')