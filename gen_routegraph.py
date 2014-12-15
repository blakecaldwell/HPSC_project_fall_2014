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

def test_to_graph(filename):
    G = nx.DiGraph()

    for key,group in itertools.groupby(filename,isa_group_separator):
        #print(key,list(group))  # uncomment to see what itertools.groupby does.
        if not key:

            data={}
            route_list = []
            for item in group:
                
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
                    G.add_node(name, lid=lid_num, guid=guid_num)
                    route_list.append(name)
            print zip(*(iter(route_list),) * 2)
            print route_list

#                field,value=item.split(':')
#                value=value.strip()
#                data[field]=value
#            print('{FamilyN} {Name} {Age}'.format(**data))

#def text_to_graph(filename):

#	with open('data_file') as f:
#    for line in f:
#    	line = line.strip()
#    	line_list = line.split()

#    	if line_list and re.match('^From ca {', line_list):
#    		for line in f:
#    			line = line.strip()
#    			if re.match('^To ca {', line):
#    				to_hca = re.search('{(0x\d+)}*lid (\d+)-\+d ("*")', line)

#    				break
#    			else:

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="script to convert slog2 text to DAG")
    parser.add_argument("-i", dest="in_file",
                        help="read slog2 text FILE", metavar="FILE")
    parser.add_argument("-o", dest="out_file", help="write DAG to JSON FILE", metavar="FILE")

    args = parser.parse_args()

    with open(args.in_file, 'r') as f:
        test_to_graph(f)
            	