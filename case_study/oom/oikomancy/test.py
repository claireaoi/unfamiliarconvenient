#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#----------------------IMPORTS------------------------------------------
from string import punctuation
import random
import json
import re
import numpy as np
from utils import pick_template, read, visualize_event_chart, update_event_data, generate_haiku, nearest_concept, initialize, approximately_colinear,redefine_embeddings
import time
from time import sleep
import sys
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from datetime import datetime

from gingerit.gingerit import GingerIt
gingerParser= GingerIt() #for grammar

# =============================================================================
# PARAMETERS to Update or tune
# =============================================================================
#------------------PATHS----------
# #NOTE: Update paths
GRAPH_PATH = "./oikomancy/graph.json"# This path is temporary, it should refer to the fallbackassociative skill folder: /home/unfamiliarconvenient/.mycroft/fallback-associative/graph.json"
WORDS_PATH="./oikomancy/data/" #Modify when...
EMBEDDINGS_PATH="./oikomancy/custom_embeddings.json" #where save words embeddings
##Parameters for the gpt-2 parameters
PATH_ML_MODEL=""  #path to your fine tuned model, If empty, would use default model #NOTE: UPDATE this to actual model.
EMBEDDINGS2D_PATH="./oikomancy/custom_embeddings2D.npy" #where save words embeddings
READING_EVENT_FOLDER="./oikomancy/outputs/"

#str(pathlib.Path(__file__).parent.absolute()) #may use path lib...

#---------------CONSTANTS MAY TUNE------------------------------
#to decide length trajectory roomba:
MAX_FRAMES=10
MIN_FRAMES=6
#interval where listen to roomba
INTERVAL_LISTEN=752
#threshold to judge if 3 points are almost aligned; sensitivity may be tuned
COLINEARITY_THRESHOLD=0.05 
#bound for embeddings
EMBEDDINGS_SCALE=1 #


# =============================================================================
# INITIALISATION
# =============================================================================

print("=============================================================================")
print("*** INITIALISATION ***")
print("=============================================================================")

#--init constants
FILENAMES=["A", "Ad1", "Ad2", "Ad3", "V", "Vt", "V2", "V+", "P", "Pf", "P0", "PR0", "PR0a", "PR1a", "PR1", "N", "N2", "Nf","Nfa", "Na", "Aa", "Va", "Nfa", "ism", "Duo", "Nf", "Ma", "S", "Sc", "ESS", "ASA", "ABL", "QU",  "Tion", "Duoa"]

#-make sure Python doesn't flood Arduino with messages
global sent 
sent = False
#--to save all points trajectory
global x_vals
global y_vals
x_vals = [] 
y_vals = []
#--to save MAIN points trajectory (only "turns")
global trajectory
trajectory=[]
#--to save concepts related to the space reading, with their associated distance & closer points in the trajectory
global event_data
event_data=dict()

#--initialize Self etc
print("Initializing Self...")
self_graph, dico, templates, custom_embeddings, embeddings2D=initialize(FILENAMES, GRAPH_PATH, WORDS_PATH, EMBEDDINGS_PATH, EMBEDDINGS2D_PATH)

#---rescale 2D embeddings if needed, depending space
embeddings2D=EMBEDDINGS_SCALE*embeddings2D


#set num frames
global num_frames
num_frames=random.randint(MIN_FRAMES, MAX_FRAMES)

#set event id
global event_id
#NOTE: event id for now is hours:min:seconds, but could be based on satellite data rather triggering it?
now = datetime.now()
event_id=now.strftime("%H:%M:%S")

#--time tracker 
#start_time = time.time()

print("Ready to start the Ritual !")

# =============================================================================
# Reinit
# =============================================================================

def reinit():
    #--init some variables:
    #--to save points trajectory
    global x_vals
    global y_vals
    x_vals = [] 
    y_vals = []
    global trajectory
    trajectory=[]#for MAIN points
    global event_data
    event_data=dict()

# =============================================================================
# Spatial Ritual (& Arduino Listener)
# =============================================================================

def spatial_ritual(i):
    """
    Spatial Ritual:
    - Listen to coordinate Sent by Arduino
    - If new interesting point (ie turn), would look up closer Self concept and say it aloud
    - Save the event data for future use 

    Input: int, step of the trajectory
    """

    global sent
    global x_vals
    global y_vals
    global trajectory
    global event_data

    print("Frame {}".format(i))

    #NOTE: CHANGED THE PROCEDURE TO TEST IT 
    if i==num_frames-1: #NOTE: currently last frame save & close the plot
        #plt.savefig('full_trajectory_event_'+ event_id+ '.png')
        print("Ending Spatial Dance!")#TODO: Send signal to arduino to stop, or
        plt.close()
    
    else:
        # case where send numerical data
        
        x = random.uniform(0.5,1)#TODO: TEMP between 0 and 1 as noticed embeddings concentrated mostly positive
        y = random.uniform(0.5,1)
        
        #--save data trajectory
        x_vals.append(x)
        y_vals.append(y)
        
        #--save plot frame
        plt.cla()
        plt.plot(x_vals, y_vals, color="mediumblue", marker="2",markevery=1, markersize=5, markeredgecolor="orangered")

        #----Check if new point +/- aligned with previous 2 points of trajectory (if trajectory length >2...)
        new_point=[x,y]
        
        
        #check if new point aligned with 2 previous point if nb point >=2
        if len(trajectory)>=2:
            aligned=approximately_colinear(trajectory[-2],trajectory[-1],new_point, threshold=COLINEARITY_THRESHOLD)
            if aligned:
                #new point aligned with last 2, so replace last point with new point:
                trajectory[-1]=new_point
                #NOTE: This is a way to clean the trajectory, in the sense it removes intermediary points on the same line, 

            else: 
                #means a turn happened, so will read aloud closer previous point (beware, a lil delay as look at previous point!)
                #get idx and distance nearest concept of this point
                idx, dist=nearest_concept(embeddings2D, trajectory[-1])
                #get word attached to that idx
                new_closer_concept=list(custom_embeddings.keys())[idx]
                #TODO: Check that not the same than previously ? (may happen if embeddings not normalized)
                print("--looking at trajectory point {}. Here is {}".format(trajectory[-1], new_closer_concept))
                #say it aloud 
                #client.emit(Message('speak', data={'utterance': new_closer_concept}))
                
                #--update event data
                # #save data of close concepts and distance
                #NOTE: beware this concept may be already in registered concept, in which case, 
                # update the idx of the trajectory point only if closer than last time registered
                event_data=update_event_data(new_closer_concept, dist, len(trajectory)-1, event_data)

                #add new point to trajectory (at least temporarily)
                trajectory.append(new_point)

        else: #second point in traj
            trajectory.append(new_point)


