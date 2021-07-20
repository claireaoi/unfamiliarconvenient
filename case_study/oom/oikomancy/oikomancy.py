#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Roomba Space Reading Ritual consist of
0) Preliminary: compute the 2D embeddings of his self words.
1) Listen to Arduino, Receive in real time coordinates of new point or ending signals while the Roomba is doing the ritual through the space
2) If point: Check if new point +/- aligned with previous 2 points of trajectory. 
    If not, it means there has been a turn so it:
        - look for closer concept in his self, save concept & distance & point
        - say it aloud
    If it is:
        - replace previous point in trajectory
3) If ending signal: trigger the full reading, i.e.:
    - clean trajectory
    - keep 3 closer concepts
    - generate Haiku from it & say it aloud

"""
#NOTE: self is world and world is self...for VA

######## NOW:
#TODO: Use satellite data or other to trigger this ? or to trigger arduino?
#TODO: Haiku verb conjugation library
#TODO: Haiku Tunings
#TODO Issue with words having 2 components or 3 even... torch.Size([2, 768])

######## SOON should do: 
#TODO: Modify back gpt2 model embeddings & test effect in generation
#TODO: Visualisation
#TODO: Other tunings, parameters etc.

#----------------------IMPORTS------------------------------------------
from mycroft_bus_client import MessageBusClient, Message
from string import punctuation
import random
import json
import re
import numpy as np
from .utils import pick_template, read, update_event_data, generate_haiku, draw, nearest_concept, self_graph_embeddings, initialize, approximately_colinear,redefine_embeddings
import time
import serial
from time import sleep
import sys
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


# =============================================================================
# PARAMETERS to Update or tune
# =============================================================================
#------------------PATHS----------
# #NOTE: CHANGE all these PATH when uploading the script !
GRAPH_PATH = "./oikomancy/graph.json"# This path is temporary, it should refer to the fallbackassociative skill folder: /home/unfamiliarconvenient/.mycroft/fallback-associative/graph.json"
WORDS_PATH="./oikomancy/data/" #Modify when...
EMBEDDINGS_PATH="./oikomancy/custom_embeddings.json" #where save words embeddings
##Parameters for the gpt-2 parameters
PATH_ML_MODEL=""  #path to your fine tuned model, If empty, would use default model #NOTE: UPDATE this to actual model.

#str(pathlib.Path(__file__).parent.absolute()) #may use path lib...

#---------------CONSTANTS MAY TUNE------------------------------
#to decide length trajectory roomba:
MAX_FRAMES=80 
MIN_FRAMES=30
#interval where listen to roomba
INTERVAL_LISTEN=752
#threshold to judge if 3 points are almost aligned; sensitivity may be tuned
COLINEARITY_THRESHOLD=0.05 
#bound for embeddings #NOTE: this depending size room or about depends scale use for other
EMBEDDINGS_BOUND=20 


# =============================================================================
# INITIALISATION
# =============================================================================

print("=============================================================================")
print("--step 0--  INITIALISATION")
print("=============================================================================")

#--init constants
FILENAMES=["A", "Ad1", "Ad2", "Ad3", "V", "Vt", "V2", "V+", "P", "Pf", "P0", "PR0", "PR0a", "PR1a", "PR1", "N", "N2", "Nf","Nfa", "Na", "Aa", "Va", "Nfa", "ism", "Duo", "Nf", "Ma", "S", "Sc", "ESS", "ASA", "ABL", "QU",  "Tion", "Duoa"]

#-make sure Python doesn't flood Arduino with messages
global sent 
sent = False

# --import Message Bus client to communicate with Mycroft's guts
print("Setting up connection to Mycroft client...")
client = MessageBusClient()

#--initialize Self etc
print("Initializing Self...")
self_graph, dico, templates, custom_embeddings=initialize(FILENAMES, GRAPH_PATH, WORDS_PATH, EMBEDDINGS_PATH)

#--extract embeddings of the concepts in Self and 2D embeddings of them
#TODO: Could do it at end when add a word to self? Save it File to gain time ?
print("Extracting Words Embeddings...and 2D Embeddings")
custom_embeddings, embeddings2D=self_graph_embeddings(self_graph, custom_embeddings, EMBEDDINGS_BOUND, PATH_ML_MODEL)

#--connect to Arduino
print("Connecting to Arduino...")
try:
    arduino = serial.Serial("/dev/cu.linvor-DevB", 9600, timeout=2)
    sleep(1)
    print("Connected")
except:
    print("Check Bluetooth")
    sys.exit()

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

    print("-step 1--Listen to Arduino...")
    #---arduino listener
    message = arduino.readline().decode("utf-8").strip()
    print(message)

    if message == 'ready' and not sent:
        # change to 1 after debug
        arduino.write('0'.encode())
        arduino.flush()
        sent = True

    # case where send numerical data
    elif message and message != 'busy' and message != 'starting roo':

        x, y = (message.split(';', 1))
        x = float(x)
        y = float(y)
        
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
                print("-step 2--- Dig the Closer Concept of this turn")
                #means a turn happened, so will read aloud closer previous point (beware, a lil delay as look at previous point!)
                #get idx and distance nearest concept of this point
                idx, dist=nearest_concept(embeddings2D, trajectory[-1])
                #get word attached to that idx
                new_closer_concept=list(custom_embeddings.keys())[idx]
                #TODO: Check that not the same than previously ? (may happen if embeddings not normalized)
                print("Here is {}".format(new_closer_concept))
                #say it aloud 
                client.emit(Message('speak', data={'utterance': new_closer_concept}))
                
                print("-step 3---  update Event data")
                #save data of close concepts and distance
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
    values=list(event_data.values())
    distances=[val[0] for val in values]
    indices=np.argsort(distances)[:3]
    trinity=[keys[i] for i in indices]
    trinity_trajectory=[values[i][1] for i in indices]
    print("The 3 closer self concepts for this event are {}".format(trinity))
    print("They correspond to the 3 points in the trajectory {}".format(trinity_trajectory))

    # =============================================================================
    #--2-- Haiku generation and Reading
    # =============================================================================
    print("-step 2---Generate Haiku")
    haiku=generate_haiku(trinity, templates, dico)
    client.emit(Message('speak', data={'utterance': haiku}))

    # =============================================================================
    #--3-- Drawing Trajectory 
    # =============================================================================
    print("-step 3---Drawing Trajectory")
    draw(trajectory, trinity_trajectory, "Blip")

    # =============================================================================
    #--4-- Redefine embeddings of these 3 concepts
    # =============================================================================
    print("-step 4---Redefine embeddings of these 3 concepts")
    custom_embeddings=redefine_embeddings(custom_embeddings, trinity)

    return trinity, custom_embeddings


# =============================================================================
# Actual Script running in loop
# =============================================================================

while True:
    print("=============================================================================")
    print("******+ Launching a new RITUAL ******+")
    print("=============================================================================")

    print("=============================================================================")
    print("******+ SPATIAL DANCE ******+")
    print("=============================================================================")
    # listen to Arduino trajectory in real time, save coordinates and draw graph
    #NOTE: currently stop listening after a certain number of frames. Could also be related to an ending signal (if arduino sends it...)
    plt.figure(figsize=(10,5))
    #compute for how many frames fo the ritual
    num_frames_trajectory=random.randint(MIN_FRAMES, MAX_FRAMES)
    ani = FuncAnimation(plt.gcf(), spatial_ritual, frames=num_frames_trajectory, interval=INTERVAL_LISTEN) 
    plt.show(block=True)
    trajectory = trajectory[:-1] #because the trajectory had one more point than when wee looked for concepts...

    print("=============================================================================")
    print("******+ SPIRITUAL READING ****** ")
    print("=============================================================================")
    trinity, custom_embeddings=reading_event(trajectory, custom_embeddings, embeddings2D, event_data)

    print("=============================================================================")
    print("******+END ******+")
    print("=============================================================================")
    #--reinit some variables before next ritual
    reinit()







# laod JSON structure
# with open('sensordata.json') as jf:
#     data_archive = json.load(jf)

#---------OLD CODE TEMPORARY KEEP it but can ERASE it SOON

# basically runs this script in a loop ? Need?
#client.run_forever()


    # #-1--- simplify pattern: if 3 consecutive points +/- aligned, remove the one in the middle
    # print("***Simplifying trajectory***")
    # i=0
    # cleaned_trajectory=[trajectory[0]]
    # while i<num_points_init-3:
    #     aligned=True
    #     count=i+1
    #     while aligned and count<num_points_init-1:
    #         p1, p2, p3=trajectory[i],trajectory[count], trajectory[count+1]
    #         ##check if p1,p2,p3 are colinear
    #         aligned=approximately_colinear(p1,p2,p3)
    #         count+=1
    #     cleaned_trajectory.append(trajectory[count]) 
    #     i=count
    # num_points=len(cleaned_trajectory)
    # print("Original trajectory length {} cleaned trajectory length {}".format( num_points_init,  num_points))


    # #-3---find closer words to each of these points
    # print("***Interpreting Trajectory; extracting closer concepts***")
    # close_concepts, distances, trajectory_points=[], [], []
    # for i, point in enumerate(extracted_trajectory):
    #     if (not (i == 0)) and (not (i == max_num_points-1)):
    #         idx, dist=nearest_concept(embeddings2D, point)
    #         key=list(words_embeddings.keys())[idx] #get corresponding concept
    #         print(i, point, idx, key)
    #         if key not in close_concepts:
    #             close_concepts.append(key)
    #             distances.append(dist)
    #             trajectory_points.append(point)#point from traj is closer to
    #         else:#TODO: currently too often same concept closer to all>>> change this! Rather ok if same?
    #             j=close_concepts.index(key)
    #             if dist<distances[j]:#update distance #although risk one closer to several
    #                 distances[j]=dist
    #                 trajectory_points[j]=point
    # assert len(distances)==len(close_concepts)==len(trajectory_points)


    #     # =============================================================================
    # #--step 1-- Extract Sub Trajectory ()
    # # =============================================================================
    # max_num_points=7 #TBD
    # extract_sub_trajectory =False #TBD NOTE: May choose if trajectory too long to extrac sub trajectory

    # if extract_sub_trajectory and len(trajectory)>max_num_points:
    #     extracted_trajectory=trajectory
    #     num_points=max_num_points
    #     start=random.randint(0,num_points-max_num_points)
    #     extracted_trajectory=trajectory[start:start+max_num_points]
    #     print("Extracted a trajectory of length {}".format(max_num_points))
    # else:
    #     extracted_trajectory=trajectory