#!/usr/bin/env python3 # to use in terminal


main_url = "http://books.toscrape.com/index.html"

#But actually https, work?
url1="http://www.climatehubs.usda.gov/sites/default/files/Climate%2C%20Weather%20and%20Strawberries.pdf"
url2="http://www.tampabay.com/incoming/climate-change-shifts-strawberry-farming/2331250/"
url3="http://www.ishs.org/ishs-article/838_6"
url4="http://www.telegraph.co.uk/news/earth/earthnews/8603607/Climate-change-resistant-strawberries.html"

import requests
from bs4 import BeautifulSoup #More beautiful to see html

blacklist = [
	'[document]',
	'noscript',
	'header',
	'html',
	'meta',
	'head',
	'input',
	'script',
	# there may be more elements you don't want, such as "style", etc.
]

#More beautiful
def scrapText(url):
    textPage = ''
    result = requests.get(url)
    html_page = result.content # or .text ?
    soup = BeautifulSoup(html_page, 'html.parser')
    #print(soup.prettify()[:10000])
    text = soup.find_all(text=True)
    #Here see what have in text
    print(set([t.parent.name for t in text]))

    for t in text:
    	if t.parent.name not in blacklist:
    		textPage += '{} '.format(t)
    #However, this is going to give us some information we don’t want.
## {'label', 'h4', 'ol', '[document]', 'a', 'h1', 'noscript', 'span', 'header', 'ul', 'html', 'section', 'article', 'em', 'meta', 'title', 'body', 'aside', 'footer', 'div', 'form', 'nav', 'p', 'head', 'link', 'strong', 'h6', 'br', 'li', 'h3', 'h5', 'input', 'blockquote', 'main', 'script', 'figure'}
    output= extractMainBlock(textPage)
    print(output)
    return(output)

#Bigger in size
def extractMainBlock(blabla):
    blocks=blabla.split("\n \n \n")
    maxBlock=blocks[0]
    max=len(blocks[0])
    for block in blocks:
        if len(block) > max:
            maxBlock=block
            max=len(block)
    return maxBlock




#With soup can look for stuff: EX: soup.find("article", class_ = "product_pod")
#soup.find("article", class_ = "product_pod").div.a
#Go on & specify #soup.find("article", class_ = "product_pod").div.a.get('href')

scrapText(url4)
