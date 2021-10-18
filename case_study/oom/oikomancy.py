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
######## 
# TODO: Improve 2D embeddng projection
# TODO: What to do with words having 2 components or 3 even... torch.Size([2, 768])
# TODO: Modify back gpt2 model embeddings & test effect in generation

# ----------------------IMPORTS------------------------------------------
from mycroft_bus_client import MessageBusClient, Message
from string import punctuation
import random
import json
import re
import numpy as np
from utils import (
    read,
    visualize_event_chart,
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
# PARAMETERS to Update/Tune
# =============================================================================
# ------------------PATHS----------
GRAPH_PATH = "/home/unfamiliarconvenient/.mycroft/fallback-associative/graph.json"  # This path is temporary, it should refer to the fallbackassociative skill folder: /home/unfamiliarconvenient/.mycroft/fallback-associative/graph.json"
WORDS_PATH = "./data/"  # Modify when...
EMBEDDINGS_PATH = "./custom_embeddings.json"  # where save words embeddings
EMBEDDINGS2D_PATH = "./custom_embeddings2D.npy"  # where save words embeddings
OUTPUT_FOLDER = "./outputs/"

# --------------PARAMETERS------------------------------
# to decide length trajectory roomba, num frame between a min and a max:
MAX_FRAMES = 150
MIN_FRAMES = 100
# sensitivity threshold to judge if 3 points are almost aligned
COLINEARITY_THRESHOLD = 0.05
# Approximate room radius, to scale the embedding
ROOM_RADIUS = 3
# When will listen to new message from Roomba
INTERVAL_LISTEN = 721 #NB: Could increase if want less point
# roomba sattelite threshold
SAT_THRESHOLD = 20
# number of initial frames to warm up roomba, before word reading etc.
WARM_UP=16
# maximum number of concept roomba is saying
MAX_WORDS_PER_EVENT=23
# If redefine gpt2 embeddings
REDEFINE_EMBEDDINGS=True 
# --if want to save visualisation Event Chart
VISUALIZE = False

# =============================================================================
# INITIALISATION
# =============================================================================

print("=============================================================================")
print("*** INITIALISATION ***")
print("=============================================================================")

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
    GRAPH_PATH, WORDS_PATH, EMBEDDINGS_PATH, EMBEDDINGS2D_PATH
)
num_concepts=len(list(self_graph.keys()))

# trajectory keeps only the relevant points (i.e. "turns"):
global trajectory
trajectory = []
# event_data save concepts related to the space reading, 
# with their associated distance & closer points in the trajectory
global event_data
event_data = dict()
# indices of concepts already said loud to avoid repetition
global idx_event_concepts
idx_event_concepts=[]
# scaling factor to downscale the trajectory coordinates
# want trajectory coordinates between -1 and 1 !
global scaling_factor
scaling_factor = ROOM_RADIUS * 1000
# set num frames for reading
global num_frames
num_frames = random.randint(MIN_FRAMES, MAX_FRAMES)
#  keep track when need end reading
global end_reading
end_reading=False
# set event id
global event_id
now = datetime.now()
event_id = now.strftime("%H:%M:%S")

# Bluetooth parameters
# Module address
ROO_ADDR = "98:D3:31:F3:F6:97"
# Connection port
port = 1
# incoming data cluster size
size = 1
# Bluetooth socket
global sock

print("Ready to start the Ritual !")

# =============================================================================
# Connect to Arduino, Listen to Arduino, Send Shutdown signal
# =============================================================================


def roomba_connect():
    """
    Connect to Arduino
    """
    global sock
    connected = False
    while not connected:
        try:
            print("Connecting to Roo")
            sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            sock.connect((ROO_ADDR, port))
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
    """
    Listen to Arduino
    Return the message that received
    """
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

def ending_dance():
    """
    Send Shutdown signal to Arduino
    To stop Roomba Trajectory
    """
    global end_reading
    global sock
    global trigger
    end_reading=True

    print("Ending Spatial Dance!")
    # Send signal to arduino to stop roomba trajectory
    sock.send("d")
    sleep(1)
    trigger = False


# =============================================================================
# Spatial Ritual (& Arduino Listener)
# =============================================================================


def spatial_ritual(i, trajectory, end_reading):
    """
    Spatial Ritual:
    - Listen to coordinate Sent by Arduino
    - If new interesting point (ie turn), would look up closer Self concept and say it aloud
    - Save the event data for future use

    Args:
        i, step of the trajectory
        trajectory: list of points saved
        end_reading: boolean if shall end the reading
        event_data: dictionnary whose keys are string (concepts) and values are list [float, int] (which are distances, reps. idx of corresponding trajectory point in our case)
    
    Output:
        trajectory: updated trajectory
        end_reading: boolean if shall end the reading
    """

    global event_data
    global idx_event_concepts

    print("Frame {}".format(i-WARM_UP))

    # ---listen to Arduino
    message = roomba_listen()

    # if message contains coordinates
    if message and message != "clearning" and message != "docking":

        x, y = message.split(",", 1)
        x = float(x)
        y = float(y)

        # ----Check if new point +/- aligned with previous 2 points of trajectory (if trajectory length >2...)
        new_point = [x / scaling_factor, y/ scaling_factor]

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
                # replace last point with new point
                # NOTE: thus removes intermediary points which are aligned
                trajectory[-1] = new_point

            else:
                # a turn happened ! so read aloud closer previous point
                # get idx and distance nearest concept of this point
                idx, dist, neue = nearest_concept(embeddings2D, trajectory[-1], idx_event_concepts)
                
                if neue: # say aloud only if new concept
                    # get word attached to that idx
                    new_closer_concept = list(custom_embeddings.keys())[idx]
                    print(
                        "--Trajectory point {}  understood as {}".format(
                            trajectory[-1], new_closer_concept
                        )
                    )
                    # say it aloud
                    client.emit(
                        Message("speak", data={"utterance": new_closer_concept})
                    )

                    # --update event data
                    event_data[new_closer_concept]=[dist, len(trajectory) - 1]
                    idx_event_concepts.append(idx)

                    # add new point to trajectory
                    trajectory.append(new_point)
                else: # if no new concept, end reading
                    end_reading=True

        else:
            trajectory.append(new_point)
    
    return trajectory, end_reading

