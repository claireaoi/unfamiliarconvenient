



#***********************************************************************INITIALIZATION***************************************************************************
###IMPORT Library
import fire

###IMPORT scripts
import core #Main script, with the different procedures
import visualize as vis #to visualize the selfGraph

#Load the selfGraph, the memory, and the interaction text from which will look for words.
with open('./chris/data/selfgraph.txt') as json_file:
    selfGraph = json.load(json_file)
with open('./chris/data/wordsMemory.txt', "r") as f:
    wordsMemory=f.readlines() #List of words concepts he looked up
with open('./chris/data/whatIHeard.txt', "a") as f:#Last historics before Chris learned
    blabla=f.readlines()

print("Self Graph Loaded here. Self Quest begins")

#***********************************************************************PROCEDURES*************************************************************************

def selfQuest(nDrift, lengthML, nSimMax, nSearch, lengthWalk, walkNetwork, audibleSelfQuest, ifVisualize):
    #(1) Self Quest, with possible walk on the network, etc, from the text blabla
    selfGraph, wordsMemory, addedWords, blablaQuest=core.selfMapLoops(selfGraph, blabla, 1, nDrift, lengthML, nSimMax,  wordsMemory, nSearch, lengthWalk, walkNetwork, True, audibleSelfQuest)

    #(2) Save the selfGraph, Update the memory
    with open('./chris/data/selfgraph.txt', 'w') as outfile:
        json.dump(selfGraph, outfile)
        nN=len(selfGraph.keys())
        print("Self has " + str(nN) + " nodes.")
        print("I am made of:", list(selfGraph.keys()))
    with open('./chris/data/wordsMemory.txt', "w") as f:
        f.write("\n".join(wordsMemory))
    #(3) Visualize if want
    if ifVisualize:
        vis.drawGraph()

#Direct Launch Interact
if __name__ == '__main__':
    fire.Fire(selfQuest)
