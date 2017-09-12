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

def list(proxmoxapi):
	getClusterStatus = proxmoxapi.proxmox.getClusterStatus()
	#print '#Node in cluster: ' + str(len(getClusterStatus['data']))
	for i in range(0, len(getClusterStatus['data'])):
		print 'node ' + getClusterStatus['data'][i]['name']
		if proxmoxapi.args.detail is True:
			# Storage
			getNodeStorage = proxmoxapi.proxmox.getNodeStorage(getClusterStatus['data'][i]['name'])
			for j in range(0, len(getNodeStorage['data'])):
				total = round(getNodeStorage['data'][j]['total']*1.0 / 1024**3, 2)
				used = round(getNodeStorage['data'][j]['used']*1.0 / 1024**3, 2)
				print getClusterStatus['data'][i]['name'] + ' storage ' + getNodeStorage['data'][j]['storage'] + ' ' + str(used) + 'GB ' + str(total) + 'GB ' + str(round(used/total*100, 2)) + '%'
			
			# CPU
			getNodeStatus = proxmoxapi.proxmox.getNodeStatus(getClusterStatus['data'][i]['name'])
			print getClusterStatus['data'][i]['name'] + ' cpu thread ' + str(getNodeStatus['data']['cpuinfo']['cpus'])
			print getClusterStatus['data'][i]['name'] + ' cpu loadavg ' + str(getNodeStatus['data']['loadavg'][0]) + ' ' + str(getNodeStatus['data']['loadavg'][1]) + ' ' + str(getNodeStatus['data']['loadavg'][2])
			
			# Memory: RAM
			total = round(getNodeStatus['data']['memory']['total']*1.0 / 1024**3, 2)
			used = round(getNodeStatus['data']['memory']['used']*1.0 / 1024**3, 2)
			print getClusterStatus['data'][i]['name'] + ' mem ' + str(used) + ' GB ' + str(total) + 'GB ' + str(round(used/total*100, 2)) + '%'

			# Memory: swap
			total = round(getNodeStatus['data']['swap']['total']*1.0 / 1024**3, 2)
			used = round(getNodeStatus['data']['swap']['used']*1.0 / 1024**3, 2)
			print getClusterStatus['data'][i]['name'] + ' swap ' + str(used) + 'GB ' + str(total) + 'GB ' + str(round(used/total*100, 2)) + '%'

			# KSM
			
def detail(proxmoxapi):
	None

class ProxmoxCLI():
	def loadConfig(self, filename):
		if os.path.exists(filename) is False:
			return False
		with open(filename) as data:
			conf = json.load(data)
			return conf

	def __init__(self):
		# Disable warning for SSL verification
		warnings.filterwarnings("ignore")

		# Check config file
		config = self.loadConfig(CONFIG_FILE)
		if config is False:
			print 'Config file not found !'
			sys.exit(1)

		connect = prox_auth(config['host'], config['user'], config['password'])
		if connect.status is False:
			print 'Error when connect to ' + config['host'] + ' as ' + config['user'] + ': ' + connect.error
			sys.exit(1)
		else:
			self.proxmox = pyproxmox(connect)
	def aaa(self):
		print 'bbb'
	
	def __call__(self):
		return self.aaa()
	
	def parse_option(self):
		self.parser = argparse.ArgumentParser(description = 'Proxmox API client')
		self.parser.add_argument('-l', '--list', action = 'store_true', help='List nodes in cluster')
		self.parser.add_argument('-d', '--detail', action = 'store_true', help='with -l, display more details')
		self.parser.parse_args()

		self.args = self.parser.parse_args()
		self.user_input = {}
		# Loop to extract names in namespace
		for arg in self.args.__dict__:
			if self.args.__dict__[arg] is True:
				# Call variable functions
				globals()[arg](self)
				#print 'Debug: argument ' + arg + ' is selected. Calling function ' + arg + '()'

if __name__ == "__main__":
	proxmoxcli = ProxmoxCLI()
	proxmoxcli.parse_option()


'''
warnings.filterwarnings("ignore")

parser = argparse.ArgumentParser()
parser.parse_args()

# Connect to Proxmox server
connect = prox_auth('mypve.ddns.net','root@pam','Admin2355')
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
'''

#print json.dumps(proxmox.getNodeStorageRRDData('pve', 'local'))
