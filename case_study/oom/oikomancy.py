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
######## NOW:
# TODO: Make embeddings more spread?

######## SOON should do:
# TODO: Improve 2D embeddng projection
# TODO: What to do with words having 2 components or 3 even... torch.Size([2, 768])
# TODO: Need CLEAN self graph? Stricter criteria to add self graph. As see there are letters like c
# TODO: Modify back gpt2 model embeddings & test effect in generation
# TODO: Visualisation better
# TODO: Other tunings, parameters etc.

# ----------------------IMPORTS------------------------------------------
from mycroft_bus_client import MessageBusClient, Message
from string import punctuation
import random
import json
import re
import numpy as np
from utils import (
    pick_template,
    read,
    visualize_event_chart,
    update_event_data,
    generate_haiku,
    nearest_concept,
    initialize,
    approximately_colinear,
    redefine_embeddings,
)
import time
import bluetooth
from time import sleep
import sys
from datetime import datetime

from gingerit.gingerit import GingerIt

gingerParser = GingerIt()  # for grammar

# =============================================================================
# PARAMETERS to Update or tune
# =============================================================================
# ------------------PATHS----------
# #NOTE: Update Paths
GRAPH_PATH = "/home/unfamiliarconvenient/.mycroft/fallback-associative/graph.json"  # This path is temporary, it should refer to the fallbackassociative skill folder: /home/unfamiliarconvenient/.mycroft/fallback-associative/graph.json"
WORDS_PATH = "./data/"  # Modify when...
EMBEDDINGS_PATH = "./custom_embeddings.json"  # where save words embeddings
EMBEDDINGS2D_PATH = "./custom_embeddings2D.npy"  # where save words embeddings
OUTPUT_FOLDER = "./outputs/"

# str(pathlib.Path(__file__).parent.absolute()) #may use path lib...

# ---------------CONSTANTS MAY TUNE------------------------------
# to decide length trajectory roomba:
MAX_FRAMES = 150
MIN_FRAMES = 100
# threshold to judge if 3 points are almost aligned; sensitivity may be tuned
COLINEARITY_THRESHOLD = 0.05
# NOTE: change the scale embeddings depending on the room size.
ROOM_RADIUS = 3
# How often frames are drawn in the graph / Depends how often Roomba sends data
INTERVAL_LISTEN = 721 #NB: Could increase if want less point
# Roomba sattelite threshold
SAT_THRESHOLD = 20

WARM_UP=20 #number of initial frame to warm up for the roomba, where will not read a word just go to a point in space.

MAX_WORDS_PER_EVENT=23  #maximum number of concepts roomba is saying #NOTE: Could vary it too

VISUALIZE=False

# =============================================================================
# INITIALISATION
# =============================================================================

print("=============================================================================")
print("*** INITIALISATION ***")
print("=============================================================================")

# --init constants
FILENAMES = [
    "A",
    "Ad1",
    "Ad2",
    "Ad3",
    "V",
    "Vt",
    "V2",
    "V+",
    "P",
    "Pf",
    "P0",
    "PR0",
    "PR0a",
    "PR1a",
    "PR1",
    "N",
    "N2",
    "Nf",
    "Nfa",
    "Na",
    "Aa",
    "Va",
    "Nfa",
    "ism",
    "Duo",
    "Nf",
    "Ma",
    "S",
    "Sc",
    "ESS",
    "ASA",
    "ABL",
    "QU",
    "Tion",
    "Duoa",
]

# use Roomba to trigger graph drawing
global trigger
trigger = False

# --import Message Bus client to communicate with Mycroft's guts
print("Setting up connection to Mycroft client...")
client = MessageBusClient()
client.run_in_thread()

# --initialize Self etc
print("Initializing Self...")
self_graph, dico, templates, custom_embeddings, embeddings2D = initialize(
    FILENAMES, GRAPH_PATH, WORDS_PATH, EMBEDDINGS_PATH, EMBEDDINGS2D_PATH
)
num_concepts=len(list(self_graph.keys()))


# --to save all points trajectory
global x_vals
global y_vals
x_vals = []
y_vals = []
# --to save MAIN points trajectory (only "turns")
global trajectory
trajectory = []
# --to save concepts related to the space reading, with their associated distance & closer points in the trajectory
global event_data
event_data = dict()
global idx_event_concepts #keep track of the concepts said in an even to avoid repetition
idx_event_concepts=[]

#to downscale the trajectory coordinates; want them between -1 and 1 always
global scaling_factor
scaling_factor = ROOM_RADIUS * 1000

# set num frames
global num_frames
num_frames = random.randint(MIN_FRAMES, MAX_FRAMES)

# --time tracker
# start_time = time.time()

global REDEFINE_EMBEDDINGS
REDEFINE_EMBEDDINGS=True 

global end_reading
end_reading=False

# set event id
global event_id
# NOTE: event id for now is hours:min:seconds, but could be based on satellite data rather triggering it?
now = datetime.now()
event_id = now.strftime("%H:%M:%S")

