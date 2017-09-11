#!/usr/bin/python2.7

# Ref: https://github.com/Daemonthread/pyproxmox
# Installation: 
# $ sudo pip install requests
# $ sudo pip install requests==2.6.0

import argparse
import json
import datetime
from pyproxmox import *
import warnings
import sys, os

CONFIG_FILE = 'proxmox.conf'



def loadConfig(filename):
	if os.path.exists(filename) is False:
		return False
	with open(filename) as data:
		conf = json.load(data)
		return conf

if __name__ == "__main__":
	# Disable warning for SSL verification
	warnings.filterwarnings("ignore")

	# Check config file
	config = loadConfig(CONFIG_FILE)
	if config is False:
		print 'Config file not found !'
		sys.exit(1)

	connect = prox_auth(config['host'], config['user'], config['password'])
	if connect.status is False:
		print 'Could not connect to server ' + config['host'] + ' as ' + config['user']
		sys.exit(1)
	else:
		proxmox = pyproxmox(connect)

	


'''

parser = argparse.ArgumentParser()
parser.parse_args()

# Connect to Proxmox server
connect = prox_auth('192.168.0.40','root@pam','Admin2355')
proxmox = pyproxmox(connect)

# Get info
getClusterStatus = proxmox.getClusterStatus()
print '#Node in cluster: ' + str(len(getClusterStatus['data']))
for i in range(0, len(getClusterStatus['data'])):
	print 'Node #' + str(i) + ': '  + getClusterStatus['data'][i]['name'] + '(' + getClusterStatus['data'][i]['ip'] + ')'
	
	getNodeNetworks = proxmox.getNodeNetworks(getClusterStatus['data'][i]['name'])
	for j in range(0, len(getNodeNetworks['data'])):
		print '\tInterface #' + str(j) + ': ' + getNodeNetworks['data'][j]['iface']
		print '\t\tType:	' + getNodeNetworks['data'][j]['type'] + (' (ports: ' + getNodeNetworks['data'][j]['bridge_ports'] + ')' if getNodeNetworks['data'][j]['type'] == 'bridge' else '')
		print '\t\tMethod:  ' + getNodeNetworks['data'][j]['method']
		if 'address' in getNodeNetworks['data'][j]:
			print '\t\tAddress: ' + getNodeNetworks['data'][j]['address']
		if 'netmask' in getNodeNetworks['data'][j]:
			print '\t\tNetmask: ' + getNodeNetworks['data'][j]['netmask']
		if 'gateway' in getNodeNetworks['data'][j]:
			print '\t\tGateway: ' + getNodeNetworks['data'][j]['gateway']

	getNodeContainerIndex = proxmox.getNodeContainerIndex(getClusterStatus['data'][i]['name'])
	print '\tContainers: ' + ('empty' if getNodeContainerIndex['data'] is None else str(len(getNodeContainerIndex['data'])))

	getNodeVirtualIndex = proxmox.getNodeVirtualIndex(getClusterStatus['data'][i]['name'])
	print '\tVirtual Machines: ' + ('empty !' if getNodeVirtualIndex['data'] is None else str(len(getNodeVirtualIndex['data'])))
	for j in range(0, len(getNodeVirtualIndex['data'])):
		print '\t\tVM ' + str(getNodeVirtualIndex['data'][j]['vmid']) + ' (' + getNodeVirtualIndex['data'][j]['name'] + '):'
		print '\t\t\tStatus: ' + getNodeVirtualIndex['data'][j]['status']
		print '\t\t\tCPU:	' + str(getNodeVirtualIndex['data'][j]['cpus'])
		print '\t\t\tMemory: ' + str(getNodeVirtualIndex['data'][j]['maxmem'] / 1024**3) + 'GB'
		print '\t\t\tDisk:   ' + str(getNodeVirtualIndex['data'][j]['maxdisk'] / 1024**3) + 'GB'
		if getNodeVirtualIndex['data'][j]['uptime'] != 0:
			print '\t\t\tUptime: ' + str(datetime.timedelta(seconds=getNodeVirtualIndex['data'][j]['uptime']))
	

	getNodeStorage = proxmox.getNodeStorage(getClusterStatus['data'][i]['name'])
	print '\tStorage: ' + str(len(getNodeStorage['data']))
	for j in range(0, len(getNodeStorage['data'])):
		print '\t\tStorage devices: ' + getNodeStorage['data'][j]['storage']
		print '\t\t\tContent: ' + getNodeStorage['data'][j]['content']
		print '\t\t\tType:	' + getNodeStorage['data'][j]['type']
		total = round(getNodeStorage['data'][j]['total']*1.0 / 1024**3, 2)
		used = round(getNodeStorage['data'][j]['used']*1.0 / 1024**3, 2)
		print '\t\t\tUsage:   ' + str(used) + 'GB / ' + str(total) + 'GB (' + str(round(used/total*100, 2)) + '%)'
	

	getNodeDNS = proxmox.getNodeDNS(getClusterStatus['data'][i]['name'])
	print '\tDNS'
	print '\t\tSearch domain: ' + getNodeDNS['data']['search']
	if 'dns1' in getNodeDNS['data']:
		print '\t\tDNS1: ' + getNodeDNS['data']['dns1']
	if 'dns2' in getNodeDNS['data']:
		print '\t\tDNS2: ' + getNodeDNS['data']['dns2']
	if 'dns3' in getNodeDNS['data']:
		print '\t\tDNS3: ' + getNodeDNS['data']['dns3']
	

#print json.dumps(proxmox.getNodeStatus('pve'))
'''