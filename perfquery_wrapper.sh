#!/bin/bash
#SBATCH -N 4                 # Requests one nodes
#SBATCH -n 48                # Requests one processors per node (these two lines could be on one)
#SBATCH -J perfquery        # Names the job
#SBATCH --qos janus-debug    # Select the debug queue
####SBATCH --mail-type=end
###SBATCH --mail-user=<caldweba@colorado.edu>

module load tau/tau-2.22.2_openmpi-1.6.4_intel-13.0.0_ib

LOOP_DELAY=$1

START_TIME=$(date '+%Y%m%d%H%M')
PATH_PREFIX=/projects/caldweba
echo "START_TIME = ${START_TIME} ( $(date +"%T.%N") )" 
${PATH_PREFIX}/wrapper_once.sh ${START_TIME}
srun -n ${SLURM_JOB_NUM_NODES} --ntasks-per-node 1 ${PATH_PREFIX}/wrapper_each_node.sh ${START_TIME} ${LOOP_DELAY} &

# kill the job after 10s
sleep 10
