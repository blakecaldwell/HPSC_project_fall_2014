#!/bin/bash

# Spawn perfqueries
# This will run forever

if [ ! -d logs ]; then
  mkdir logs
fi

START_TIME=$(date '+%Y%m%d%H%M')
DIR=perfqueries
OLDIFS=$IFS
IFS=$'\n'
while true; do
  perfquery -C mlx4_0 -P 1
  for line in $(cat $DIR/${HOSTNAME}_perfqueries); do 
    echo $line|awk -F":" '{print $1,$2}' | awk '{$cmd="perfquery -C mlx4_0 -P 1 "$1" "$2; system($cmd)}' &
  done >> logs/${HOSTNAME}_perfquery_${START_TIME}.log
  wait
  echo "Finished sweep at $(date +"%T.%N")" >> logs/${HOSTNAME}_perfquery_${START_TIME}.log
done
IFS=$OLDIFS
