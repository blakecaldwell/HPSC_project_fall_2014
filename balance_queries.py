#!/bin/python
import sys, getopt, re

verbose=False
all_lids=set()
switch_lids=set()
hca_lids=set()
balance_paths=set()

class balancer(object):
  balanced_work={}
  leftover = []
  def __init__(self,balance_lids):
    for worker in balance_lids:
      self.balanced_work[worker] = []
      self.leftover = [] 
  def add(self,switch,port,worker_lids):
    # find
    potential = []
    for entry in switch.dst[port]:
      if entry in worker_lids:
        potential.append(entry)
 
    if len(potential) == 0:
      self.leftover.append((switch.switch_guid,switch.switch_lid,port))
      if verbose:
        print "found no potentials for port %s on switch %s" % (port, switch.switch_name )
      return
      
    min = 10000
    min_key = 0

    value_set = False
    for key in potential:
      if not value_set:
        min = len(self.balanced_work[key])
        value_set = True
      elif len(self.balanced_work[key]) < min:
        min_key = key
        min = len(self.balanced_work[key])
    # key now has the lid of the lucky HCA that will get the task

    self.balanced_work[key].append((switch.switch_guid,switch.switch_lid,port))
  def finalize(self):
    for key in self.balanced_work.iterkeys():
      if len(self.leftover) > 0:
        self.balanced_work[key].append(self.leftover.pop())
      else:
        return
    #if len(self.leftover) > 0:
    #  self.finalize()

  def printout(self):
    for key in self.balanced_work.iterkeys():
      if len(self.balanced_work[key]) > 0:
        for entry in self.balanced_work[key]:
          sys.stdout.write("%s:"% key)
          (guid, lid, port) = entry
          sys.stdout.write("%s:%d\n" % (lid, port))
 
class switch_table(object):
  def __init__(self):
    self.switch_name=''
    self.switch_guid=''
    self.switch_lid=''
    self.nr_ports=0
    self.nr_dst_lids=0
    self.dst={}
  def clear(self):
    self.switch_name=''
    self.switch_guid=''
    self.switch_lid=''
    self.nr_ports=0
    self.nr_dst_lids=0
    self.dst={}
  def addPort(self,lid,port):
    if port in self.dst:
      self.dst[port].append(int(lid,16))
    else:
      self.dst[port] = []
      self.dst[port].append(int(lid,16))
    self.nr_dst_lids += 1
    self.nr_ports = len(self.dst)
  def isEmpty(self):
    if self.nr_ports == 0:
      return True
    else:
      return False
  def printSwitch(self):
    sys.stdout.write("%s:" % (self.switch_guid))
    for key in self.dst.iterkeys():
      sys.stdout.write("%s,"%key)
    print
  def countDestinations(self):
    count = 0
    for key in self.dst.iterkeys():
      count += len(self.dst[key])
    return count

class switch_table_list(object):
  switches = []
  def add(self,switch):
    self.switches.append(switch)
  def length(self):
    return len(self.switches)
  def printList(self):
    for switch in self.switches:
      switch.printSwitch()
  def countDestinations(self):
    count = 0
    for switch in self.switches:
      count += switch.countDestinations()
    return count
  def countEndpoints(self):
    count = 0
    for switch in self.switches:
      count += len(switch.dst)
    return count

def balance_paths(data_file, balance_lids):
  my_switches = switch_table_list()
  current_switch = switch_table()
 
  f = open(data_file,'r')

  lines = f.readlines()
  for line in lines:
    if "Unicast" in line:
      if not current_switch.isEmpty():
        my_switches.add(current_switch)
        current_switch = switch_table()
      m = re.search(r'Unicast.*guid\s+(0x[0-9a-f]+)\s+\((.*)\):',line)
      if m:
        current_switch.switch_name = m.group(2)
        current_switch.switch_guid = m.group(1)
      else:
        print "Failed to parse line: %s" % line
        sys.exit(1)
    elif "Destination" in line:
      continue
    elif "Port" in line:
      continue
    elif "dumped" in line:
      continue
    elif "0x" in line:
      (lid,port) = line.split()
      all_lids.add(int(lid,16))
      if port == "000":
        # port referring to self, known switch lid
        switch_lids.add(int(lid,16))
        current_switch.switch_lid = int(lid,16)
        continue
      current_switch.addPort(lid,int(port))
    else:
      print "Unrecognized text: %s" % line.rstrip()

  #print "There are %d destinations" % my_switches.countDestinations()
  #print "There are %d switch ports" % my_switches.countEndpoints()
  #  my_switches.printList()
  hca_lids = all_lids.difference(switch_lids)
  err_lids = balance_lids.difference(hca_lids)
  if len(err_lids) > 0:
    for lid in err_lids:
      print "Could not match up lid %s with a HCA in the fdbs file"
    balance_lids = balance_lids.intersection(hca_lids)

  # initalize the structure
  myBalancer = balancer(balance_lids)

  # go down list of switches and put items on balanced_work structure
  for switch in my_switches.switches:
    for port in switch.dst.iterkeys():
      myBalancer.add(switch,port,balance_lids)

  # Spread out remaining tasks on leftover list
  myBalancer.finalize()

  myBalancer.printout()
  
def read_host_lids(lid_file):
  f = open(lid_file,'r')
  balance_lids = []
  lines = f.readlines()
  for line in lines:
    try:
      (srclid,srcport,dstlid,dstport) = line.split(':')
    except:
      print "line does not contain an integer: %s"% line
    balance_lids[int(lid)
 
  return balance_lids
 
def main(argv):
  neighbors = ''
  forwardingdb = ''

  try:
    opts, args = getopt.getopt(argv,"hf:n:",["forwardingdb=","neighbors="])
  except getopt.GetoptError:
    print '%s.py -f <forwardingdb> -n <neighbors>' % sys.argv[0]
    sys.exit(2)
  if len(argv) < 4:
    print '%s.py -f <forwardingdb> -n <neighbors>' % sys.argv[0]
    sys.exit(2)

  for opt, arg in opts:
    if opt == '-h':
      print '%s.py -f <forwardingdb> -n <neighbors>' % sys.argv[0]
      sys.exit()
    elif opt in ("-f", "--forwardingdb"):
      forwardingdb = arg
    elif opt in ("-n", "--neighbors"):
      neighbors = arg

  neighbor_lids=read_host_lids(neighbors)
  balance_paths(forwardingdb,neighbor_lids)

if __name__== '__main__':
    main(sys.argv[1:])
    sys.exit(0)
 
