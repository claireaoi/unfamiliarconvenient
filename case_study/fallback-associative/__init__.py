# !/usr/local/bin/python3
# -*- coding: utf-8 -*-

######Description############
#
# FallBack Skill where...
#
######About############
#***********************************************************************LIBRARY IMPORT***************************************************************************

###IMPORT libraries
from mycroft.messagebus.message import Message
import numpy as np
import random
import re
import json
import time
import urllib.request
import os.path 
from os import path
import pathlib
import time


###IMPORT general
import operator
#For semantic similarity
from sematch.semantic.similarity import WordNetSimilarity
wns = WordNetSimilarity()
#For NLP and Wikipedia
import nltk
from nltk import word_tokenize, sent_tokenize, pos_tag
from nltk.corpus import words, wordnet
from nltk.stem.wordnet import WordNetLemmatizer
lemmatizer = WordNetLemmatizer()
import wikipediaapi
wikipedia = wikipediaapi.Wikipedia('en')


import requests
from bs4 import BeautifulSoup #More beautiful to see html
import urllib.parse
import lxml
import cssselect
import sys
import subprocess 
# from googleapiclient.discovery import build #METHOD 1 with BUILD and google_search function for previous scraper
from configparser import ConfigParser
import spacy
from string import punctuation
from googlesearch import search
import newspaper
from urllib.error import URLError


from mycroft.audio import wait_while_speaking
from transformers import GPT2Tokenizer, GPT2LMHeadModel
from mycroft.filesystem import FileSystemAccess

#from .utils import hatchSelf

#***********************************************************************PARAMETERS***************************************************************************

#####PARAMETERS WHICH EVOLVE#############
#TODO: EVOLVE both With size graph: nSelf=len(list(self.graph.keys()))
global threshold_similarity
threshold_similarity=0.1 # threshold when to consider 2 concepts as similar
global n_sim_concept
n_sim_concept=30 # when compare for words in self, this is a max number look for, else slow down too much
global FIRST_RUN
FIRST_RUN=False
######OTHER PARAMETERS TO BE TUNED##############
global TEMPERATURE
TEMPERATURE=1.0 #for ML model 
global TEMPERATURE_VARIANCE
TEMPERATURE_VARIANCE=0.3 #for ML model
global MIN_CHAR_SAVE
MIN_CHAR_SAVE=40
global SEED_LENGTH#BEWARE IN OPINION LENGTH TAKEN INTO ACCOUNT!
SEED_LENGTH=80#WOULD BE DOUBLED...
global OPINION_LENGTH
OPINION_LENGTH=500
global OPINION_LENGTH_VARIANCE
OPINION_LENGTH_VARIANCE=40
global MIN_CHAR_BIT
MIN_CHAR_BIT=80
global MIN_CHAR_BLOCK
MIN_CHAR_BLOCK=200
global BOUND_CHAR_EXTRACT
BOUND_CHAR_EXTRACT=400 
global BOUND_CHAR_EXTRACT_VARIANCE
BOUND_CHAR_EXTRACT_VARIANCE=100
global OPINION_TIMEOUT
OPINION_TIMEOUT=30
#################################FIXED PARAMETERS##############
global MAX_PICK_WORD
MAX_PICK_WORD=20 # When look for words bounded to a certain number to avoid too slow.
# Amounts to bound on found wikipediable word! When search from opinion, may be bigger.
global OWN_ML_MODEL
OWN_ML_MODEL=False
global path_ML_model
path_ML_model=str(pathlib.Path(__file__).parent.absolute())+'/gpt-2'
global SAVE_BLA
SAVE_BLA=True
global timeout_start
timeout_start=0

#TODO: SCRAP LESS
#TODO: cf ERROR file desktop with google api etc
#TODO: SCRAPER RETURN SMALL TEXTS?CHECK IT PARSER
EXCLUDED=['a', 'the', 'an', 'I', 'to', 'are', 'not', 'for', 'best','you', 'they', 'she', 'he', 'if', 'me', 'on', 'is', 'are', 'them', 'why', 'per', 'out', 'with', 'by'] #exclude these words to be looked upon

