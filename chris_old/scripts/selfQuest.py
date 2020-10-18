

#***********************************************************************INITIALIZATION***************************************************************************
###IMPORT Library
import fire

###IMPORT scripts
import core #Main script, with the different procedures
import visualize as vis #to visualize the selfGraph

#***********************************************************************PROCEDURES*************************************************************************

def loadSelf(firstTime):
    if firstTime:
        print("Hatching self in process...")
        execfile('./chris/scripts/initGraph.py')
        with open('./chris/data/selfbirth.txt') as json_file:
            selfGraph = json.load(json_file)
            wordsMemory=list(selfGraph.keys()) #The memory of the VA is the words he has looked for on wikipedia.
            wo=wordsMemory[0]#To remember where is last element added
            wordsMemory[0]=str(len(wordsMemory))
            wordsMemory.append(wo)
        blabla=[]
    else:
        with open('./chris/data/selfgraph.txt') as json_file:
            selfGraph = json.load(json_file)
        with open('./chris/data/wordsMemory.txt', "r") as f:
            wordsMemory=f.readlines() #List of words concepts he looked up
        with open('./chris/data/whatIHeard.txt', "r") as f:#Last historics before Chris learned
            blabla=f.readlines()

    print("I am here. Self Quest can begin.")
    print("I am made of:", list(selfGraph.keys()))
    nSelf=len(list(selfGraph.keys()))
    return selfGraph, wordsMemory, blabla

def selfQuest(firstTime, nDrift, lengthML, nSimMax, nSearch, lengthWalk, walkNetwork, audibleSelfQuest, ifVisualize):
    #(0) Load SELF, memory, rememberedStuff and blabla
    ####selfGraph is a dictionnary, whose keys are concepts, and values are couple (weight, neighbors).
    selfGraph, wordsMemory, blabla=loadSelf(firstTime)

    #(1) Self Quest, with possible walk on the network, possible ML drifts, and parameters, from the text blabla
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
