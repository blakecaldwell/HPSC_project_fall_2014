#!/usr/bin/python

# Script to convert slog2 text to a DAG with weighted edges
# and find the critical path graph.
# DJM 12/2014

import os
import sys
import glob
import re
import argparse
import json
import logging
import networkx as nx
from collections import defaultdict
from networkx.readwrite import json_graph
sys.path.append('/home/dami9546/zodb/lib/python2.7/site-packages')
from BTrees.OOBTree import OOBTree
from BTrees.check import check

class DAG(object):
    """docstring for DAG"""

    def __init__(self, filename, host_mapping):
        super(DAG, self).__init__()
        self.filename = filename
        self.host_mapping = host_mapping

        global mapping_dict
        mapping_dict = {}
        strings = ("Hostname:", "Cart_rank:")
        with open(self.host_mapping, 'r') as map:
            for line in map:
                if all(x in line for x in strings):
                    hostname = re.search('Hostname:(\w+\d+)', line)
                    rank = re.search('Cart_rank:\s+(\d+)', line)
                    hostname = hostname.group(1)
                    rank = int(rank.group(1))
                    mapping_dict[rank] = hostname

    def slog2Dict(self):
        # Defaultdict must be callable, so use lambda
        rank_dict = rank_dict = defaultdict(lambda: defaultdict(lambda: OOBTree(dict())))

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
                    t_grp = re.search('TimeBBox\(([0-9]+.[0-9]+),([0-9]+.[0-9]+)\)', line)
                    tBBox = [float(t_grp.group(1)), float(t_grp.group(2))]
                    # Assemble the dictionary and add to defaultdict(defaultdict(OOBtree))
                    attr_dict = {'dest':dest, 'msg_size':size, 'tBBox_s':tBBox[0],
                                    'tBBox_e':tBBox[1], 'event':event}
                    rank_dict[source]['MPI_Send'][tBBox[1]] = attr_dict
                    # Now add node to nascent graph.
                    host = mapping_dict[source]
                    node_name = '_'.join((str(host), str(tBBox[1])))
                    G.add_node(node_name)
            
                # Do for MPI_Wait
                elif all(x in line for x in strings2):
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
                                    'tBBox_e':tBBox[1], 'event': event}
                    rank_dict[source]['MPI_Wait'][tBBox[1]] = attr_dict
                    # Now add node to nascent graph.
                    host = mapping_dict[source]
                    node_name = '_'.join((str(host), str(tBBox[1])))
                    G.add_node(node_name)

        return G, rank_dict


    def connectGraph(self, G, rank_dict):
        # Iterate over MPI_Send() nodes
        for src_rank in rank_dict.keys():
            # Now loop over events
            for evnt in rank_dict[src_rank]['MPI_Send']:
                my_dest = rank_dict[src_rank]['MPI_Send'][evnt]['dest']
                try:
                    next_send = rank_dict[my_dest]['MPI_Send'].minKey(evnt)
                except ValueError:
                    pass
                try:
                    next_wait = rank_dict[my_dest]['MPI_Wait'].minKey(evnt)
                except ValueError:
                   pass

                if evnt <= next_send <= next_wait:
                    try:
                        delta_t = next_send - evnt
                        source_name = '_'.join((str(mapping_dict[src_rank]), str(evnt)))
                        dest_name = '_'.join((str(mapping_dict[my_dest]), str(next_send)))
                        G.add_edge(source_name, dest_name, weight=delta_t)

                    except:
                        pass

                # Else wait fulfilled first- means path remains on this node
                elif evnt <= next_wait <= next_send:
                    try:
                        delta_t_w = next_wait - evnt
                        source_name = '_'.join((str(mapping_dict[src_rank]), str(evnt)))
                        wait_name = '_'.join((str(mapping_dict[my_dest]), str(next_wait)))
                        G.add_edge(source_name, wait_name, weight=delta_t_w)
                    except:
                        pass

                    #  Now add edge from next_wait to next_send
                    try:
                        delta_t_s = next_send - next_wait
                        send_name = '_'.join((str(mapping_dict[my_dest]), str(next_send)))
                        G.add_edge(wait_name, send_name, weight=delta_t_s)
                    except:
                        pass
                elif evnt == rank_dict[src_rank]['MPI_Send'].maxKey():
                    end_name = '_'.join((str(mapping_dict[src_rank]), 'end'))
                    G.add_edge(source_name, end_name, weight=0.0)

                else:
                    logging.error("order's screwed up!")
                    logging.info("my send time: %f, my next send: %f, my next wait: %f" % (evnt, next_send, next_wait))
                    logging.info("max send time: %f, max next send: %f, max next wait: %f" % (rank_dict[src_rank]['MPI_Send'].maxKey(), \
                                 rank_dict[my_dest]['MPI_Send'].maxKey(),rank_dict[my_dest]['MPI_Wait'].maxKey()))
        logging.error("number of self-edges before removal: %d" % (G.number_of_selfloops()))
        G.remove_edges_from(G.selfloop_edges())
        return G


    # Now compute the critical (longest) path graph. Copied from StackOverflow
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
    parser.add_argument("-m", dest="host_mapping",
                        help="directory for host mappings")

    args = parser.parse_args()

    logging.basicConfig(filename='/projects/dami9546/HPSC/final/hostgraph_test2120.out', \
                        format='%(asctime)s %(message)s',level=logging.DEBUG)
    logging.info('Starting graph script')

    D = DAG(args.in_file, args.host_mapping)
    Grf, H = D.slog2Dict()
    I = D.connectGraph(Grf,H)

    for i in H.keys():
        logging.info("type of rank_dict[i]['MPI_Send']: %s" % (type(H[i]['MPI_Send'])))
        logging.info("type of rank_dict[i]['MPI_Wait']: %s" % (type(H[i]['MPI_Wait'])))
        logging.info("type of rank_dict[i]: %s" % (type(H[i])))
        try:
            check(H[i]['MPI_Send'])
            check(H[i]['MPI_Wait'])
            logging.info('my type: %s' % type(i))
            logging.info('%d is clean' % i)
        except:
            logging.info('my type: %s' % type(i))
            logging.error('%d is corrupt' % i)
    logging.info("DAG size: %d" % (I.size()))
    logging.info("DAG numnodes %d" % (len(I)))
    logging.info("number of self-loops: %d" % (I.number_of_selfloops()))

    crit_path = D.find_critical(I)
    with open(args.crit_file, 'wb') as c:
        crit_path = map(lambda x:x+'\n', crit_path)
        c.writelines(crit_path)

    graph_data = json_graph.node_link_data(I) 

    with open(args.out_file, 'w') as f:
        json.dump(graph_data, f)