import shutil, os


#***********************************************************************PARAMETERS INITIALIZATION***************************************************************************

####LOAD CONFIG PARAMETERS
config = ConfigParser()
config.read(str(pathlib.Path(__file__).parent.absolute())+'/data/config.ini') 
my_api_key = config.get('auth', 'my_api_key')
my_cse_id = config.get('auth', 'my_cse_id')

#OTHER PARAMETERS
page = 2
start = (page - 1) * 10 + 1
min_char_bit=80
min_char_block=200
maximum_char=300

# there may be more elements you don't want, such as "style", etc. can check
blacklist = [
'[document]',
	'noscript',
	'header',
	'footer',
	'html',
	'meta',
	'head',
	'input',
	'script',
	'button',
    'cite',
	'style',
	'title',
	'form',
    'div',
    'img',
    'body',#, ok?
	'label',#, ok?
    'hgroup'#, ok?
	'section',# ok?
    'aside',#?
    'link',
    'svg',
    'span', # ok?
    'nav',
    'g',
    'picture',
    'figure',
    'figcaption',
    'main',
    'dd',#in a description list
    'dt',#in a description list
    'ul', #, unordered list
	'li'#, list
    #'strong', ? 
	#'ol',#, ordered list
	#'a',#, hyperlink to link one page to another?

]
#**********************************************************************PATH***************************************************************************

#FILE NAMES
#str(pathlib.Path(__file__).parent.absolute())+"/data/" 
HEARD_HUMAN_FILE='heard_human.txt'
DATA_FILE="selfdata.json"
GRAPH_FILE="graph.json"
HEARD_ONLINE_FILE="heard_online.txt"

#***********************************************************************MAIN CLASS***************************************************************************

#***********************************************************************INITIALIZATION MYCROFT***************************************************************************

from mycroft.skills.core import FallbackSkill

class AssociativeFallback(FallbackSkill):
    """
        A Fallback skill running some associative self quest, mapping the world
    """
    def __init__(self):
        super(AssociativeFallback, self).__init__()
        self.tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        self.log.info("Loading GPT2")
        if OWN_ML_MODEL:
            self.model=GPT2LMHeadModel.from_pretrained(path_ML_model)
        else:
            self.model=GPT2LMHeadModel.from_pretrained("gpt2") 
        self.log.info("GPT2 Loaded")
        self.data, self.graph=dict(),dict()
        self.load_self(FIRST_RUN, MAX_PICK_WORD, threshold_similarity)#loadSelf(FIRST_RUN, MAX_PICK_WORD, threshold_similarity)
        self.concepts, self.extracts =[], []
        self.human_opinion=None

        #TODO: USE SKILL SETTINGS ? skill settings are also a good option if you are saving non binary data, skill settings are basically a persistent dict saved as a .json file
        #skill settings are auto saved on skill shutdown, you can also force a save when you want ???

        #INIT and LOAD THE MESSAGE LIST
        self.MSG_ASKOPINION, self.MSG_COMETOGETHER, self.MSG_COMETOGETHER3, self.MSG_INTEREST, self.MSG_LETMETHINK, self.MSG_NOINTEREST, self.MSG_SHARE, self.MSG_NOTED=[], [], [],[], [], [],[], []
        self.load_messages() 

    def initialize(self):
        """
            Registers the fallback handler.
            The second Argument is the priority associated to the request.
            Lower is higher priority. But number 1-4 are bypassing other skills.
            Can register several handle
        """
        #self.reload_skill=False#avoid autoreload 
        self.register_fallback(self.handle_all, 6)#1 means always trigger it here
        #self.register_fallback(self.handle_associative, 1)#1 means always trigger it here
        # #self.register_fallback(self.handle_opinion, 2)#1 means always trigger it here
        #TODO: Have two different handle one for begin_interaction, other for opinion
        #self.register_fallback(self.handle_begin_interaction, 2)#1 means always trigger it here
        #self.register_fallback(self.handle_opinion, 3)#1 means always trigger it here


