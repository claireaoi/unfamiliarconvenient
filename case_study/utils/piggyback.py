#!/usr/bin/env python3

# Vytas Jankauskas 2021
# Unfamiliar Convenient Project, in collaboration with Claire Glanois
# Project page: https://vjnks.com/works/unfamiliar-convenient-project-in-progress-46
# Repo: https://github.com/modern-online/Unfamiliar-Convenient/tree/main/ITP-class

# The script runs on Mycroft framework and requires Mycroft's virtual environment to work
# More on Mycroft: https://github.com/MycroftAI
# Primary module to communicate via Mycroft: mycroft-message-bus
# Additional modules used: googlesearch, newspaper, nltk, spacy

# This script was developed as one of educational templates into using Mycroft
# as part of 2021 NYU ITP spring semester class.

# Apparently some other version of this script is used by Claire in a project
# she's working on with some peeps. Hence this template should be taken as
# a departure point and not a final result.

"""
Contextual plug-in script for Mycroft voice assistant. 
When a human utterance is detected and resolved by Mycroft,
this 'plug-in' forces additional 'contextualisation' 
in a domain of choice. 

For example, if you ask Mycroft to look up 'Planet Jupiter',
after providing the original answer it will provide additional
information within a context (popcorn by default).

This is done by:
1) Capturing human utterance via Mycroft before adequate skills
get triggered,
2) Extracting keywords from utterace via NLP, 
3) Summing extracted keywords with chosen context keywords 
4) Executing a Google search and retrieving links (5 by default),
5) Picking a random link, downloading its contents (HTML)
6) Parsing the page, extracting summary with the help of NLP
7) Sending (emitting) text to Mycroft after the original inquiry
has been answered
"""

from mycroft_bus_client import MessageBusClient, Message
import spacy
from string import punctuation
from googlesearch import search
import newspaper
import nltk
import requests
from random import randint
from time import sleep
from urllib.error import URLError

# SEARCH CONTEXT / CHOOSE ANYTHING
search_context = "popcorn"

# import Message Bus client to communicate with Mycroft's guts
print("Setting up connection to Mycroft client")
client = MessageBusClient()

# load machine learning model for keyword extraction
# (first download the model! : python3 -m spacy download en_core_web_sm)
print("Importing machine learning model")
keyworder = spacy.load("en_core_web_sm")

print("Ready!")


def extract_keywords(input):
    # we're looking for proper nouns, nouns, and adjectives
    pos_tag = ['PROPN', 'NOUN', 'ADJ']
    # tokenize and store input
    phrase = keyworder(input.lower())
    keywords = []
    # for each tokenized word
    for token in phrase:
        # if word is a proper noun, noun, or adjective;
        if token.pos_ in pos_tag:
            # and if NOT a stop word or NOT punctuation
            if token.text not in keyworder.Defaults.stop_words or token.text not in punctuation:
                keywords.append(token.text)
    # convert list back to string
    key_string = " ".join(keywords)

    return key_string


def retrieve_google_url(query):
    # query search terms on google
    # tld: top level domain, in our case "google.com"
    # lang: search language
    # num: how many links we should obtain
    # stop: after how many links to stop (needed otherwise keeps going?!)
    # pause: if needing multiple results, put at least '2' (2s) to avoid being blocked)
    try:
        online_search = search(query, tld='com',
                               lang='en', num=5, stop=3, pause=2)
    except URLError:
        pass
    website_urls = []
    for link in online_search:
        website_urls.append(link)

    # returns a list of links
    return website_urls


def parse_article(urls):
    article_downloaded = False
    while not article_downloaded:
        try:
            # choose random url from list obtained from Google
            url = urls[randint(0, len(urls)-1)]
            # locate website
            article = newspaper.Article(url)
            # download website
            print('Downloading ' + url)
            article.download()
            article_downloaded = True
        except requests.exceptions.RequestException:
            print("Article download failed. Trying again")
            article_downloaded = False
            pass
    # parse .html to normal text
    article.parse()
    # analyze text with natural language processing
    article.nlp()
    # return summary
    return article.summary

# =============================================================================
# Processes original human message and gives extra info within specific context
# =============================================================================


def nobody_asked_this(message):
    # step 1: extract what human asked for out of a JSON object
    human_said = message.data.get('utterances')[0]
    print(f'Human said {human_said}')

    # step 2: extract keywords from the phrase and add search_context
    search_keys = extract_keywords(human_said) + " " + search_context
    print("Search query: " + search_keys)

    # step 3: retrieve page url from Google
    urls = retrieve_google_url(search_keys)

    # step 4: parse contents of the page
    supplementary_info = parse_article(urls)
    print(supplementary_info + '\n')

    # step 5: speak out supplementary info via Mycroft
    sleep(3)  # this is optional just to give time for mycroft to retrieve original results before supplementary ones
    client.emit(Message('speak', data={'utterance': supplementary_info}))


# waits for messages from Mycroft via websocket
client.on('recognizer_loop:utterance', nobody_asked_this)

# basically runs this script in a loop
client.run_forever()
