#!/usr/bin/python

# Script to convert slog2 text to a DAG with weighted edges
# and find the critical path graph.
# DJM 12/2014

import os
import sys
import re
import argparse
import networkx as nx
from BTrees.OOBTree import OOBTree
from collections import defaultdict


class DAG(object):
	"""docstring for DAG"""

	def __init__(self, filename):
		super(DAG, self).__init__()
		self.filename = filename

	def slog2Dict(self):
		# Defaultdict must be callable, so use lambda
		rank_dict = defaultdict(lambda: defaultdict(dict))

		with open(self.filename, 'r') as infile:
			strings1 = ("name=MPI_Send()", "Primitive")
			strings2 = ("name=MPI_Wait()", "Primitive")

			# Again, must be callable, so use lambda for OOBTree
			op_dict = defaultdict(lambda: defaultdict(OOBTree()))

			for line in infile:

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

					# Assemble the dictionary and add to event_btree
					attr_dict = {'dest':dest, 'msg_size':size, 'tBBox_s':tBBox[0],
									'tBBox_e':tBBox[1]}

					rank_dict[source]['MPI_Send'][event] = attr_dict
					# Test
					#print rank_dict[source]['MPI_Send'][event], event, source


		

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="script to convert slog2 text to DAG")
	parser.add_argument("-i", dest="in_file",
                        help="read slog2 text FILE", metavar="FILE")
	parser.add_argument("-o", dest="out_file",
                        help="write DAG to FILE", metavar="FILE")

	args = parser.parse_args()

	D = DAG(args.in_file)
	A = D.slog2Dict()


