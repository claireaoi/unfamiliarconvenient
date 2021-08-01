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
#TODO: Issue with words having 2 components or 3 even... torch.Size([2, 768])
#TODO: CLEAN self graph.. there are letters like c
#TODO: Test embeddings 

######## SOON should do: 
#TODO: Modify back gpt2 model embeddings & test effect in generation
#TODO: Visualisation better
#TODO: Other tunings, parameters etc.

#----------------------IMPORTS------------------------------------------
from mycroft_bus_client import MessageBusClient, Message
from string import punctuation
import random
import json
import re
import numpy as np
from .utils import pick_template, read, visualize_event_chart, update_event_data, generate_haiku, nearest_concept, initialize, approximately_colinear,redefine_embeddings
import time
import serial
from time import sleep
import sys
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from datetime import datetime


# =============================================================================
# PARAMETERS to Update or tune
# =============================================================================
#------------------PATHS----------
# #NOTE: CHANGE all these PATH when uploading the script !
GRAPH_PATH = "./oikomancy/graph.json"# This path is temporary, it should refer to the fallbackassociative skill folder: /home/unfamiliarconvenient/.mycroft/fallback-associative/graph.json"
WORDS_PATH="./oikomancy/data/" #Modify when...
EMBEDDINGS_PATH="./oikomancy/custom_embeddings.json" #where save words embeddings
EMBEDDINGS2D_PATH="./oikomancy/custom_embeddings2D.npy" #where save words embeddings
READING_EVENT_FOLDER="./oikomancy/outputs/"

#str(pathlib.Path(__file__).parent.absolute()) #may use path lib...

#---------------CONSTANTS MAY TUNE------------------------------
#to decide length trajectory roomba:
MAX_FRAMES=80 
MIN_FRAMES=30
#interval where listen to roomba
INTERVAL_LISTEN=752
#threshold to judge if 3 points are almost aligned; sensitivity may be tuned
COLINEARITY_THRESHOLD=0.05 
#NOTE: change the scale embeddings depending size room!
EMBEDDINGS_SCALE=1


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

# --import Message Bus client to communicate with Mycroft's guts
print("Setting up connection to Mycroft client...")
client = MessageBusClient()

#--initialize Self etc
print("Initializing Self...")
self_graph, dico, templates, custom_embeddings, embeddings2D=initialize(FILENAMES, GRAPH_PATH, WORDS_PATH, EMBEDDINGS_PATH, EMBEDDINGS2D_PATH)

#---rescale 2D embeddings if needed, depending space
embeddings2D=EMBEDDINGS_SCALE*embeddings2D


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

#set num frames
global num_frames
num_frames=random.randint(MIN_FRAMES, MAX_FRAMES)
#--time tracker 
#start_time = time.time()

#set event id
global event_id
#NOTE: event id for now is hours:min:seconds, but could be based on satellite data rather triggering it?
now = datetime.now()
event_id=now.strftime("%H:%M:%S")

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
    global num_frames
    
    print("Frame {}".format(i))
    
    if i==num_frames-1: #NOTE: currently last frame save & close the plot
        #plt.savefig('./outputs/full_trajectory_event_'+ event_id+ '.png')
        print("Ending Spatial Dance!") #TODO: Send signal to arduino to stop roomba trajectory ?
        plt.close()
    else:
        #---listen to arduino
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
                    #means a turn happened, so will read aloud closer previous point (beware, a lil delay as look at previous point!)
                    #get idx and distance nearest concept of this point
                    idx, dist=nearest_concept(embeddings2D, trajectory[-1])
                    #get word attached to that idx
                    new_closer_concept=list(custom_embeddings.keys())[idx]
                    #NOTE: Refer to the trajectory points values to adjust EMBEDDINGS_BOUND, else would always output same concept
                    print("--looking at trajectory point {}. Here is {}".format(trajectory[-1], new_closer_concept))
                    #say it aloud 
                    client.emit(Message('speak', data={'utterance': new_closer_concept}))
                    
                    #--update event data
                    # save data of close concepts and distance
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
    #NOTE: may have to work with sub trajectory if too big?

    # =============================================================================
    #--1--  Extract 3 Closer concepts
    # =============================================================================
    print("-step 1--Extract 3 closer concepts")
    keys=list(event_data.keys())
    values=list(event_data.values())
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
    haiku=generate_haiku(trinity, templates, dico)
    client.emit(Message('speak', data={'utterance': haiku}))
    #save it
    with open(READING_EVENT_FOLDER+ "haiku_event_"+ event_id+ '.txt', 'w+') as f:
        f.writelines(haiku.split(";"))

    # =============================================================================
    #--3-- Redefine embeddings of these 3 concepts
    # =============================================================================
    print("-step 3---Redefine embeddings of these 3 concepts")
    custom_embeddings=redefine_embeddings(custom_embeddings, trinity)
    #save it:
    with open(EMBEDDINGS_PATH, 'w') as fp:
        json.dump(custom_embeddings, fp)

    return trinity, trinity_trajectory, custom_embeddings, haiku