# Bluetooth parameters
# Module address
roo_addr = "98:D3:31:F3:F6:97"
# Connection port
port = 1
# incoming data cluster size
size = 1
# Bluetooth socket
global sock

print("Ready to start the Ritual !")

# =============================================================================
# Connect to Arduino
# =============================================================================


def roomba_connect():
    global sock
    connected = False
    while not connected:
        try:
            print("Connecting to Roo")
            sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            sock.connect((roo_addr, port))
            connected = True
            sent = False
            if not sent:
                sock.send(str(SAT_THRESHOLD))
                sleep(1)
                sent = True
            print("Connected to Roomba. Awaiting Data.")
            client.emit(Message("speak", data={"utterance": "Connected to Roo"}))
        except Exception as e:
            print(e)
            print("Connection failed, retrying in 5 seconds...")
            sleep(5)


def roomba_listen():
    global sock
    message = ""
    while ";" not in message:
        try:
            data = sock.recv(size).decode()
            if not data.isspace():
                message += data
        except:
            print("Socket disconnected. Attempting to reconnect")
            roomba_connect()
    message = message[:-1]
    print(message)
    return message


# =============================================================================
# Reinit
# =============================================================================


def reinit():
    # --init some variables:
    # --to save points trajectory
    global x_vals
    global y_vals
    x_vals = []
    y_vals = []
    global trajectory
    trajectory = []  # for MAIN points
    global event_data
    event_data = dict()
    global idx_event_concepts
    idx_event_concepts=[]
    global end_reading
    end_reading=False


# =============================================================================
# Spatial Ritual (& Arduino Listener)
# =============================================================================


def ending_dance():
    global end_reading
    global sock
    global trigger
    end_reading=True

    print("Ending Spatial Dance!")
    # Send signal to arduino to stop roomba trajectory
    sock.send("d")
    sleep(1)
    trigger = False

def spatial_ritual(i, trajectory, end_reading):
    """
    Spatial Ritual:
    - Listen to coordinate Sent by Arduino
    - If new interesting point (ie turn), would look up closer Self concept and say it aloud
    - Save the event data for future use

    Input: int, step of the trajectory
    """

    global x_vals
    global y_vals
    global event_data
    global idx_event_concepts
    global scaling_factor

    print("Frame {}".format(i-WARM_UP))

    # ---listen to Arduino
    message = roomba_listen()

    # if message contains coordinates
    if message and message != "clearning" and message != "docking":

        x, y = message.split(",", 1)
        x = float(x)
        y = float(y)

        ######UPDATING SCALING FACTOR ?
        # #---sanity check to ensure room radius is good, else update room radius:
        # #NOTE: although rescaling trajectory during event may fuck up the coordinates !
        # if x>scaling_factor or x<-scaling_factor :
        #     scaling_factor = scaling_factor, abs(x) + 1000 #add a margin of 1 meter
        # if y>scaling_factor or y<-scaling_factor:
        #     scaling_factor = max(scaling_factor, abs(y) + 1000) #add a margin of 1 meter rel where is
        

        # --save data trajectory after rescaling
        #NOTE: rescale here coordinates for them to be between -1 and 1; may adjust it ?
        x_vals.append(x / scaling_factor)
        y_vals.append(y / scaling_factor)

        # ----Check if new point +/- aligned with previous 2 points of trajectory (if trajectory length >2...)
        new_point = [x, y]

        # check if new point aligned with 2 previous point if nb point >=2
        # and if it has not reached the maximum concept number per reading:
        if len(trajectory) >= 2 and len(idx_event_concepts)<MAX_WORDS_PER_EVENT:
            aligned = approximately_colinear(
                trajectory[-2],
                trajectory[-1],
                new_point,
                threshold=COLINEARITY_THRESHOLD,
            )
            if aligned:
                # new point aligned with last 2, so replace last point with new point:
                trajectory[-1] = new_point
                # NOTE: This is a way to clean the trajectory, in the sense it removes intermediary points on the same line,

            else:

                # means a turn happened, so will read aloud closer previous point (beware, a lil delay as look at previous point!)
                # get idx and distance nearest concept of this point
                idx, dist, neue = nearest_concept(embeddings2D, trajectory[-1], idx_event_concepts)
                
                if neue: #say concept only if new concept
                    # get word attached to that idx
                    new_closer_concept = list(custom_embeddings.keys())[idx]
                    print(
                        "--looking at trajectory point {}. Here is {}".format(
                            trajectory[-1], new_closer_concept
                        )
                    )
                    # say it aloud
                    client.emit(
                        Message("speak", data={"utterance": new_closer_concept})
                    )

                    # --update event data
                    # save data of close concepts and distance
                    event_data = update_event_data(
                        new_closer_concept, dist, len(trajectory) - 1, event_data
                    )
                    idx_event_concepts.append(idx)

                    # add new point to trajectory (at least temporarily)
                    trajectory.append(new_point)
                else:#no new concept, end reading
                    end_reading=True

        else:  # second point in traj
            trajectory.append(new_point)
    
    return trajectory, end_reading

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

    num_points = len(trajectory)
    print("Reading Event of a trajectory of length {}".format(num_points))
    # NOTE: may have to work with sub trajectory if too big?

    # =============================================================================
    # --1--  Extract 3 Closer concepts
    # =============================================================================
    print("-step 1--Extract 3 closer concepts")
    #NOTE: here do not have to choose closer concepts necessarily?
    keys = list(event_data.keys())
    values = list(event_data.values())
    distances = [val[0] for val in values]
    indices = np.argsort(distances)[:3]
    trinity = [keys[i] for i in indices]
    trinity_idx = [values[i][1] for i in indices]
    trinity_trajectory = [trajectory[idx] for idx in trinity_idx]
    #check points are different:
    assert not (trinity[0]==trinity[1] or trinity[0]==trinity[2] or trinity[1]==trinity[2])
    print("Event trinity Core: {}".format(trinity))
    print(
        "In correspondance with the 3 domesticoCosmic points n° {}".format(trinity_idx)
    )

    # =============================================================================
    # --2-- Haiku generation and Reading
    # =============================================================================
    print("-step 2---Generate Haiku")
    haiku = generate_haiku(trinity.copy(), templates, dico, gingerParser) #copy trinity to avoid affected
    client.emit(Message("speak", data={"utterance": haiku}))
    # save it: no, now save it in dictionnary
    # with open(OUTPUT_FOLDER + "haiku_event_" + event_id + ".txt", "w+") as f:
    #    f.writelines(haiku.split(";"))

    # =============================================================================
    # --3-- Redefine embeddings of these 3 concepts
    # =============================================================================
    print("-step 3---Redefine embeddings of these 3 concepts")
    if len(trinity)==3 and REDEFINE_EMBEDDINGS: #ensure there are 3 concepts before redefining embeddings
        custom_embeddings = redefine_embeddings(custom_embeddings, trinity)
        # save it:
        with open(EMBEDDINGS_PATH, "w") as fp:
            json.dump(custom_embeddings, fp)

    return trinity, trinity_trajectory, custom_embeddings, haiku


