
import json
import matplotlib.pyplot as plt
import math
import numpy as np
import keyboard

def get_trajectory():
    """
    From the list of distances and angles, get the trajectory.

    """
    with open('sensordata.json', 'r') as outfile:
                sensordata=json.load(outfile)
    #data
    distances=sensordata["distances"] 
    angles=sensordata["angles"] #in degree, beware
    #initialise
    num_points=len(distances)
    position=np.array([0,0])
    points=np.zeros((num_points,2), dtype=float)
    points[0,:]=position
    angle=0
    assert len(distances)==len(angles)

    for t in range(num_points-1):
        #new angle, in radian; accumulated angle relative to "North" (not necessarily the real North but the starting North haha)
        angle+=math.pi*float(angles[t])/180
        #compute new position
        position = position +float(distances[t])* np.array([- math.sin(angle), math.cos(angle)])
        #update points with last point
        points[t+1,:]=position
     
    return points



def draw(data, title):
    """
    Draw the pattern given the list of points.
    """
    plt.figure(figsize=(10,5))
    plt.plot(data[:,0],data[:,1], color="deeppink", marker="2",markevery=1, markersize=6, markeredgecolor="limegreen")
    #show
    plt.show()
    #or save it (have to choose)
    #plt.savefig(title+'.png')
    #plt.close()

def draw_real_time(data, title):
    """
    Draw the pattern given the list of points in real time
    """

    interval_time=2#in seconds
    plt.ion()
    plt.show()
    max_iteration=50
    #while not keyboard.is_pressed('q'):#quit when press q
    for i in range(max_iteration):
        plt.figure(figsize=(10,5))
        plt.plot(data[i, :,0],data[i, :,1], color="deeppink", marker="2",markevery=1, markersize=6, markeredgecolor="limegreen")
        plt.pause(interval_time)
        plt.clf()
    #save it at end ?
    #plt.savefig(title+'.png')
    #plt.close()

#Test it
points_rnd=np.random.rand(50, 10,2)
draw_real_time(points_rnd, "Blipblop")




def get_pattern(title):
    points=get_trajectory()
    #print(points)
    draw(points, title)


get_pattern("pattern")



