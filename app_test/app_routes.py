#!/usr/bin/env python

import os
import subprocess
import re
import glob
import sys

hostnamecmd = '/bin/hostname'
lidcmd = '/usr/sbin/ibstat'

hostnameproc = subprocess.Popen(hostnamecmd.split(), stdout=subprocess.PIPE)
hostname =  hostnameproc.communicate()[0].rstrip('\n')

lidnameproc = subprocess.Popen(lidcmd.split(), stdout=subprocess.PIPE)
lidstring = lidnameproc.communicate()[0].rstrip('\n')

mylid = re.search('Base lid: (\d+)', lidstring).group(1)

filelist = glob.glob('/home/dami9546/CSCI5576/project/app_test/host_lids/node*')

for nodefile in filelist:
    with open(nodefile, 'r') as file:
        for host in file:
            host = host.rstrip()
            if not host.split(' ', 1)[0] == hostname:
                lid = host.split(' ', 1)[1]
                pathcmd = '/usr/sbin/ibtracert %d %d' %(int(mylid), int(lid))
                try:
                    pathproc = subprocess.Popen(pathcmd.split(), stdout=subprocess.PIPE)
                    path = pathproc.communicate()[0].rstrip()
                    print path
                except subprocess.CalledProcessError:
                    try:
                        pathproc = subprocess.Popen(pathcmd.split(), stdout=subprocess.PIPE)
                        path = pathproc.communicate()[0].rstrip()
                        print path
                    except subprocess.CalledProcessError:
                        print "ERROR: ibtracert failed from %s to %s" % (mylid, lid)
                        sys.exit(1)

            #for guid_switch in re.findall('\{([a-z0-9]+)\}\[(\d+)\]', path):
                #guid = guid_switch[0]
                #port = guid_switch[1]
                #print guid, port
                #perfquerycmd = '/usr/sbin/perfquery -G %s %s' %(guid, port)
                #print perfquerycmd
                #perfquerycmd_proc = subprocess.Popen(perfquerycmd.split(), stdout=subprocess.PIPE)
                #switch_perf = perfquerycmd_proc.communicate()[0].strip()
                #print switch_perf 

#            for guid_hca in re.findall('\{([a-z0-9]+)\}(?!\[(\d+)\])', path):
#                guid = guid_hca[0]
#                perfquerycmd = '/usr/sbin/perfquery -G %s 1' % guid
#                print perfquerycmd
#                perfquerycmd_proc = subprocess.Popen(perfquerycmd.split(), stdout=subprocess.PIPE)
#                hca_perf = perfquerycmd_proc.communicate()[0].rstrip()
#                print hca_perf
