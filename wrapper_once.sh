#!/bin/bash

die() {
  echo "$@" 1>&2
  exit 1
}

START_TIME=$(date '+%Y%m%d%H%M')
# in ms
TIMEOUT=10

[ $SLURM_NODELIST ] || die "are you running outside of SLURM?"

#echo ${SLUM_NODELIST} |sed 's/node//g' | sed 's/[\[,]\([0-9]\+\)\-\([0-9]\+\)\]/{\2..\1}/g' | sed 's/,/ /'

cd /projects/caldweba/
/projects/caldweba/dump_fts -n -t ${TIMEOUT} > fts.out.${START_TIME}
scontrol show hostname ${SLUM_NODELIST} > job_nodes
ibnetdiscover -p -t ${TIMEOUT} |grep -f job_nodes|grep -e "^CA" |awk '{print $2}' > /projects/caldweba/lids_of_job_members
for each in $(cat lids_of_job_members); do
  OUTPUT=$(saquery -x $each)
  echo $OUTPUT
done | sed 's/.*\.\.\([0-9]\+\) .*\.\.\([0-9]\+\) .*\.\.\([0-9]\+\) .*\.\.\([0-9]\+\)/\1:\2:\3:\4/' > neighbors.${START_TIME}

# Balance the queries
python balance_queries.py --forwardingdb fts.out.${START_TIME} --neighbors neighbors.${START_TIME} > balance.out

#cd /projects/caldweba/
#split_queries.sh
# This will take balance.out and split it into the individual files the node is responsible for in 
#  /projects/caldweba/perfqueries/

#spawn_queries.sh &
# This will spawn N jobs in the background (where N is wc -l perfqueries/$HOSTNAME_perfqueries
#   and then wait until that sweep is complete. It writes the output to /projects/caldweba/logs/
#   It will loop forever until it is killed (by the slurm script)