#***********************************************************************************************************************************************
#**********************************************************************MAIN INTERACTION BELOW*************************************************************************
#***********************************************************************************************************************************************


    def handle_all(self, message):
        """
            to handle the utterance. 
        """
        self.concepts,self.extracts=[], [] #reinitialise
        no_new_concept, if_added_concept=False, False

        #(0) Get the human utterance
        utterance = message.data.get("utterance")

        self.log.info("=======================================================")
        self.log.info("------------------INTERACT PART 1------------------")
        self.log.info("=======================================================")
        
        self.log.info("Associative skill, handler associative triggered by " + str(utterance))
        self.log.info(f'Caught Human Bla: "{utterance}"')
        human_bla =str(utterance)

        
         #(1) Chris update its lifetime, save it and ask the listener to be patient.
        self.log.info("=======================================================")
        self.log.info("Step 1--Preliminaries")
        self.log.info("=======================================================")
        self.speak(random.choice(self.MSG_LETMETHINK))
        self.data["lifetime"]+=1

        #(2) Chris extract one or two word from utterance
        self.log.info("=======================================================")
        self.log.info("Step 2- Extract words from human Bla") 
        self.log.info("=======================================================")
        ## OKWords, self.graph=extractWiki(human_bla, self.graph, self.data["memory"], MAX_PICK_WORD) #TODO ALTERNATIVE EXTRACTION?
        OKWords = self.extract(human_bla, MAX_PICK_WORD)
        self.log.info("Words extracted from human blabla with wordnet:"+",".join(OKWords))

        #(3) Pick one word from this list (if not empty), and look for similar concept in self
        self.log.info("=======================================================")
        self.log.info("Step 3--Look for a similar self-concept")
        self.log.info("=======================================================") 
        if OKWords==[]:
            no_new_concept=True
            self.log.info("Did not hear any new word interesting in human blabla.")
        else:
            new_concept=random.choice(OKWords)
            self.log.info("Picked a new concept:"+new_concept)
            if_added_concept, closer_concept=self.isSelf(new_concept, n_sim_concept,threshold_similarity)
            self.log.info("Closer concept in self-graph {}. If added it to self graph: {}".format(closer_concept, if_added_concept))
            self.data["memory"].append(new_concept)#update memory and save
            self.save_data_json(DATA_FILE, self.data, mode="w")
      
            if if_added_concept:
                self.concepts=[new_concept,closer_concept]
                self.save_data_json(GRAPH_FILE, self.graph, mode="w")
 
                self.speak(random.choice(self.MSG_INTEREST))
            else:
                self.log.info("Did not find a concept similar enough.")

        # has not find a new concept interesting him. Will Look about two self concepts online. or one ?
        if no_new_concept or (not if_added_concept):
            self.speak(random.choice(self.MSG_NOINTEREST))
            concepts=self.graph.keys()#his self-graph
            self.concepts=[random.choice(list(concepts)),random.choice(list(concepts))] #Or pick last?
            while self.concepts[0]==self.concepts[1]:#so not same#TODO and bound if no new concpt
                self.concepts[1]=random.choice(list(concepts))
        #self.concepts=["ripe", "silicon"]#TEMP

        #(4) ONLINE SURF AND SCRAP 
        self.log.info("=======================================================")
        self.log.info("Step 4--Surf online space and Scrap")
        self.log.info("=======================================================")
        #Form query and Scrap online space
        query= self.concepts[0]+ " "+ self.concepts[1]
        come_together=random.choice(self.MSG_COMETOGETHER)
        come_together=come_together.replace("xxx",self.concepts[0])
        come_together=come_together.replace("yyy",self.concepts[1])
        self.speak(come_together)
        self.log.info(come_together+ "Now surfing the online space...")
        nb_char_extract=BOUND_CHAR_EXTRACT+random.randint(-BOUND_CHAR_EXTRACT_VARIANCE, BOUND_CHAR_EXTRACT_VARIANCE)
        #scraped_data, extract_surf=["xxx yyy","test blabla"], "blue whales surfing USA" # JUST FOR TEST
        
        #reset time to avoid query timeout
        #self.bus.emit(message.response({"phrase":"Chill, I am scraping.", "skill_id":self.skill_id, "searching":True}))#searxch_phrase
        self.bus.emit(Message('question:query.response', data={"phrase":message.data.get('utterance'), "skill_id":self.skill_id, "searching":True}))
        scraped_data, extract_surf=self.surf_google(query, MIN_CHAR_BIT, MIN_CHAR_BLOCK, nb_char_extract) 

        time.sleep(3)  
        self.extracts=[extract_surf]

        # #save data scraped
        # self.log.info("Saving scraped data in"+HEARD_ONLINE_FILE)
        # self.save_data_file(HEARD_ONLINE_FILE, "\n".join(scraped_data), mode="a")

         # (5) Say a bit of the article about what found online
        self.log.info("=======================================================")
        self.log.info("step 5---Share what found:")
        self.log.info("=======================================================")
        self.log.info(self.extracts[0])
        self.speak(random.choice(self.MSG_SHARE))
        self.speak(self.extracts[0])
        #wait_while_speaking()

        self.log.info("=======================================================")
        self.log.info("------------------ASK FOR HUMAN OPINION------------------")
        self.log.info("=======================================================")
        self.bus.emit(Message('question:query.response', data={"phrase":message.data.get('utterance'), "skill_id":self.skill_id, "searching":True}))
        time.sleep(3)
        #human_opinion=self.get_response('ask.opinion', num_retries=0) # #random.choice(self.MSG_ASKOPINION)#TODO: RETURN OK ?  #data=None, validator=None,on_fail=None, num_retries=-1 CHECK PARAM GET RESPONSE
        human_opinion="Vytas is hot as a pepper"
        
        
        if human_opinion is not None:#do not need both, check new utterance not same than old one...
            self.log.info("=======================================================")
            self.log.info("============YOUHOUUUU CAUGHT HUMAN OPINION===========")
            self.log.info("=======================================================")
            human_opinion = str(human_opinion)
            self.log.info("Current human opinion saved:{}".format(human_opinion))
            self.speak(random.choice(self.MSG_NOTED))

            self.interact_part2(human_opinion, message)
        else:
            self.log.info("Seems human opinion is void.")

        

        return True #IF HANDLED...


    def interact_part2(self, human_bla, message):
        """
            End of an interaction loop with an human. 
            At the end of this loop, the VA is listening still for a possible other loop.
        """
        self.bus.emit(Message('question:query.response', data={"phrase":message.data.get('utterance'), "skill_id":self.skill_id, "searching":True}))

        self.log.info("=======================================================")
        self.log.info("PART 2 cool")
        self.log.info("=======================================================")
        self.log.info(f'Caught Human Bla: "{human_bla}"')

        self.speak("Thanks for this interaction")

        self.log.info("Thanks for this interaction.")
       
