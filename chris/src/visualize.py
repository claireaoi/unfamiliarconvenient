



######This Script aims to visualize the current state of the Graph as recorded in selfgraph.txt


#TO DO: Better visualisation. Tune parameters aesthetically of graphviz OR change of library

#***********************************************************************REFERENCES***************************************************************************

#######FOR NETWORK creation
#With  NetworkX cf. https://networkx.github.io/documentation/stable/reference/introduction.html  for Network creation
#https://programminghistorian.org/en/lessons/exploring-and-analyzing-network-data-with-python


#######FOR NETWORK visualisation
#Notable examples of dedicated and fully-featured graph visualization tools are Cytoscape, Gephi, Graphviz . Plotly too ?
#Could also use for visualisation: https://pyvis.readthedocs.io/en/latest/
#https://networkx.github.io/documentation/stable/reference/drawing.html

#***********************************************************************INITIALIZATION***************************************************************************

#PARAMETERS:

###IMPORT general
import fire
import numpy as np
import re
import random
import json
import string
import time

#import plotly.graph_objects as go #plotly
import networkx as nx #networkx need install the library: pip install networkx
#To visualize:
import pylab as plt
from networkx.drawing.nx_agraph import graphviz_layout, to_agraph
import pygraphviz as pgv

##STEP 0: Load the self Graph
####selfGraph is a dictionnary, whose keys are concepts, and values are couple (weight, neighbors).
##Neighbors is a dictionnary whose keys are related concepts and values are weights


#***********************************************************************PROCEDURES*************************************************************************
#selfGraph[word][1][nextWord]

def createGraph():
    with open('/home/christopher/mycroft-core/chris/data/selfgraph.txt') as json_file:
        selfGraph = json.load(json_file)
    #Create graph, network entity with networkx
    G = nx.Graph()
    #(1) Add Nodes
    G.add_nodes_from(list(selfGraph.keys()))

    #(2)) Add edges with weight specified directly
    #First, build edge set:
    edgesList=[]
    for node1 in selfGraph.keys():
        for node2 in selfGraph[node1][1]:
            weight12=selfGraph[node1][1][node2]#weight of the edge, relatedness of 2 nodes
            if not [node2, node1, weight12] in edgesList: #as symmetric edges
                edgesList.append([node1, node2, weight12])
    G.add_weighted_edges_from(edgesList)    #G.add_edges_from()   #G.add_edge(2, 3, weight=0.9)

    #(3) Add Attributes Nodes:  attribute data to be in the form dictionary: keys: nodes name, values: attributes.
    #NB: can have different type attributes: nx.set_node_attributes(G, att_dic, 'name_att')
    weightNode={w: selfGraph[w][0] for w in selfGraph.keys()}
    nx.set_node_attributes(G, weightNode, 'relevancy')   #To access them: G.nodes[node]['relevancy']
    #(4) Add Attributes Edges. Dont need for now, as already added the weight in the edges
    #nx.set_edge_attributes(G, weightEdge, 'relatedness')

    #(5)Print Info // Self graph
    print(nx.info(G))
    print('Self Density:', nx.density(G))
    print('Is Self Connected :', nx.is_connected(G))
    components = nx.connected_components(G)
    print('Number of Connected component of Self :', number_connected_components(G))
    largest_component = max(components, key=len)
    subSelf = G.subgraph(largest_component) # Create a "subgraph" of just the largest component
    diameter = nx.diameter(subSelf)
    print('Diameter of largest Connected Component of Self :', diameter)
    #Transitivity, like density, expresses how interconnected a graph is in terms of a ratio of actual over possible connections. Transitivity is the ratio of all triangles over all possible triangles.
    print("Self Transivity:", nx.transitivity(G))
    #Centrality node: Find which nodes are the most important ones in your network.
    degree_dict = dict(G.degree(G.nodes())) #degree is connectivity of each node: how many egde
    nx.set_node_attributes(G, degree_dict, 'degree') #First add degree each nodes as extra attribute
    sorted_degree = sorted(degree_dict.items(), key=itemgetter(1), reverse=True) #sort this degree list
    hubs=""
    for d in sorted_degree[:3]:
        hubs.append("  " + d)
    print("Three bigger Hubs in Self: " +  hubs)
    #Other centralities than just hubs:
    #EIgenvector Centrality is a kind of extension of degree—it looks at a combination of a node’s edges and the edges of that node’s neighbors. Eigenvector centrality cares if you are a hub, but it also cares how many hubs you are connected to. Like second order connectivity
    #Betweenness centrality  Betweenness centrality looks at all the shortest paths that pass through a particular node (see above).
    betweenness_dict = nx.betweenness_centrality(G)
    eigenvector_dict = nx.eigenvector_centrality(G)
    nx.set_node_attributes(G, betweenness_dict, 'betweenness')     # Assign each to an attribute in your network
    nx.set_node_attributes(G, eigenvector_dict, 'eigenvector')
    sorted_betweenness = sorted(betweenness_dict.items(), key=itemgetter(1), reverse=True)
    print("Top 3 Central Concepts in Self:")
    for b in sorted_betweenness[:3]:
        print(b)
    #Community detection within Self: with modularity, different cluster >>Clustered Self

    return G

def drawGraph():
    #Draw Graph with plotly
    G=createGraph() #create it with above procedure
    #Conversion to be readable by graphviz #agraph is Interface to pygraphviz AGraph class.
    A = to_agraph(G) #agraph is Interface to pygraphviz AGraph class.
    #Rendering via Graphviz. >>Draw Attributes!
    A.layout('dot')
    #Saving
    A.draw('selfGraph.png')
