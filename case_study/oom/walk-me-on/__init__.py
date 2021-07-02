########################  ABOUT THIS SKILL

#TODO: CHANGE THIS PATH : put where graph file is...
GRAPH_PATH = "/home/unfamiliarconvenient/.mycroft/fallback-associative/graph.json"
#str(pathlib.Path(__file__).parent.absolute()) #may use path lib...

PATH_WORDS=".../walk-me-on/data/" #Modify when...

######################## INITIALISATION

###Mycroft Imports
from adapt.intent import IntentBuilder # adapt intent parser
from mycroft import MycroftSkill, intent_handler #padatious intent parser
from mycroft.skills.audioservice import AudioService
from mycroft.audio import wait_while_speaking
###Other imports
from random import randint
from time import sleep
import pathlib
import re
import json
import random
import fire
import nltk
from nltk.corpus import wordnet
import numpy as np

#from pattern3.text.en import conjugate, lemma, lexeme, PRESENT, SG #pip3 install pattern3 !
#TODO find replacement of this libto conjugate verb

#----------------------------------------------------------------
#----------------------PRELIMINARIES PROCEDURES  ------------------
#----------------------------------------------------------------

def pick_structure(structures):
    structure_=random.choice(structures)
    structure=structure_.split("\n\n")
    final_structure=[]
    for el in structure:
        lines=el.split("\n")
        line=random.choice(lines)
        final_structure.append(line)

    return final_structure
#----------------------------------------------------------------