# =============================================================================
# Connect to Roomba
# =============================================================================

roomba_connect()

# =============================================================================
# Actual Script running in loop
# =============================================================================

while True:
    global sock


    try:
        cleaning = roomba_listen()
        if cleaning == "cleaning":
            print("Trigger!")
            trigger = True

        if trigger:
            print(
                "============================================================================="
            )
            print("****** Launching a new RITUAL ******+")
            print(
                "============================================================================="
            )

            print(
                "============================================================================="
            )
            print("****** SPATIAL DANCE ******+")
            print(
                "============================================================================="
            )
            # listen to Arduino trajectory in real time, save coordinates and draw graph
            # NOTE: currently stop listening after a certain number of frames. Could also be related to an ending signal (if arduino sends it...)

            #---number frame ritual including warm up
            # #max num frames of the nb words in self graph, else will run out of concepts...
            num_frames = min(num_concepts-1, random.randint(MIN_FRAMES, MAX_FRAMES))
            total_frames=num_frames+WARM_UP
            
            #---spatial ritual
            print("Performing spatial ritual for {} warm up and {} legit frames".format(WARM_UP, num_frames))
            count_frame=0
            while (count_frame<total_frames) and (not end_reading):
                if count_frame>=WARM_UP:
                    trajectory, end_reading= spatial_ritual(count_frame, trajectory, end_reading)
                count_frame+=1
                time.sleep(INTERVAL_LISTEN/1000)#INTERVAL_LISTEN is in ms

            #Sending ending dance signals
            ending_dance()

            trajectory = trajectory[
                :-1
            ]  # because the trajectory had one more point than when wee looked for concepts...
            print("Final trajectory of length {}".format(len(trajectory)))

            print(
                "============================================================================="
            )
            print("****** SPIRITUAL READING ****** ")
            print(
                "============================================================================="
            )
            trinity, trinity_trajectory, custom_embeddings, haiku = reading_event(
                trajectory, custom_embeddings, embeddings2D, event_data
            )

            print(
                "============================================================================="
            )
            print("****** ENDING ******+")
            print(
                "============================================================================="
            )
            print("Save Event Data...")
            #NOTE: Full event data is a dictionnary which contain both the haiku generated and the event data (event_data):
            full_event_data=dict()
            full_event_data["haiku"]=haiku
            full_event_data["data"]=event_data
            event_data_path=OUTPUT_FOLDER + event_id + "_event_data.json"
            with open(event_data_path, "w+") as fp:
                json.dump(full_event_data, fp)

            print("Save Event Chart...")
            # --visualise Event Chart
            chart_path=OUTPUT_FOLDER + event_id + "_event_chart.png"
            visualize_event_chart(
                trajectory,
                trinity_trajectory,
                haiku,
                output_path=chart_path
            )
            print("Saved new Event Chart!")

            # --reinit some variables before next ritual
            reinit()
            print("reinitialized")

    except KeyboardInterrupt:
        print("closing")
        sock.close()
        sys.exit()


