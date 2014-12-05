#!/bin/python
import sys, getopt, re

verbose=False

class balancer(object):
  global verbose
  balanced_work={}
  leftover = []
  def __init__(self,balance_lids):
    for worker in balance_lids.iterkeys():
      self.balanced_work[worker] = []
      self.leftover = [] 
  def add(self,switch,port):
    min = 10000
    min_key = ''

    value_set = False
    for worker in self.balanced_work:
      if not value_set:
        min = len(self.balanced_work[worker])
        value_set = True
      else:
        if len(self.balanced_work[worker]) < min:
          # this test case is not working for some reason
          min_key = key
          min = len(self.balanced_work[worker])

    if min_key:
      self.balanced_work[min_key].append((switch.switch_guid,switch.switch_lid,port))
    elif verbose:
      print "found no min key"

  #def finalize(self):
  #  for key in self.balanced_work.iterkeys():
  #    if len(self.leftover) > 0:
  #      self.balanced_work[key].append(self.leftover.pop())
  #    else:
  #      return
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
      self.dst[port].add(int(lid,16))
    else:
      self.dst[port] = set()
      self.dst[port].add(int(lid,16))
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
  global verbose

  my_switches = switch_table_list()
  current_switch = switch_table()
  all_lids=set()
  switch_lids=set()
  hca_lids=set()
 
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
      else:
        hca_lids.add(int(lid,16))

      current_switch.addPort(lid,int(port))
    else:
      print "Unrecognized text: %s" % line.rstrip()

  if verbose:
    print "There are %d destinations" % my_switches.countDestinations()
    print "There are %d switch ports" % my_switches.countEndpoints()
  #my_switches.printList()
  #hca_lids = set ( [balance_lids[x] for x in range(0,len(balance_lids)) ] )
  hca_lids = set(balance_lids.keys())
  err_lids = hca_lids.difference(all_lids)
  if len(err_lids) > 0:
    for lid in err_lids:
      print "Could not match up lid %s of job node with an HCA in the fdbs file"
      hca_lids = hca_lids.intersection(hca_lids)

  # initalize the structure
  myBalancer = balancer(balance_lids)

  # go down list of switches and put items on balanced_work structure
  for switch in my_switches.switches:
    for port in switch.dst.iterkeys():
      port_lids = switch.dst[port]
      job_lids = set(list(balance_lids.keys()))
      if len(job_lids.intersection(port_lids)) > 0:
        myBalancer.add(switch,port)

  # Spread out remaining tasks on leftover list
  #myBalancer.finalize()

  #myBalancer.printout()
  
def read_neighbors(neighbors_file):
  f = open(neighbors_file,'r')
  neighbor_dict = {}
  lines = f.readlines()
  for line in lines:
    (srclid,srcport,dstlid,dstport) = line.split(':')
    neighbor_dict[int(srclid)]={'dstlid' : dstlid, 'dstport' : dstport}
 
  return neighbor_dict
 
def main(argv):
  neighbors = ''
  forwardingdb = ''
  global verbose

  try:
    opts, args = getopt.getopt(argv,"vhf:n:",["forwardingdb=","neighbors="])
  except getopt.GetoptError:
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
    elif opt == '-v':
      verbose = True

  neighbor_dict=read_neighbors(neighbors)
  balance_paths(forwardingdb,neighbor_dict)

if __name__== '__main__':
    main(sys.argv[1:])
    sys.exit(0)
 