class WalkMeOnSkill(MycroftSkill):
    def __init__(self):
        """ The __init__ method is called when the Skill is first constructed.
        It is often used to declare variables or perform setup actions, however
        it cannot utilise MycroftSkill methods as the class does not yet exist.
        """
        super(WalkMeOnSkill, self).__init__(name='Walk Me On Skill')

    def initialize(self):
        """ Perform any final setup needed for the skill here.
        This function is invoked after the skill is fully constructed and
        registered with the system. Intents will be registered and Skill
        settings will be available."""
        # my_setting = self.settings.get('my_setting') #not needed yet

        #load self graph
        with open(GRAPH_PATH) as json_file:
            self.graph = json.load(json_file)
        #loads words dictionaries
        self.wordsDic = {} #Dictionnary of list words
        filenames=["A", "Ad1", "Ad2", "Ad3", "V", "Vt", "V2", "V+", "P", "Pf", "P0", "PR0", "PR0a", "PR1a", "PR1", "N", "N2", "Nf","Nfa", "Na", "Aa", "Va", "Nfa", "ism", "Duo", "Nf", "Ma", "S", "Sc", "ESS", "ASA", "ABL", "QU",  "Tion", "Duoa"]
        for filename in filenames:
            self.wordsDic[filename] = [line.rstrip('\n') for line in open(PATH_WORDS+filename+'.txt')]
        #load structures
        with open(PATH_WORDS+'haiku.txt', "r") as f:
            self.structures  = f.read().split(">>>") #LIST for each Haiku

    #What happen when detect like Intent. PADATIOUS: use .intent file
    @intent_handler('classic.intent')
    def handle_walk_intent(self, message):
        self.log.info("=======================================================")
        self.log.info("==========step 0: Walk Me On caught Human Utterance=======")
        self.log.info("=======================================================")
        # 0-- extract what human asked 
        human_said = str(message.data.get("utterance"))
        self.log.info(f'Human said {human_said}')

        self.log.info("=======================================================")
        self.log.info("==========step 1: Extract 3 keywords from self =======")
        self.log.info("=======================================================")
        words=random.choice(list(self.graph.keys(), 3))
        self.log.info("Picked some words about self", words)

        self.log.info("=======================================================")
        self.log.info("==========step 2: Choose an Haiku structure=======")
        self.log.info("=======================================================")
        structure = pick_structure(self.structures)
        self.log.info("Picked a structure", structure)

        self.log.info("=======================================================")
        self.log.info("==========step 3: Generate Haiku=======")
        self.log.info("=======================================================")
        haiku=""
        for line in structure:
            bla, seeds=self.read(line, seeds)#return non used seeds
            haiku+=bla + "\n"
        self.log.info("Generated Haiku", haiku)
    
        self.log.info("=======================================================")
        self.log.info("==========step 4: Clean &Share it =======")
        self.log.info("=======================================================")
        haiku= re.sub("\s\s+" , " ", haiku) #remove multiple blanks
        self.log.info("Formatted Haiku", haiku)
        self.speak(haiku)
    

    def read(self, line, seeds=[]):
        sentence=""
        things=line.split(" ")
        for thg in things:
            elements=thg.split("//")#// means an or
            element=random.choice(elements)
            units=element.split("/")#/ means an AND
            for unit in units:
                bla, seeds=self.readUnit(unit.strip(), seeds)
                sentence+=" "+ bla.strip()#Strip to remove if spaces
        return sentence, seeds

    def readUnit(self, unit, seeds=[]):
        #-----may use seeds----
        if unit in ["N","N2", "Ns", "N2s", "Na"]:
            if len(seeds)>0:
                bla=seeds[0]
                seeds.pop(0)
            else:
                bla, w=self.read(random.choice(self.wordsDic[unit.replace("s","")]))
        #---------composite structures
        elif unit=="N2p" or unit=="Np":#Here dont caree about plural !
            bla, seeds=self.read("N//Na//Pf/Na", seeds)
        elif unit=="X" or unit=="Xs" or unit=="Xp":
            bla, seeds=self.read("Duo//Duoa//N//Na//Na/N2//N/and/N//N2/P0/N//Pf/Na//Na/P0/N//A/A/N//A/N//Ns/N2//N2//N//A/N//Ns/N2//N2//N//A/N//Ns/N2//N//A/N//Ns/N2//N//A/N//Ns/N2//N//A/N//Ns/N2//N//A/N//Ns/N2//N//A/N//Ns/N2//N//A/N//Ns/N2//A/N2//A/N2//A/N2", seeds)
        elif unit=="X+":#to add to "the X ""...Ex: which...
            bla, seeds=self.read("whose/Na/W0//which/W//better/Vtd/that/W0//than/Vtd//which/have/been/PR1a//which/have/been/PR1//which/W0//the/X/PR1//thought/as/Nfa//we/are/trying/to/Vt//that/W0//that/we/allow/to/W0//we/are/Vtg//that/Ad2/W0//that/V+//that/have/become/A//that/do/not/W0//that/you/should/not/Vt", seeds)
        elif unit=="Y":
            bla, seeds=self.read("Y0//Y0//Y0//Y0//Y0/PR1//Y0/PR1a//all/what/W//the/X/X+//everyone/X+//anything/X+//each/X/X+//X/Wg", seeds)
        elif unit=="Y0":
            bla, seeds=self.read("Nf//Nfa//Nf//Nfa//Nfa//Nfa//the/A/N//the/Na/P/N//the/Na/P/X//the/Ns/N2//the/A/Ns/N2//the/X/P/X//the/X/P0/X//the/Vg/X//X/,/X/and/X//both/X/and/X//the/X/that/W0", seeds)
        elif unit=="W":
            bla, seeds=self.read("W0//W0//W0//W0//W0//V+//V+//V+//could/W0//should/W0//would/W0//could/V+//Ad2/W0//Ad2/W0", seeds)
        elif unit=="W0":
            bla, seeds=self.read("V//V//Vt/X//Va//Va//V2//Vt/Y//Vt/Nfa", seeds)
        elif unit=="WA":
            bla, seeds=self.read("Ad2/V//Ad2/Vt/X//V/Ad3//Vt/X/Ad3", seeds)
        elif unit=="Wd":
            bla, seeds=self.read("Vd//Vd//Vtd/X//Vad//Vad//V2d//Vtd/Y//Vtd/Nfa", seeds)
        elif unit=="Wg":
            bla, seeds=self.read("Vg//Vg//Vtg/X//Vag//Vag//V2g//Vtg/Y//Vtg/Nfa", seeds)
        elif unit=="XWg":#NEED ?
            bla, seeds=self.read("X/Wg", seeds)
        elif unit=="PRO":
            bla, seeds=self.read("S/V//S/Vt/X//X/V//N/Vt/X//S/V/P0/X", seeds)
    
        #---not affecting seeds
        elif unit=="A":
            bla, w=self.read("A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0//A0/A0//A0/A0//A0/A0/A0//Ad2/A0//A0//Ad2/A0//Ad2/A0//A0/A0//still/A0//A0/yet/A0//yet/A0//soon/A0//somehow/A0//already/A0")    
        elif unit=="A0":
            bla, w=self.read(random.choice(self.wordsDic["A"]))
        elif unit=="PR10":
            bla, w=self.read(random.choice(self.wordsDic["PR1"]))
        elif unit=="PR1":
            bla, w=self.read("PR10//PR10//PR10//PR10//PR10//PR10//Ad1/PR10//Ad2/PR10//Ad2/PR10")
        #--------verbs
        elif unit=="Vd" or unit=="Vad" or unit=="Vtd" or unit=="V2d":
            verb=random.choice(self.wordsDic[unit.replace("d", "")]).split(" ")
            bla=verb
            #TODO: This library need Python3.6 or 2.7... find replacement...
            # bla=lexeme(verb[0])[4] #past
            # if len(verb)>0:
            #     bla+=' '.join(verb[1:])
        elif unit=="Vag" or unit=="Vg" or unit=="Vtg" or  unit=="V2g":
            verb=random.choice(self.wordsDic[unit.replace("g", "")]).split(" ")
            bla=verb
            #TODO: This library need Python3.6 or 2.7...
            ## bla=lexeme(verb[0])[2] #present participe
            # #conjugate(verb[0], tense = "present",  person = 3,  number = "singular",  mood = "indicative", aspect = "progressive",negated = False)
            # if len(verb)>0:
            #     bla+=' '.join(verb[1:])
        #----remaining stuff
        elif unit in self.wordsDic.keys():
            bla, w=self.read(random.choice(self.wordsDic[unit]))

        else:#mean just a word
            bla=unit

        return bla, seeds


######*****************************************************************************************
######*********************** SKILL ***********************************************
######*****************************************************************************************

    def stop(self):
        pass


def create_skill():
    return WalkMeOnSkill()


