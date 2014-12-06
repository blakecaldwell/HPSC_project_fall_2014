#!/bin/bash

# Spawn perfqueries
# This will run forever

START_TIME=$1
[ $START_TIME ] || die "the first argument must be the START_TIME"

LOOP_DELAY=$2
[ $LOOP_DELAY ] || die "the second argument must be the LOOP_DELAY"

if [ ! -e logs/${START_TIME} ]; then
  mkdir -p logs/${START_TIME}
fi

DIR=perfqueries

while true; do
  echo "Starting sweep at $(date +"%T.%N")" >> logs/${START_TIME}/$(hostname)_perfquery.log
  ./perfquery -C mlx4_0 -P 1 $(cat $DIR/${START_TIME}/$(hostname)_perfqueries) >> logs/${START_TIME}/$(hostname)_perfquery.log
  echo "Finished sweep at $(date +"%T.%N")" >> logs/${START_TIME}/$(hostname)_perfquery.log
  sleep $LOOP_DELAY 
done

#OLDIFS=$IFS
#IFS=$'\n'
#while true; do
#  PORTS+=$line
#  #perfquery -C mlx4_0 -P 1 >> logs/${START_TIME}/$(hostname)_perfquery.log
#  for line in $(cat $DIR/${START_TIME}/$(hostname)_perfqueries); do 
#    echo $line|awk -F":" '{print $1,$2}' | awk '{$cmd="./perfquery -C mlx4_0 -P 1 "$1" "$2; system($cmd)}'
#  done >> logs/${START_TIME}/$(hostname)_perfquery.log
#  wait
#  echo "Finished sweep at $(date +"%T.%N")" >> logs/${START_TIME}/$(hostname)_perfquery.log
#done
#IFS=$OLDIFS