# =============================================================================
# Reading event
# =============================================================================


def reading_event(trajectory, custom_embeddings, embeddings2D, event_data):
    """
    Reading of the trajectory
    Inputs:
        trajectory: list of points in 2D space send by roomba
        custom_embeddings: embedding dictionary of self concepts
        embeddings2D: 2D embeddings of self concepts
        event_data: dictionnary whose keys are string (concepts) and values are list [float, int] (which are distances, reps. idx of corresponding trajectory point in our case)
    Output:
        trinity: 3 closer self concepts selected
        custom_embeddings: redefined embedding dictionary
        
    """
    num_points=len(trajectory)
    print("Reading Event of a trajectory of length {}".format(num_points))
    #TODO: work with sub trajectory if too big?

    # =============================================================================
    #--1--  Extract 3 Closer concepts
    # =============================================================================
    print("-step 1--Extract 3 closer concepts")
    keys=list(event_data.keys())
    values=list(event_data.values()) #list of [distance, idx]
    distances=[val[0] for val in values]
    indices=np.argsort(distances)[:3]
    trinity=[keys[i] for i in indices]
    trinity_idx=[values[i][1] for i in indices]
    trinity_trajectory=[trajectory[idx] for idx in trinity_idx]
    print("Event trinity Core: {}".format(trinity))
    print("In correspondance with the 3 domesticoCosmic points n° {}".format(trinity_idx))

    # =============================================================================
    #--2-- Haiku generation and Reading
    # =============================================================================
    print("-step 2---Generate Haiku")
    haiku=generate_haiku(trinity, templates, dico, gingerParser)
    trinity=[keys[i] for i in indices] #seems needed to redefine it as original else trinity got "consumed" by Haiku generation
    #save it
    with open(READING_EVENT_FOLDER+"haiku_event_"+ event_id+ '.txt', 'w+') as f:
        f.writelines(haiku.split(";"))

    #client.emit(Message('speak', data={'utterance': haiku}))

    # =============================================================================
    #--3-- Redefine embeddings of these 3 concepts
    # =============================================================================
    print("-step 4---Redefine embeddings of these 3 concepts")
    custom_embeddings=redefine_embeddings(custom_embeddings, trinity)
    #save it:
    with open(EMBEDDINGS_PATH, 'w') as fp:
        json.dump(custom_embeddings, fp)

    return trinity, trinity_trajectory, custom_embeddings, haiku

# =============================================================================
# Actual Script running in loop
# =============================================================================



print("=============================================================================")
print("****** Launching a new RITUAL ******")
print("=============================================================================")

print("=============================================================================")
print("****** SPATIAL DANCE ******")
print("=============================================================================")
# listen to Arduino trajectory in real time, save coordinates and draw graph
#NOTE: currently stop listening after a certain number of frames. Could also be related to an ending signal (if arduino sends it...)
plt.figure(figsize=(10,5))
#compute for how many frames fo the ritual
num_frames_trajectory=random.randint(MIN_FRAMES, MAX_FRAMES)
print("Performing spatial ritual for {} frames".format(num_frames_trajectory))
ani = FuncAnimation(plt.gcf(), spatial_ritual, frames=num_frames_trajectory, interval=INTERVAL_LISTEN, repeat=False) 
plt.show(block=True)
trajectory = trajectory[:-1] #because the trajectory had one more point than when wee looked for concepts...
print("Trajectory of length {}".format(len(trajectory)))

print("=============================================================================")
print("******  SPIRITUAL READING ****** ")
print("=============================================================================")
trinity, trinity_trajectory, custom_embeddings, haiku=reading_event(trajectory, custom_embeddings, embeddings2D, event_data)


print("=============================================================================")
print("****** END ******")
print("=============================================================================")

#--visualise Event Chart
visualize_event_chart(trajectory, trinity_trajectory, haiku, event_id=event_id, output_folder=READING_EVENT_FOLDER)
print("Saved new Event Chart!")

#--reinit some variables before next ritual
reinit()
print("reinitialized.")







# =============================================================================
# TEMP to test HAIKU
# =============================================================================
# haiku=generate_haiku(["bathtub", "internet", "duck"], templates, dico, gingerParser)