# =============================================================================
# Reading event
# =============================================================================


def reading_event(trajectory, custom_embeddings, embeddings2D, event_data):
    """
    Reading of the trajectory
    Args:
        trajectory: list of points in 2D space send by roomba
        custom_embeddings: embedding dictionary of self concepts
        embeddings2D: 2D embeddings
        event_data: dictionnary whose keys are string (concepts) and values are list [float, int] (which are distances, reps. idx of corresponding trajectory point in our case)
    Output:
        trinity: 3 closer self concepts selected
        custom_embeddings: redefined embedding dictionary

    """

    num_points = len(trajectory)
    print("Reading Event of a trajectory of length {}".format(num_points))

    # --step 1--  Extract 3 Closer concepts
    print("-step 1--Extract 3 closer concepts")
    keys = list(event_data.keys())
    values = list(event_data.values())
    distances = [val[0] for val in values]
    indices = np.argsort(distances)[:3]
    trinity = [keys[i] for i in indices]
    trinity_idx = [values[i][1] for i in indices]
    trinity_trajectory = [trajectory[idx] for idx in trinity_idx]
    print("Event trinity Core: {}".format(trinity))
    print(
        "In correspondance with the 3 domesticoCosmic points n° {}".format(trinity_idx)
    )

    # --step 2-- Haiku generation and Reading
    print("-step 2---Generate Haiku")
    haiku = generate_haiku(trinity.copy(), templates, dico, gingerParser) #copy trinity to avoid affected
    client.emit(Message("speak", data={"utterance": haiku}))

    # --step 3-- Redefine embeddings of these 3 concepts
    print("-step 3---Redefine embeddings of these 3 concepts")
    if len(trinity)==3 and REDEFINE_EMBEDDINGS: # ensure 3 holy concepts
        custom_embeddings = redefine_embeddings(custom_embeddings, trinity)
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
            print("=========================================")
            print("****** launching a new RITUAL ******+")
            print("============================================")

            print("=========================================")
            print("****** SPATIAL DANCE ******+")
            print("=========================================")

            #--step 0---number frame of the ritual including warm up
            # NOTE: num frames bounded by nb words in self graph, else will run out of concepts
            num_frames = min(num_concepts-1, random.randint(MIN_FRAMES, MAX_FRAMES))
            total_frames=num_frames+WARM_UP
            
            #---step 1--spatial ritual
            print("Performing spatial ritual for {} warm up and {} legit frames".format(WARM_UP, num_frames))
            count_frame=0
            while (count_frame<total_frames) and (not end_reading):
                if count_frame>=WARM_UP:
                    trajectory, end_reading= spatial_ritual(count_frame, trajectory, end_reading)
                count_frame+=1
                time.sleep(INTERVAL_LISTEN/1000)#INTERVAL_LISTEN is in ms

            #----ending spatial ritual signal
            ending_dance()

            trajectory = trajectory[:-1]
            print("Final trajectory of length {}".format(len(trajectory)))

            #---step 2--spiritual reading
            print("==============================================")
            print("****** SPIRITUAL READING ****** ")
            print("==============================================")
            trinity, trinity_trajectory, custom_embeddings, haiku = reading_event(
                trajectory, custom_embeddings, embeddings2D, event_data
            )

            #---step 3--saving stuff
            print("Save Event Data...")
            full_event_data=dict()
            full_event_data["haiku"]=haiku
            full_event_data["data"]=event_data
            event_data_path=OUTPUT_FOLDER + event_id + "_event_data.json"
            with open(event_data_path, "w+") as fp:
                json.dump(full_event_data, fp)

            if VISUALIZE:
                print("Save Event Chart...")
                # --visualise Event Chart
                chart_path=OUTPUT_FOLDER + event_id + "_event_chart.png"
                visualize_event_chart(
                    trajectory,
                    trinity_trajectory,
                    haiku,
                    output_path=chart_path
                )

            print("Reinitialization...")
            # --reinit some variables before next ritual
            trajectory, event_data, idx_event_concepts, end_reading = [], dict(), [], False
            print("==============================================")
            print("****** END ******+")
            print("==============================================")

    except KeyboardInterrupt:
        print("closing")
        sock.close()
        sys.exit()


