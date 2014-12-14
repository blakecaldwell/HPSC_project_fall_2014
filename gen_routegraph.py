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
    return line=='To ca {0x'

    for key,group in itertools.groupby(f,isa_group_separator):
        # print(key,list(group))  # uncomment to see what itertools.groupby does.
        if not key:
            data={}
            for item in group:
                field,value=item.split(':')
                value=value.strip()
                data[field]=value
            print('{FamilyN} {Name} {Age}'.format(**data))

def text_to_graph(filename):

	with open('data_file') as f:
    for line in f:
    	line = line.strip()
    	line_list = line.split()

    	if line_list and re.match('^From ca {', line_list):
    		for line in f:
    			line = line.strip()
    			if re.match('^To ca {', line):
    				to_hca = re.search('{(0x\d+)}*lid (\d+)-\+d ("*")', line)

    				break
    			else:


            	