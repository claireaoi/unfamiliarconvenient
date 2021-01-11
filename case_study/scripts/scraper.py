
#!/usr/bin/env python3 # to use in terminal

#TODO: IMPROVE TIME! for extracting texts step mainlz
#TODO: TO FILTER FOLLOWING TEXTS below page. library check if make sense
#remove link if only a link, not in a sentence?
#newspaper as parser?
#RUN NEW TESTS. 

#**********************************************************************IMPORT**************************************************************************

import requests
from bs4 import BeautifulSoup #More beautiful to see html
import urllib.parse
import lxml
import cssselect
import sys
import subprocess 
from googleapiclient.discovery import build #METHOD 1 with BUILD and google_search function
from configparser import ConfigParser
import random

#***********************************************************************PARAMETERS INITIALIZATION***************************************************************************

####LOAD CONFIG PARAMETERS
config = ConfigParser()
config.read('./case_study/data/config.ini') 
my_api_key = config.get('auth', 'my_api_key')
my_cse_id = config.get('auth', 'my_cse_id')

#OTHER PARAMETERS #TODO: AS ARGUMENT FCT>>>
page = 2
start = (page - 1) * 10 + 1
minimum_char_one=80
minimum_char_all=400
maximum_char=1000

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
	'form',#, okremove ?
	'label',#, okremove ?
	'span', #, okremove ?
	'img',#, okremove ?
	'section',#, okremove ?
	'ul', #, unordered list
	'li',#, okremove ?
	'ol',#, ordered list
	#'a',#, hyperlink to link one page to another?#TODO: GET THE TEXT FROM the a, not the href
	'body',#, okremove ?
#	'hgroup'#, okremove ?
]
#USUALLY: p is the good tag or div! but also 'h2', 'h3','h1 maybbe...
#GOOD TAGS: p, a, div, i, ...

#*******************************************************************PROCEDURES**************************************************************************

def google_search(search_term, api_key, cse_id, **kwargs):
    """
        Use Google Search API to get Google results over a query
    """
    service = build("customsearch", "v1", developerKey=api_key)
    res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
    #print(res)
    return res #python dictionarry ok?

def get_urls(data):
    """
        Parse the data obtained from Google API to get the urls of these articles.
    """
    # get the result items
    search_items = data.get("items")
    urls=[]
    for i, search_item in enumerate(search_items, start=1):
        title = search_item.get("title")
        link = search_item.get("link")
        #Print the results
        #print("="*10, f"Result #{i+start-1}", "="*10)
        #print("Title:", title)
        #print("URL:", link, "\n")
        urls.append(link)
    return urls


def extractMainBlocks(blabla, minimum_char):
    """
        Extract the main blocks of text, above a certain number of characters.
    """
    #TODO: ONLY KEEP ONE BLOCK FOR FURTHER COHERENCE. (as one paragraph) between 2 tags for instance...
    
    blocks=blabla.split("\n \n \n")
    extract=""
    for block in blocks:
        if len(block) > minimum_char:
            extract+=block+" \n"
    return extract

def scrapsPage(url, minimum_char_one, minimum_char_all):
    textPage = ''
    result = requests.get(url)
    html_page = result.content # or .text ?
    soup = BeautifulSoup(html_page, 'html.parser')
    #print(soup.prettify()[:10000])
    text = soup.find_all(text=True)
    #Here see what have in text, as text is going to give us some information we don’t want: remove some type in black list.
    #print(set([t.parent.name for t in text]))
    for t in text:
        if len(t)>minimum_char_one:#for one thing between tag
            if not (t.parent.name in blacklist):
                #FIRST FILTER HERE if has element <
                #TODO: FILTER MORE from html type but also characters
                if (t.count("<") < 2):
                    textPage += '{} '.format(t)
    #JUST HERE TO CHECK BLOCK TYPE HTML, COMMENT OUT THEN
    #for t in text:
    #    if len(t)>minimum_char_one:
    #        if not (t.parent.name in blacklist) and (t.count("<") < 2):
    #            print("===================")
    #            print(t.parent.name)
    #            print(t)
    output= extractMainBlocks(textPage, minimum_char_all) 
    return output

def filter_html(text):
    """
        Filter the html text  like <...> blabla <...> unless very long within blabla (because then may be a paragraph)
    #TODO
    """
    return text

def extract_text(urls, minimum_char_one, minimum_char_all):
    extracts=[]
    for url in urls:
        #print("new PAGE=======================================================")
        extract=scrapsPage(url, minimum_char_one, minimum_char_all)
        #print("Scrapped Text", extract)
        filtered_extract=filter_html(extract)
        if not filtered_extract is None:
            extracts.append(filtered_extract)
    return extracts