#***********************************************************************************************************************************************
#***********************************************************************************************************************************************
#***********************************************************************************************************************************************
#**********************************************************************SELF QUEST PROCEDURE *************************************************************************
#***********************************************************************************************************************************************
#***********************************************************************************************************************************************
#***********************************************************************************************************************************************

    def load_self(self, first_run, max_pick_word, threshold_similarity):
        """
            The VA loads his self.graph, memory, lifetime, as last saved. Or build it if first time.
        """
        if first_run:
            self.log.info("Hatching self in process...")
            self.graph, self.data, description=hatchSelf(max_pick_word, threshold_similarity)
        else:
            self.log.info("Loading self in process...")
            self.graph=self.load_data_json(GRAPH_FILE)
            self.data=self.load_data_json(DATA_FILE)
            self.log.info("I am here. My lifetime is {} interactions".format(self.data["lifetime"]))
        self.log.info("selfgraph {}".format(self.graph))
        self.log.info("selfgraph {}".format(self.graph.keys()))


    def semanticSimilarity(self, word1, word2):
        """
        Compute the semantic similarity between two words, as define by the library wnsm, and return score. Of course this is subjective. If word1 cmposed word: average similarity of its both elements.
        """
        score=0
        splitWord=word1.split()
            #Case of concepts made of several words
        if len(splitWord)>1:
            for elt in splitWord:
                score+=self.semanticSimilarity(elt, word2)
            score/=len(splitWord)
        else:#word1 has 1 component
            splitWord2=word2.split()
            if len(splitWord2)>1:#case word2 has 2 component or more
                for elt in splitWord2:#Else could take the max but would be non symmetic
                    score+=wns.word_similarity(word1, elt, 'li')
                score/=len(splitWord2)
            else:#case both concepts have only 1 word
                score=wns.word_similarity(word1, word2, 'li')
        #self.log.info('Similarity score between ' + word1 + ' and ' + word2 +": " + str(score))

        return score

    def isSelf(self, word, n_sim_concept, threshold_similarity):
        """
        Check if a word (not belonging to his self) is related to his self.graph.
        And pick a similar concept (any above the threshold of similarity).
        """
        nSelf=len(list(self.graph.keys()))
        #CASE in case graph becomes too big:
        indices=random.sample(range(0, nSelf), min(n_sim_concept, nSelf)) #Generate random list of indices where will look for
        self.graph[word]=[0,dict()]   #Add entry to dictionary for now
        ifConnected=False
        maxSim=0
        possible_simWord=[]
        simWord=""
        #Check similarity with other concepts in Self
        for i, wordSelf in enumerate(list(self.graph.keys())):
            if i in indices:
                similarity_score= self.semanticSimilarity(word,wordSelf)
                if similarity_score>threshold_similarity:
                    possible_simWord.append(wordSelf)
                    self.graph[word][1][wordSelf]=similarity_score#Add a connection if related enough.
                    self.graph[wordSelf][1][word]=similarity_score#Symmetric
                    ifConnected=True
                    #if similarity_score>maxSim:#IF WANT MAX SIMILARITY
                    #    maxSim=similarity_score
                    #    simWord=wordSelf
        
        #Conclude if related
        if not ifConnected: #Not related, ie no connection with SelfConcept was above a fixed threshold.
            del self.graph[word] #delete entry from SelfGraph therefore
        else: # if related
            #Pick a word above threshold similarity:
            simWord=random.choice(possible_simWord)
            self.graph[word][0]=maxSim*self.graph[simWord][0] #adjust the weight of the node
        return ifConnected, simWord


    def extract(self, blabla, max_pick_word):
        """
            Extract wordnet nouns (or proper noun) from a blabla, which are not on the memory, nor on the selGraph, nor in EXCLUDED
            TAKE ALSO WIKIPEDIA STILL
            Self Quest bounded to a maximum of max_pick_word to avoid too long wait. Beware, of found wikipediable word!
            Beware of upper or lower letters which can create conflicts.
            #TODO: Test Edge Cases and memorz
        
        """
        OKWordnet=[]
        wn_lemmas = set(wordnet.all_lemma_names())#TODO: SHALL LOAD IT ONLY ONCE???
        if len(blabla)==0: #empty
            print("No new words to grow from.")
        else:
            counter=0#count words added
            for word, pos in nltk.pos_tag(word_tokenize(blabla)):
                if counter<max_pick_word:#Stop once has enough words
                    if pos in ['NN', 'NNS','NNP']:
                        if not word.isupper():#To avoid turning words like AI lower case. Else turn to lower case. Ex: donald_trump
                            word=word.lower()
                        #TODO: Need Lemmatizer to avoid words which have same roots?
                        if ((word in wn_lemmas) or (wikipedia.page(word).exists())) and not (word in OKWordnet):
                            if word in self.graph.keys():#Word is there, augment its weight.
                                self.graph[word][0]=self.graph[word][0]*1.1
                            else: #TODO: Shall exclude memory ?
                                OKWordnet.append(word)
                                counter+=1
            #Special case of duo words for wikipedia, such as global_warming https://en.wikipedia.org/wiki/Global_warming
            #FOR THESE, use wikipedia!
            wordList=blabla.split()#then need word.strip(string.punctuation)
            token_list=nltk.pos_tag(word_tokenize(blabla))
            counter=0
            for token1, token2 in zip(token_list, token_list[1:]):#Consecutive token
                word1, pos1=token1
                word2, token2=token2
                if counter<max_pick_word and len(word1)>1 and len(word2)>1 and (word1 not in EXCLUDED) and (word2 not in EXCLUDED):#Stop once has enough words
                    if not word1.isupper(): #lower letter unless fully upper letter:check for proper noun
                        word1=word1.lower()
                    if not word2.isupper(): #lower letter unless fully upper letter
                        word2=word2.lower()
                    duo=word1+" "+word2
                    if wikipedia.page(duo).exists() and not (duo in OKWordnet):
                        if duo in self.graph.keys():
                            self.graph[duo][0]=self.graph[duo][0]*1.1
                        else:
                            OKWordnet.append(duo)
                            counter+=1
            print("New words to learn from", OKWordnet)
        return OKWordnet

