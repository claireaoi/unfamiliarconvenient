############## Parameters chosen for the ML Drift################


#Length of ML Drift:
lengthDrift=200

#Number of ML Drifts:
nDrift=1

#Temperature Drift

#Repetition Penalty drift
temperature = 1.0

repetition_penalty = 2

#If decide randomize moods:
randomizeMood=True
#If not, here is the mood chosen:
currentMood='neutral'

#Possible moods for the ML Drift, with their probabilities.
#Keeping the category neutral as such, with an empty string only, enable have the possibility of a neutral mood, so unaltered ML drift.
moodSeeds=dict()
moodSeeds["curious"]=["Why are they", "Why do they", "How could we", "I wonder if", "I wonder how", "Why are there still", "What should we think of", "Is there something like"]
moodSeeds["confrontational"]=["Maybe not.", "Yet, I feel this is wrong. ", "I would argue against this.", "I would prefer not to.", "What if this is bullshit?", "I don't believe in this. Listen,"]
moodSeeds["thrilled"]=["Amazing.", "That is wonderful.", "How beautiful is this.", "That is incredible."]
moodSeeds["emotional"]=["It makes me feel", "I feel like"]
moodSeeds["appreciative"]=["Let us appreciate how", "Let us contemplate the", "Now, let us breathe and take a moment for", "Let us welcome the", "Let us appreciate what", "Instead of opposing, we shoud embrace", "I would like to thank the world for what"]
moodSeeds["thrilled"]=["Amazing.", "That is wonderful.", "How beautiful is this.", "That is incredible."]
moodSeeds["neutral"]=[""]

#Randomize the Moods:
probaMood=dict()
probaMood["curious"]=0.2
probaMood["confrontational"]=0.2
probaMood["thrilled"]=0.1
probaMood["emotional"]=0.1
probaMood["appreciative"]=0.1
probaMood["thrilled"]=0.1
probaMood["neutral"]=0.2