def choose_extract(extracts):
    """
        Choose an extract of text among several. 
        First filter it by a "is cool" procedure, to select only nice texts. (todo, cf. below)
        Then, pick up randomly among the 3 longer cool extracts
    """
    cool_extracts=[]
    cool_length=[]
    for extract in extracts:
        if isCool(extract):
            cool_extracts.append(extract)
            cool_length.append(len(extract))
    #Get 3 longer cool extracts
    nb_pick=min(3, len(cool_extracts))#Will pick 3 if nb cool exctracts >=3
    longer_extracts=sorted(zip(cool_length, cool_extracts), reverse=True)[:nb_pick]#as sorted by default order from first argument when tuple
    #Pick one randomly
    chosen_extract=random.choice(longer_extracts)
    return chosen_extract[1]#text part (first element is score)

def isCool(text):
    """
    Has to try to judge if a text extract is cool.
    #TODO: Do this procedure. if too much space between lines, bad, paragraph condensed are better or if too many special characters may be bad etc.
    #notably if too much of : </div>
    #For now temporary: count <> and if bigger than 20, say not cool. But need to implement filter_html first
    """

    nb_bad_stuff=text.count("<")

    return bool(nb_bad_stuff<4)#CHECK THIS

def cut_extract(extract, maximum_char):
    """
    Cut a text extract if above a certain nb character
    """
    #TODO: find closer punctuation sign to cut at end sentence!

    return extract[:maximum_char]


#**********************************************************************MAIN PROCEDURE**************************************************************************


def surf_google(query, minimum_char_one, minimum_char_all, maximum_char):
    """
    Main procedure to scrap google result of a query: will scrap the urls first, then the texts of the articles, parse the text and choose
    one of these extracts.

    """
    #TODO: if none result satisfying criteria (length etc), relaunch further pages?

    ###(0) Scrap data from Google Search
    print("=======================================================")
    print("Scraping Google results")
    data = google_search(query, my_api_key, my_cse_id)
    #print(data)
    ###(1) Get urls
    urls = get_urls(data)
    print("=======================================================")
    print("Getting urls")
    #print(urls)
    ###(2) Extract texts part
    print("=======================================================")
    print("Extracting the texts")
    #TODO: check if can accelerate this step
    scraped_data=extract_text(urls, minimum_char_one, minimum_char_all)
    #print(extracts)
    ###(3) Choose one extract
    print("=======================================================")
    print("Choosing one Extract")
    chosen_extract=choose_extract(scraped_data)
    #print(chosen_extract)#TODO: FILTER?
    ###(4) Cut extract
    print("=======================================================")
    print("Final Extract")
    final_extract=cut_extract(chosen_extract, maximum_char)
    print(final_extract)
   
    return scraped_data, final_extract

###LAUNCH IT to try. TEST SAVE
#surf_google("Coffee", minimum_char_one, minimum_char_all, maximum_char)



#**********************************************************************OLD ARXIV*************************************************************************



###METHOD 2 with request 
#import requests
#params = {'num': 10, 'start': start}
## cf.doc: https://developers.google.com/custom-search/v1/using_rest
#url = f"https://www.googleapis.com/customsearch/v1?key={API_KEY}&cx={SEARCH_ENGINE_ID}&q={query}"
## make the API request:
#data = requests.get(url, params=params).json() #automatically parse the returned JSON data to a Python dictionary:
## specify various request parameters to customize your search, you can also print the data dictionary to see other meta data, such as total results, search time, and even the meta tags of each page. Check CSE's documentation for further detail.
##cf https://developers.google.com/custom-search/v1/using_rest



  ## page snippet: 
        # snippet = search_item.get("snippet")
        # print("Description:", snippet)
        ## or for HTML snippet (bolded keywords) html_snippet = search_item.get("htmlSnippet")


#TO FILTER FOLLOWING TEXTS
""" Setting `pad_token_id` to `eos_token_id`:50256 for open-end generation.

	Subscription Cart Footer
	http://rechargepayments.com: v2
	Updated: 2017/06/12

 """