#***********************************************************************************************************************************************
#***********************************************************************************************************************************************
#***********************************************************************************************************************************************
#**********************************************************************SCRAPER PROCEDURES**************************************************************************
#***********************************************************************************************************************************************
#***********************************************************************************************************************************************
#***********************************************************************************************************************************************

    def surf_google(self,query, min_char_bit, min_char_block, maximum_char):
        """
        Main procedure to scrap google result of a query: will scrap the urls first, then the texts of the articles, parse the text and choose
        one of these extracts.

        """
        #TODO: If none result satisfying criteria (length etc), relaunch further pages? OR TAKE SMALLER TEXT
        ###(0) Scrap data from Google Search and get urls
        print("=======================================================")
        print("Scraping Google results and get urls")
        #data = self.google_search(query, api_key=my_api_key, cse_id=my_cse_id) #METHOD API OLD ONE
        #urls = self.get_urls(data)
        urls=self.retrieve_google_url(query, num_links=8)
        #print(urls)
        ###(2) Extract texts part
        print("=======================================================")
        print("Extracting the texts")
        scraped_data=self.parse_article_vytas(urls) #self.parse_article(urls) #extract_text(urls, min_char_bit, min_char_block)#TEMPORARY
        #print(extracts)
        ###(3) Choose one extract
        print("=======================================================")
        print("Choosing one Extract")
        #TODO: Better choice there
        #TEMPORARZ OUT chosen_extract=self.choose_extract(scraped_data)
        #print(chosen_extract)
        ###(4) Cut extract
        print("=======================================================")
        print("Final Extract")
        #TEMPORARY OUT final_extract=self.cut_extract(chosen_extract, maximum_char)
        final_extract=self.cut_extract(scraped_data, maximum_char)
        print(final_extract)

        return scraped_data, final_extract


    def retrieve_google_url(self,query, num_links=8):
        # query search terms on google
        # tld: top level domain, in our case "google.com"
        # lang: search language
        # num: how many links we should obtain
        # stop: after how many links to stop (needed otherwise keeps going?!)
        # pause: if needing multiple results, put at least '2' (2s) to avoid being blocked)
        try:
            online_search = search(query, tld='com', lang='en', num=10, stop=num_links, pause=2)
        except URLError:
            pass
        website_urls = []
        for link in online_search:
            website_urls.append(link)
        # returns a list of links
        return website_urls


    # def google_search(self,search_term, api_key, cse_id, **kwargs):
    #     """
    #         Use Google Search API to get Google results over a query
    #         Old procedure!
    #     """
    #     service = build("customsearch", "v1", developerKey=api_key)
    #     res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
    #     return res #python dictionary ?

    # def get_urls(self,data):
    #     """
    #         Parse the data obtained from Google API to get the urls of these articles.
    #     """
    #     search_items = data.get("items")
    #     urls=[]
    #     for i, search_item in enumerate(search_items, start=1):
    #         title = search_item.get("title")
    #         link = search_item.get("link")
    #         urls.append(link)
    #     return urls



    def parse_article_vytas(self,urls):
        article_downloaded = False
        MIN_LENGTH=50
        count=1
        while not article_downloaded and count<10:
            try:
                # choose random url from list obtained from Google
                url = urls[random.randint(0, len(urls)-1)]
                # locate website
                article = newspaper.Article(url)
                # download website
                print('Downloading ' + url)
                article.download()
                # parse .html to normal text
                article.parse()
                #get text
                content=article.text
                if len(content)>MIN_LENGTH:
                    article_downloaded = True
                    self.log.info("WHAT FOUND ONLINE:"+content)
                count+=1
            except requests.exceptions.RequestException:
                print("Article download failed. Trying again")
                pass
        
        # analyze text with natural language processing
        #article.nlp()
        # return summary
        return content


    def parse_one_article(self,url):
        text=""
        try:
            # locate website
            article = newspaper.Article(url)
            # download website
            print('Downloading ' + url)
            article.download()
            article_downloaded = True
            # parse .html to normal text
            article.parse()
            # analyze text with natural language processing
            #article.nlp()
            print("========Article Scraped==========================")
            #print(article.text)
            text = article.text
        except Exception: #requests.exceptions.RequestException:
            #print("Article download failed.")
            pass
        return text

    def parse_article(self,urls):
        """
        New procedure to extract text from articles.
        """
        articles=[]
        count=0
        for url in urls:
            if count<4:#only 4 working links
                print("article scraped n{}".format(count))
                try:
                    article=self.parse_one_article(url)
                    if article is not None and not article=="":
                        articles.append(article)
                        count+=1
                except:
                    continue

        return articles


    def choose_extract(self,extracts):
        """
        Choose an extract of text among several. 
        First filter it by a "is cool" procedure, to select only nice texts. (todo, cf. below)
        Then, pick up randomly among the 3 longer cool extracts
        """
        cool_extracts=[]
        cool_length=[]
        for extract in extracts:
            #if isCool(extract):
            cool_extracts.append(extract)
            cool_length.append(len(extract))
        #Get 3 longer cool extracts
        nb_pick=min(3, len(cool_extracts))#Will pick 3 if nb cool exctracts >=3
        longer_extracts=sorted(zip(cool_length, cool_extracts), reverse=True)[:nb_pick]#as sorted by default order from first argument when tuple
        #Pick one randomly
        chosen_extract=random.choice(longer_extracts)
        return chosen_extract[1]#text part (first element is score)

    def isCool(self,text):
        """
        Has to try to judge if a text extract is cool.
        #TODO: Do this procedure. if too much space between lines, bad, paragraph condensed are better or if too many special characters may be bad etc.
        #notably if too much of : </div>
        #For now temporary: count <> and if bigger than 20, say not cool. But need to implement filter_html first
        """
        #nb_bad_stuff=text.count("<")
        return True #bool(nb_bad_stuff<4)#CHECK THIS

    def crop_unfinished_sentence(self, text):
        """
        Remove last unfinished bit from text. 
        """
        #TODO: better?
        #SELECT FROM THE RIGHT rindex s[s.rindex('-')+1:]  
        stuff= re.split(r'(?<=[^A-Z].[.!?]) +(?=[A-Z])', text)

        new_text=""
        for i in range(len(stuff)):
            if i<len(stuff)-1:
                new_text+= " " + stuff[i]
            elif len(stuff[i])>0 and (stuff[i][-1] in [".", ":", "?", "!", ";"]):#only if last character ounctuation keep
                new_text+= " " + stuff[i]

        return new_text

    def cut_extract(self, extract, maximum_char):
        """
        Cut a text extract if above a certain nb character
        """
        bound_extract=extract[:maximum_char]
        return  self.crop_unfinished_sentence(bound_extract)

