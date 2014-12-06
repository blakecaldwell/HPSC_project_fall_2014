#!/bin/bash

# Spawn perfqueries
# This will run forever

START_TIME=$1
[ $START_TIME ] || die "the first argument must be the START_TIME"

if [ ! -e logs/${START_TIME} ]; then
  mkdir -p logs/${START_TIME}
fi

echo "Starting perfqueries on $(hostname) at $(date +"%T.%N")" >> logs/${START_TIME}/$(hostname)_perfquery.log
DIR=perfqueries
OLDIFS=$IFS
IFS=$'\n'
while true; do
  perfquery -C mlx4_0 -P 1 >> logs/${START_TIME}/$(hostname)_perfquery.log
  for line in $(cat $DIR/${START_TIME}/$(hostname)_perfqueries); do 
    echo $line|awk -F":" '{print $1,$2}' | awk '{$cmd="perfquery -C mlx4_0 -P 1 "$1" "$2; system($cmd)}'
  done >> logs/${START_TIME}/$(hostname)_perfquery.log
  wait
  echo "Finished sweep at $(date +"%T.%N")" >> logs/${START_TIME}/$(hostname)_perfquery.log
done
IFS=$OLDIFS
