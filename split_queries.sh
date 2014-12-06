#!/bin/bash

START_TIME=$1
[ $START_TIME ] || die "the first argument must be the START_TIME"

cd /projects/caldweba

mkdir -p perfqueries/$START_TIME

if [ ! -e balance.out.$START_TIME ]; then
  die wrapper_once.sh did not generate balance.out.$START_TIME
fi

if [ ! -e perfqueries/$START_TIME ]; then
  die "failed to create directory perfqueries/$START_TIME"
fi

# Reads the output of the balancer file and parses it into a per_node list.
# This script should be run once on job startup
LID=$(cat /sys/class/infiniband/mlx4_0/ports/1/lid)
LID=$(echo $LID| xargs -i'{ }' printf "%d\n" '{ }')
cat balance.out.$START_TIME | awk -F':' "\$1 == $LID { print \$2\":\"\$3 }" > perfqueries/${START_TIME}/$(hostname)_perfqueries