#TODO: CHECK FILTERING FOR THIS
 #age, including during development in the womb, during childhood, and during adulthood (13). When a clitoris size is large enough to be considered abnormal, this is called   and the clitoris are related in structure t

                                    #  Hats & Caps
                                 
                                    #             Beanies & Winter Hats
                                             
                                    # Hair Accessories
                                 
                                    #             Headbands
                                             
                                    #             Fascinators & Mini Hats
                                             
                                    #             Wreaths & Tiaras
                                             
                                    # Sunglasses & Eyewear
                                 
                                    # Scarves & Wraps
                                 
                                    # Belts & Suspenders
                                 
                                    # Keychains & Lanyards


                 
                    # Clit Clip Emoji Humor Nonpiercing Clit Jewelry Fake VCH Piercing Under The Hoode Intimate Jewelry and Gifts Stud Button Hugger Emoticons
                 
                    # Clit Clip Fake VCH Piercing Clip On Clit Jewelry Large Ebony Heart Button Hugger Clit Stimulation Under The Hoode
                 
                    # Clit Clip Fake VCH Piercing Clip On Clit Jewelry Copper Sun Button Hugger Clit Stimulation Under The Hoode
                 
                    # Clit Clip Fake VCH Piercing Clit Jewelry Shimmering Pink Stud Button Hugger Under The Hoode
                 
                    # Clit Clip Fake VCH Piercing Clip On Clit Jewelry Faux Turquoise Medallion Stud Button Hugger Clit Stimulation Under The Hoode
                 
                    # Clit Clip Fake VCH Piercing Clip On Clit Jewelry Bronze Floral Button Hugger Clit Stimulation Under The Hoode
                 
                    # Clit Clip Fake VCH Piercing Clip On Clit Jewelry Hibiscus Charm Button Hugger Clit Stimulation Under The Hoode 
# =============================================Content Header========================================== 
# =============================================Title Bar========================================== 
# =============================================Content Body========================================== 

# © Copyright 2021 Variety Media, LLC, a subsidiary of Penske Business Media, LLC. Variety and the Flying V logos are trademarks of Variety Media, LLC.  

#                                                                 Create                                                                                                                             Make social videos in an instant: use custom templates to tell the right story for your business. 
#                                                                 Screen Recorder                                                                                                                             
#                                                                 Live Streaming                                                                                                                             
#                                                                 Enterprise                                                                                                                             Get your team aligned with all the tools you need on one secure, reliable video platform. 
#                                         Log in                                     
#                                         Join                                     
#                                                 Upload                                                                                             
#                                                 Create a video                                                                                             
#                                                 Go live                                                                                             
#                                 Distribution & Marketing                             
#                                 Hosting & Management                             Make social videos in an instant: use custom templates to tell the right story for your business. Get your team aligned with all the tools you need on one secure, reliable video platform. 
#                                 Creative Professionals                             
#                                                                 Pricing                                                                                             Search                              

#future. Accuracy and availability may vary. The authoritative record of NPR’s programming is the audio record.  END ID="NEWSLETTER-ACQUISITION-CALLOUT-DATA" DATA-NEWSLETTER="{&QUOT;NEWSLETTERID&QUOT;:&QUOT;BREAKING-NEWS&QUOT;,&QUOT;TITLE&QUOT;:&QUOT;BREAKING NEWS ALERTS&QUOT;,&QUOT;MARKETINGHEADER&QUOT;:&QUOT;SIGN UP FOR BREAKING NEWS ALERTS&QUOT;,&QUOT;FREQUENCY&QUOT;:&QUOT;&QUOT;,&QUOT;SHORTDESCRIPTION&QUOT;:&QUOT;STAY ON TOP OF THE LATEST STORIES AND DEVELOPMENTS, SENT WHEN NEWS BREAKS.&QUOT;,&QUOT;STICKYDESCRIPTION&QUOT;:&QUOT;SIGN UP FOR BREAKING NEWS ALERTS TO STAY ON TOP OF THE LATEST STORIES AND DEVELOPMENTS.&QUOT;,&QUOT;CONTENTIMAGE&QUOT;:&QUOT;HTTPS:\/\/MEDIA.NPR.ORG\/ASSETS\/IMG\/2018\/08\/03\/NEWSLETTERS\/BREAKING_NEWS.PNG&QUOT;,&QUOT;STATICMARKUPDIR&QUOT;:&QUOT; &QUOT;,&QUOT;BRANDINGDIR&QUOT;:&QUOT; &QUOT;,&QUOT;BRANDINGLINK&QUOT;:&QUOT; &QUOT;,&QUOT;ORGANIZATIONID&QUOT;:1,&QUOT;RECAPTCHASITEKEY&QUOT;:&QUOT;6LFD6CYUAAAAAIBEUEKWZ9KCJF4UYLFTU7NWNAEK&QUOT;}"   END ID="END-OF-STORY-RECOMMENDATIONS-MOUNT" CLASS="RECOMMENDED-STORIES" ARIA-LABEL="RECOMMENDED STORIES"   

