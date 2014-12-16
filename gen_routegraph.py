#!/usr/bin/python

# Script to convert route text to a DAG
# DJM 12/2014

import os
import sys
import re
import glob
import argparse
import json
import networkx as nx
import itertools
from collections import defaultdict

def isa_group_separator(line):
    return line=='\n'

def group(n, iterable, fillvalue=None):
    args = [iter(iterable)] * n
    return itertools.zip_longest(*args, fillvalue=fillvalue)

def test_to_graph(pathname):
    G = nx.DiGraph()

    filelist = glob.glob(os.path.join(pathname, '*end'))
    for file in filelist:
        with open(file, 'r') as filename:  
            for key,group in itertools.groupby(filename,isa_group_separator):
                #print(key,list(group))  # uncomment to see what itertools.groupby does.
                if not key:

                    data={}
                    route_list = []
                    for item in group:
                        try:
                            if re.match('^From ca {', item):
                                guid_num = re.search('(?<={)[^}]*(?=})', item).group(0)
                                lid_num = re.search('lid (\d+)-', item).group(1)
                                name = re.search('"([^"]*)"', item).group(1).split(' ')[0]
                                G.add_node(name, lid=lid_num, guid=guid_num)
                                route_list.append(name)
                            elif re.match('^\[\d+', item):
                                guid = re.search('(?<={)[^}]*(?=})', item).group(0)
                                lid = re.search('lid (\d+)-', item).group(1)
                                name = re.search('"([^"]*)"', item).group(1).split(' ')[0]                    
                                if "Infiniscale" in name:
                                    name = guid
                                G.add_node(name, lid=lid_num, guid=guid_num)
                                route_list.append(name)
                        except:
                            pass
                    try:
                        for idx, val in enumerate(route_list[1:-1]):
                            G.add_edge(route_list[idx-1], route_list[idx])
                    except:
                        pass
    return G

if __name__ == "__main__":
    from networkx.readwrite import json_graph
    parser = argparse.ArgumentParser(description="script to convert slog2 text to DAG")
    parser.add_argument("-i", dest="in_dir",
                        help="read slog2 text FILE", metavar="FILE")
    parser.add_argument("-o", dest="out_file", help="write DAG to JSON FILE", metavar="FILE")

    args = parser.parse_args()
    Graph = test_to_graph(args.in_dir)
    print len(Graph)
    print Graph.size()
    data = json_graph.node_link_data(Graph)

    with open(args.out_file, 'w') as of:
        json.dump(data, of)
