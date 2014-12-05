#!/bin/bash

module load HPSC_CLASS2014/hw06
module load tau/tau-2.22.2_openmpi-1.6.4_intel-13.0.0_ib

hostname=$( hostname )
lid=$( /usr/sbin/ibstat | grep "Base lid:" | cut -d: -f2 | sed 's/ //' )

echo "${hostname} ${lid}" > /home/dami9546/CSCI5576/HPSC_project_fall_2014/app_test/host_lids/${hostname}

sleep 90

python /home/dami9546/CSCI5576/HPSC_project_fall_2014/app_test/app_routes.py >> /home/dami9546/CSCI5576/HPSC_project_fall_2014/app_test/host_routes/${hostname}_$1
