# !/usr/local/bin/python3
# -*- coding: utf-8 -*-


######About############
#
#

#***********************************************************************INITIALIZATION***************************************************************************

from mycroft.skills.core import FallbackSkill
from mycroft.skills.audioservice import AudioService # for audio

import random


#***********************************************************************PRELIMINARIES***************************************************************************



#***********************************************************************MAIN CLASS***************************************************************************

class whistleFallback(FallbackSkill):
    """
        A Fallback skill running some ML drits with gpt2, and a mode.
    """
    def __init__(self):
        super(whistleFallback, self).__init__(name='whistle')


    def initialize(self):
        """
            Registers the fallback handler.
            The second Argument is the priority associated to the request.
            Lower is higher priority. But number 1-4 are bypassing other skills.
        """
        self.audio_service = AudioService(self.bus) #instantiate an AudioService object:
        self.register_fallback(self.handle_play, 6)

    #The method that will be called to potentially handle the Utterance
    #The method implements logic to determine if the Utterance can be handled and shall output speech if itcan handle the query.
    #For now, will handle all query.
    def handle_play(self, message):
        """
            Answer by sounds
        """
        #(0) Get the human utterance
        utterance = message.data.get("utterance")
        #(1) Play a track. (after can randomize or make it dependent utterance>>)
        self.audio_service.play('./data/birds.wav') #'file:///path/to/my/track.mp3') #wav work or mp3 ?
        #Play a list of tracks
        #self.audio_service.play(['file:///path/to/my/track.mp3', 'http://tracks-online.com/my/track.mp3'])


        return True

    #the Skill creator must make sure the skill handler is removed when the Skill is shutdown by the system.
    def shutdown(self):
        """
            Remove this skill from list of fallback skills.
        """
        self.remove_fallback(self.handle_play)
        super(WhistleFallback, self).shutdown()

#***********************************************************************create SKILL***************************************************************************

def create_skill():
    return WhistleFallback()
