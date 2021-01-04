
my_api_key = "AIzaSyDhfG5n_c_M1sdasbA3O4x8D8fxeZ3FTs4"
my_cse_id = "6b1aa6117d1440ce9" #SEARCH ENGINE ID
query1="Coffee"
page = 2
start = (page - 1) * 10 + 1


#!/usr/bin/env python3 # to use in terminal
import requests
from bs4 import BeautifulSoup #More beautiful to see html
import urllib.parse
import lxml
import cssselect
import sys
import subprocess 

from googleapiclient.discovery import build #METHOD 1 with BUILD and google_search function


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
	'style',
	'title',#, okremove ?
	'form',#, okremove ?
	'label',#, okremove ?
	'span', #, okremove ?
	'img',#, okremove ?
	'section',#, okremove ?
	'ul', #, unordered list
	'li',#, okremove ?
	'ol',#, ordered list
	'a',#, hyperlink to link one page to another
	'body',#, okremove ?
#	'hgroup'#, okremove ?
]
#USUALLY: p is the good tag or div! but also 'h2', 'h3','h1 maybbe...

def extractMainBlocks(blabla, mChar):
    blocks=blabla.split("\n \n \n")
    extract=""
    for block in blocks:
        if len(block) > mChar:
            extract+=block+" \n"
    return extract

def scrapsPage(url):
    textPage = ''
    result = requests.get(url)
    html_page = result.content # or .text ?
    soup = BeautifulSoup(html_page, 'html.parser')
    #print(soup.prettify()[:10000])
    text = soup.find_all(text=True)
    #Here see what have in text, as text is going to give us some information we don’t want: remove some type in black list.
    print(set([t.parent.name for t in text]))
    for t in text:
    	if t.parent.name not in blacklist:
    		textPage += '{} '.format(t)
    output= extractMainBlocks(textPage, 400) #Could add also number line>>
    return output

def isGood(text):
    #HERE TO JUDGE IF A TEXT IS GOOD: TODO: JUDGE OUTPUT
    return True

def google_search(search_term, api_key, cse_id, **kwargs):
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
    #print(res)
    return res #python dictionarry ok?


###METHOD 2 with request 
#import requests
#params = {'num': 10, 'start': start}
## cf.doc: https://developers.google.com/custom-search/v1/using_rest
#url = f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={SEARCH_ENGINE_ID}&q={query}"
## make the API request:
#data = requests.get(url, params=params).json() #automatically parse the returned JSON data to a Python dictionary:
## specify various request parameters to customize your search, you can also print the data dictionary to see other meta data, such as total results, search time, and even the meta tags of each page. Check CSE's documentation for further detail.
##cf https://developers.google.com/custom-search/v1/using_rest


#NEED PARSE RESULT TO HAVE URL LIST ONLY >
def parse_result(data):
    # get the result items
    search_items = data.get("items")
    urls=[]
    texts=[]
    # iterate over 10 results found
    for i, search_item in enumerate(search_items, start=1):
        # get the page title
        title = search_item.get("title")
        # extract the page url
        link = search_item.get("link")
        # print the results
        print("="*10, f"Result #{i+start-1}", "="*10)
        print("Title:", title)
        print("URL:", link, "\n")

        ## page snippet: NO NEED
        # snippet = search_item.get("snippet")
        # print("Description:", snippet)
        ## alternatively, you can get the HTML snippet (bolded keywords)
        #html_snippet = search_item.get("htmlSnippet")

        #SCRAP TEXT PAGE
        text=scrapsPage(link)
        print("Scrapped Text", text)

        urls.append(link)
        texts.append(text)

    #OR SCRAP UNTIL ONE TEXT IS GOOD ??>>>

    #with open('climateChange.txt', "a") as f: #add this text
	#	f.write(output)
    return urls, texts



def scrap_google(query):
    data = google_search(query, my_api_key, my_cse_id)
    print(data)
    urls = parse_result(data)



scrap_google(query1)