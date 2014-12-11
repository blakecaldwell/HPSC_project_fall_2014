#!/usr/bin/python

# Script to convert slog2 text to a DAG with weighted edges
# and find the critical path graph.
# DJM 12/2014

import os
import sys
import re
import argparse
import json
import itertools
import networkx as nx
#from BTrees.OOBTree import OOBTree
from collections import defaultdict
from networkx.readwrite import json_graph

sys.path.append('/home/dami9546/zodb/lib/python2.7/site-packages')
from BTrees.OOBTree import OOBTree

class DAG(object):
    """docstring for DAG"""

    def __init__(self, filename):
        super(DAG, self).__init__()
        self.filename = filename

    def slog2Dict(self):
        # Defaultdict must be callable, so use lambda
        rank_dict = rank_dict = defaultdict(lambda: defaultdict(lambda: OOBTree()))

        # Initialize the graph
        G = nx.DiGraph()

        with open(self.filename, 'r') as infile:
            strings1 = ("name=MPI_Send()", "Primitive")
            strings2 = ("name=MPI_Wait()", "Primitive")

            for line in infile:

                # Do for MPI_Send
                if all(x in line for x in strings1):
                    # Parse the string to get important values
                    event = re.search('^([0-9]+)', line).group(1)
                    event = int(event)
                    grp = re.search('from ([0-9]+) to ([0-9]+)', line)
                    source = int(grp.group(1))
                    dest = int(grp.group(2))
                    size = re.search('size ([0-9]+)', line).group(1)
                    size = int(size)
                    t_grp = re.search('TimeBBox\((\d+.\d+),(\d+.\d+)\)', line)
                    tBBox = [float(t_grp.group(1)), float(t_grp.group(2))]

                    # Assemble the dictionary and add to defaultdict(defaultdict(OOBtree))
                    attr_dict = {'dest':dest, 'msg_size':size, 'tBBox_s':tBBox[0],
                                    'tBBox_e':tBBox[1]}

                    rank_dict[source]['MPI_Send'][event] = attr_dict
                    # Now add node to nascent graph.
                    node_name = '_'.join((str(source), str(event)))
                    G.add_node(node_name)
            
                # Do for MPI_Wait
                if all(x in line for x in strings2):
                    # Parse the string to get important values
                    event = re.search('^([0-9]+)', line).group(1)
                    event = int(event)
                    grp = re.search('\]: \] \((\d+.\d+), (\d+)\) \((\d+.\d+), (\d+)\)', line)
                    source = int(grp.group(2))
                    dest = int(grp.group(2))
                    t_grp = re.search('TimeBBox\((\d+.\d+),(\d+.\d+)\)', line)
                    tBBox = [float(t_grp.group(1)), float(t_grp.group(2))]

                    # Assemble the dictionary and add to defaultdict(defaultdict(OOBtree))
                    attr_dict = {'dest':dest, 'tBBox_s':tBBox[0],
                                    'tBBox_e':tBBox[1]}

                    rank_dict[source]['MPI_Wait'][event] = attr_dict
                    # Now add node to nascent graph.
                    node_name = '_'.join((str(source), str(event)))
                    G.add_node(node_name)

        return G, rank_dict


    def connectGraph(self, G, rank_dict):
        # Iterate over MPI_Send() nodes
        for src_rank in rank_dict:

            # Now loop over events
            for evnt in rank_dict[src_rank]['MPI_Send']:
                my_dest = rank_dict[src_rank]['MPI_Send'][evnt]['dest']
              #  print type(rank_dict[src_rank]['MPI_Send'])
                try:
                    next_send = rank_dict[my_dest]['MPI_Send'].minKey(evnt)
                except ValueError:
                    if evnt > rank_dict[my_dest]['MPI_Send'].maxKey():
                        pass#    next_send = rank_dict[my_dest]['MPI_Send'].maxKey()
                try:
                    next_wait = rank_dict[my_dest]['MPI_Wait'].minKey(evnt)
                except ValueError:
                   if evnt > rank_dict[my_dest]['MPI_Wait'].maxKey():
                       pass#  next_wait = rank_dict[my_dest]['MPI_Wait'].maxKey()
                try:
                    next_send_1 = rank_dict[my_dest]['MPI_Send'].minKey(next_send)
                except ValueError:
                    pass
                
                my_send_t = rank_dict[src_rank]['MPI_Send'][evnt]['tBBox_e']
                next_send_t = rank_dict[my_dest]['MPI_Send'][next_send]['tBBox_e']
                next_wait_t = rank_dict[my_dest]['MPI_Wait'][next_wait]['tBBox_s']

                if my_send_t <= next_send_t:
                    delta_t = rank_dict[my_dest]['MPI_Send'][next_send]['tBBox_e'] \
                            - rank_dict[src_rank]['MPI_Send'][evnt]['tBBox_s']
                    source_name = '_'.join((str(src_rank), str(evnt)))
                    dest_name = '_'.join((str(my_dest), str(next_send)))

                    G.add_edge(source_name, dest_name, weight=delta_t)

                # Else wait fulfilled first- means path remains on this node
                else:
                    #delta_t_w = rank_dict[my_dest]['MPI_Wait'][next_wait]['tBBox_e'] \
                    #            - rank_dict[src_rank]['MPI_Send'][evnt]['tBBox_s']
                    #source_name = '_'.join((str(src_rank), str(evnt)))
                    #wait_name = '_'.join((str(my_dest), str(next_wait)))

                    #G.add_edge(source_name, wait_name, weight=delta_t_w)

                    # Now add edge from next_wait to next_send
                    delta_t_s = rank_dict[my_dest]['MPI_Send'][next_send_1]['tBBox_e'] \
                                - rank_dict[src_rank]['MPI_Send'][evnt]['tBBox_s']
                    send_name = '_'.join((str(src_rank), str(next_send_1)))

                    G.add_edge(source_name, send_name, weight=delta_t_s)

        return G


    # Now compute the critical (longest) path graph.
    def find_critical(self, G):
        dist = {} # stores [node, distance] pair

        for node in nx.topological_sort(G):
            # pairs of dist,node for all incoming edges
            pairs = [(dist[v][0]+1,v) for v in G.pred[node]]

            if pairs:
                dist[node] = max(pairs)

            else:
                dist[node] = (0, node)

        node,(length,_)  = max(dist.items(), key=lambda x:x[1])
        path = []

        while length > 0:
            path.append(node)
            length,node = dist[node]

        return list(reversed(path))



        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="script to convert slog2 text to DAG")
    parser.add_argument("-i", dest="in_file",
                        help="read slog2 text FILE", metavar="FILE")
    parser.add_argument("-o", dest="out_file",
                        help="write DAG to JSON FILE", metavar="FILE")
    parser.add_argument("-j", dest="crit_file",
                        help="write critical path to JSON FILE", metavar="FILE")


    args = parser.parse_args()

    D = DAG(args.in_file)
    Grf, H = D.slog2Dict()
    I = D.connectGraph(Grf,H)
    crit_path = D.find_critical(Grf)

    with open(args.crit_file, 'w') as c:
      json.dump(crit_path, c)

    for cycle in nx.simple_cycles(Grf):
        print cycle


    graph_data = json_graph.node_link_data(I)
    
    with open(args.out_file, 'w') as f:
        json.dump(graph_data, f, indent=2)
