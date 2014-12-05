#!/bin/bash

if [ ! -e perfqueries ]; then
  mkdir perfqueries
fi

# Reads the output of the balancer file and parses it into a per_node list.
# This script should be run once on job startup
LID=$(cat /sys/class/infiniband/mlx4_0/ports/1/lid)
LID=$(echo $LID| xargs -i'{ }' printf "%d\n" '{ }')
cat balance.out | awk -F':' "\$1 == $LID { print \$2\":\"\$3 }" > "perfqueries/${HOSTNAME}_perfqueries"

#OLDIFS=$IFS
#IFS=$'\n'
#for line in $(cat my_tasks); do 
#  echo $line|awk -F':' "\$1 == $LID { print \$2,\$3 }"|awk '{$cmd="echo "$1" "$2; system("($cmd ) &")}'
#done
#wait
#IFS=$OLDIFS

