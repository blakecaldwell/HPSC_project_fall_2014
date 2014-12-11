#!/bin/bash

#SBATCH -J graph

#SBATCH --time=3:00:00

#SBATCH -N 1

#SBATCH --ntasks-per-node 15

#SBATCH --qos crestone

#SBATCH --output=/home/dami9546/CSCI5576/HPSC_project_fall_2014/graphjob.out

module load python/anaconda-2.0.0
cd /home/dami9546/CSCI5576/HPSC_project_fall_2014/

python generate_graph.py -i /lustre/janus_scratch/dami9546/stripe_4/run_20141206_2105/tautrace_20141206_2105.slog2_text -o /lustre/janus_scratch/dami9546/stripe_4/run_20141206_2105/execution.json -j /lustre/janus_scratch/dami9546/stripe_4/run_20141206_2105/critical.txt
