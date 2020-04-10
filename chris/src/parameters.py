import urllib

#PARAMETERS GLOBAL for ACID DRIFT
lengthML=300 #Typical Length drift >>ADD NOISE
nbDrift=2 #Nb MiniDrift, before proba play role
pSwitch=0.3 #=1/nbDrift
pStop=0.2 #proba stop after nDriftMin

##Proba To trigger certain DIRECT function for Chris
pFairy=0.1
pJoke=0.1
pNews=0.1
pSing=0.1
pBark=0.1
pHistory=0.1
pStock=0.1
pEmail=0.1
pQuote=0.1
pWeather=0.1
pISS=0.1
probaTrigger=[pFairy, pJoke, pNews, pSing, pBark, pHistory, pStock, pEmail, pQuote, pWeather, pISS]
sayTrigger=["Tell a fairy tale", "Make me laugh", "Sing", "Bark", "What happened today in history?","Play the News", "Stock price of Google", "Check my email", "Give me a quote", "What is the weather?","Where is the international space station?"]

#Proba for Chris questions
pTrigger=0.3 #Proba trigger one of the above when context is there
pDonald=0.1
pDefi=0.2
pDuck=0.2
pChat=0.1
probaQu=[pTrigger, pDonald, pDefi, pDuck, pChat]

##Proba to put reminder, and proba record/playback.
pRemind=0.1
pPlayBack=0.1
pRecord=0.1

initWords=["vacuum", "assistant", "home", "semantic"]