#***********************************************************************************************************************************************
#***********************************************************************************************************************************************
#***********************************************************************************************************************************************
#**********************************************************************LOAD PROCEDURES**************************************************************************
#***********************************************************************************************************************************************
#***********************************************************************************************************************************************
#***********************************************************************************************************************************************

    def load_messages(self):
        self.log.info("Loading messages")
        path_folder=str(pathlib.Path(__file__).parent.absolute())+'/messages/'
        self.log.info(str(pathlib.Path(__file__).parent.absolute())+'/messages/message_askopinion.txt')
        self.MSG_ASKOPINION=self.load_data_txt("message_askopinion.txt", path_folder=path_folder)
        self.MSG_COMETOGETHER=self.load_data_txt("message_cometogether.txt",path_folder=path_folder)
        self.MSG_COMETOGETHER3=self.load_data_txt("message_cometogether3.txt", path_folder=path_folder)
        self.MSG_INTEREST=self.load_data_txt("message_interest.txt",path_folder=path_folder)
        self.MSG_NOINTEREST=self.load_data_txt("message_nointerest.txt", path_folder=path_folder)
        self.MSG_SHARE=self.load_data_txt("message_share.txt", path_folder=path_folder)
        self.MSG_NOTED=self.load_data_txt("message_noted.txt", path_folder=path_folder)
        self.MSG_LETMETHINK=self.load_data_txt("message_letmethink.txt", path_folder=path_folder)


    def load_data_json(self, filename):
        folder_skill="/home/unfamiliarconvenient/.mycroft/fallback-associative/"
        with open(folder_skill+filename) as json_file:
            data = json.load(json_file)
        return data

    def load_data_txt(self, filename, path_folder="", mode="r"):
        """
        for messages in skill, load txt
        """
        with open(path_folder+filename,  mode=mode) as f:
            data = f.readlines()
        return data

    def save_data_file(self, filename, data, mode="w"):
        try:
            file_system = FileSystemAccess(str(self.skill_id))
            file = file_system.open(filename, mode)
            file.write(data)
            file.close()
            return True
        except Exception:#as e
            self.log.info("ERROR: could not save skill file " + filename)
            #LOG.warning("could not save skill file " + filename)
            #LOG.error(e)
            return False


    def save_data_json(self, filename, data, mode="w"):
        try:
            file_system = FileSystemAccess(str(self.skill_id))
            file = file_system.open(filename, mode)
            json.dump(data, file)
            file.close()
            return True
        except Exception:
            self.log.info("ERROR: could not save skill file " + filename)
            return False