# =============================================================================
# Actual Script running in loop
# =============================================================================

while True:
    print("=============================================================================")
    print("****** Launching a new RITUAL ******+")
    print("=============================================================================")

    print("=============================================================================")
    print("****** SPATIAL DANCE ******+")
    print("=============================================================================")
    # listen to Arduino trajectory in real time, save coordinates and draw graph
    #NOTE: currently stop listening after a certain number of frames. Could also be related to an ending signal (if arduino sends it...)
    plt.figure(figsize=(10,5))
    #compute for how many frames fo the ritual
    num_frames=random.randint(MIN_FRAMES, MAX_FRAMES)
    print("Performing spatial ritual for {} frames".format(num_frames))
    ani = FuncAnimation(plt.gcf(), spatial_ritual, frames=num_frames, interval=INTERVAL_LISTEN, repeat=False) 
    plt.show(block=True)
    trajectory = trajectory[:-1] #because the trajectory had one more point than when wee looked for concepts...
    print("Trajectory of length {}".format(len(trajectory)))

    print("=============================================================================")
    print("****** SPIRITUAL READING ****** ")
    print("=============================================================================")
    trinity, trinity_trajectory, custom_embeddings, haiku=reading_event(trajectory, custom_embeddings, embeddings2D, event_data)

    print("=============================================================================")
    print("****** ENDING ******+")
    print("=============================================================================")
    print("Save new Event Chart")
    #--visualise Event Chart
    visualize_event_chart(trajectory, trinity_trajectory, haiku, event_id=event_id, output_folder=READING_EVENT_FOLDER)
    print("Saved new Event Chart!")

    #--reinit some variables before next ritual
    reinit()
    print("reinitialized")






#-------------------------------------------------
#---------OLD CODE TEMPORARY KEEP 

# laod JSON structure
# with open('sensordata.json') as jf:
#     data_archive = json.load(jf)

# basically runs this script in a loop ? Need?
#client.run_forever()

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
    #         else:#NOTE: Currently too often same concept closer to all>>> change this! Rather ok if same?
    #             j=close_concepts.index(key)
    #             if dist<distances[j]:#update distance #although risk one closer to several
    #                 distances[j]=dist
    #                 trajectory_points[j]=point
    # assert len(distances)==len(close_concepts)==len(trajectory_points)


    #     # =============================================================================
    # #--step 1-- Extract Sub Trajectory ()
    # # =============================================================================
    # max_num_points=7 #TBD
    # extract_sub_trajectory =False 
    # if extract_sub_trajectory and len(trajectory)>max_num_points:
    #     extracted_trajectory=trajectory
    #     num_points=max_num_points
    #     start=random.randint(0,num_points-max_num_points)
    #     extracted_trajectory=trajectory[start:start+max_num_points]
    #     print("Extracted a trajectory of length {}".format(max_num_points))
    # else:
    #     extracted_trajectory=trajectory