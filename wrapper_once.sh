#!/bin/bash

die() {
  echo "$@" 1>&2
  exit 1
}

START_TIME=$(date '+%Y%m%d%H%M')
TIMEOUT=10 # in ms

[ $SLURM_NODELIST ] || die "are you running outside of SLURM?"

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