#**************************************************************************************************************************************************
#**************************************************************************************************************************************************
#**************************************************GPT2  GENERATION***************************************************************************************
#**************************************************************************************************************************************************
#************************************************************************************************************************************



    def gpt2_text_generation(self, context, length_output, temperature): 
        """
            One ML drift with gpt-2, with a context. Printed and said by VA.
            With some stochasticity
        """
        process = self.tokenizer.encode(context, return_tensors = "pt")
        generator = self.model.generate(process, max_length = length_output, temperature= temperature, repetition_penalty = 2.0, do_sample=True, top_k=20)
        drift = self.tokenizer.decode(generator.tolist()[0])
        
        return drift

#**************************************************************************************************************************************************
#**************************************************************************************************************************************************
#**************#**************************************************************************************************************************************************
#**************************************************************************************************************************************************
#************************************************************************************************************************************


    #the Skill creator must make sure the skill handler is removed when the Skill is shutdown by the system.
    def shutdown(self):
        """
            Remove this skill from list of fallback skills.
        """
        self.remove_fallback(self.handle_all)
        #self.remove_fallback(self.handle_opinion)
        #self.remove_fallback(self.handle_associative)
        #self.remove_fallback(self.handle_beginning)
        super(AssociativeFallback, self).shutdown()




#**************************************************************************************************************************************************
#**************************************************************************************************************************************************
#**************************************************************************************************************************************************
#***********************************************************************create SKILL***************************************************************************

def create_skill():
    return AssociativeFallback()

#**************************************************************************************************************************************************
#**************************************************************************************************************************************************
#************************************************************************************************************************************
#**************************************************************************************************************************************************
#**************************************************************************************************************************************************
#**********************************************************************ARCHIVE*************************************************************************


    # def load_data_file(self, filename, mode="r"):
    #     file_system = FileSystemAccess(str(self.skill_id))
    #     file = file_system.open(filename, mode)
    #     data = file.read()
    #     file.close()
    #     return data

    # def load_data_lines(self, filename, mode="r"):
    #     file_system = FileSystemAccess(str(self.skill_id))
    #     file = file_system.open(filename, mode)
    #     data = [line.rstrip('\n') for line in file]
    #     file.close()
    #     return data
