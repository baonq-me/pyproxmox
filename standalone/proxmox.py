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
import time

CONFIG_FILE = 'proxmox.conf'

def formatData(bytes, unit, decimals):
	units = {'KB': 1, 'MB': 2, 'GB': 3}
	return round(bytes*1.0 / 1024**units[unit], decimals)

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
		# Check config file
		self.config = self.loadConfig(CONFIG_FILE)
		if self.config is False:
			print 'Config file not found !'
			sys.exit(1)

		connect = prox_auth(self.config['host'], self.config['user'], self.config['password'])
		if connect.status is False:
			print 'Error when connect to ' + self.config['host'] + ' as ' + self.config['user'] + ': ' + connect.error
			sys.exit(1)
		else:
			self.proxmox = pyproxmox(connect)
			print 'Connected to ' + self.config['host'] + ' as ' + self.config['user']


	def parse_option(self):
		self.parser = argparse.ArgumentParser(description = 'Proxmox API client')
		self.parser.add_argument('-l', '--list', nargs = '*', help='List nodes in cluster')
		self.parser.add_argument('-d', '--detail', nargs = '*', help='with -l, display more details')
		self.parser.add_argument('-c', '--clone', nargs = 5, help='List nodes in cluster')
		# clone arg: node hostname cpu ram disk
		self.parser.parse_args()

		self.args = self.parser.parse_args()
		# Loop to extract names in namespace
		#print '[DEBUG] ' + str(self.args)
		#for arg in self.args.__dict__:
		#	if self.args.__dict__[arg] is True:
		#		# Call variable functions
		if self.args.list is not None:
			getClusterStatus = self.proxmox.getClusterStatus()
			#print '#Node in cluster: ' + str(len(getClusterStatus['data']))
			for i in range(0, len(getClusterStatus['data'])):
				if len(self.args.list) == 0 or getClusterStatus['data'][i]['name'] in self.args.list:
					print getClusterStatus['data'][i]['name'] + ' ' + getClusterStatus['data'][i]['ip'] + ' ' + ('online' if getClusterStatus['data'][i]['online'] == 1 else 'offline')

				if self.args.detail is not None:
					# Storage
					if len(self.args.detail) == 0 or 'storage' in self.args.detail:
						getNodeStorage = self.proxmox.getNodeStorage(getClusterStatus['data'][i]['name'])
						for j in range(0, len(getNodeStorage['data'])):
							total = formatData(getNodeStorage['data'][j]['total'], 'GB', 2)
							used = formatData(getNodeStorage['data'][j]['used'], 'GB', 2)
							print getClusterStatus['data'][i]['name'] + ' storage ' + getNodeStorage['data'][j]['storage'] + ' ' + str(used) + 'GB ' + str(total) + 'GB ' + str(round(used/total*100, 2)) + '%'
				
					# CPU
					if len(self.args.detail) == 0 or 'cpu' in self.args.detail:
						getNodeStatus = self.proxmox.getNodeStatus(getClusterStatus['data'][i]['name'])
						print getClusterStatus['data'][i]['name'] + ' cpu thread ' + str(getNodeStatus['data']['cpuinfo']['cpus'])
						print getClusterStatus['data'][i]['name'] + ' cpu loadavg ' + str(getNodeStatus['data']['loadavg'][0]) + ' ' + str(getNodeStatus['data']['loadavg'][1]) + ' ' + str(getNodeStatus['data']['loadavg'][2])
					
					# Memory
					if len(self.args.detail) == 0 or 'memory' in self.args.detail:
						# RAM
						getNodeStatus = self.proxmox.getNodeStatus(getClusterStatus['data'][i]['name'])
						total = formatData(getNodeStatus['data']['memory']['total'], 'GB', 2)
						used = formatData(getNodeStatus['data']['memory']['used'], 'GB', 2)
						print getClusterStatus['data'][i]['name'] + ' mem ' + str(used) + ' GB ' + str(total) + 'GB ' + str(round(used/total*100, 2)) + '%'

						# Swap
						total = formatData(getNodeStatus['data']['swap']['total'], 'GB', 2)
						used = formatData(getNodeStatus['data']['swap']['used'], 'GB', 2)
						print getClusterStatus['data'][i]['name'] + ' swap ' + str(used) + 'GB ' + str(total) + 'GB ' + str(round(used/total*100, 2)) + '%'

					# CPU
					if len(self.args.detail) == 0 or 'net' in self.args.detail:
						getNodeVirtualIndex = self.proxmox.getNodeVirtualIndex(getClusterStatus['data'][i]['name'])
						netin = 0
						netout = 0
						for instance in getNodeVirtualIndex['data']:
							if instance['uptime'] != 0:
								print getClusterStatus['data'][i]['name'] + ' net vmid ' + str(instance['vmid']) + ' ' + str(formatData(instance['netin'], 'MB', 2)) + 'MB ' + str(formatData(instance['netout'], 'MB', 2)) + 'MB'
								netin = netin + instance['netin']
								netout += instance['netout']
						print getClusterStatus['data'][i]['name'] + ' net ' + str(formatData(netin, 'GB', 3)) + 'GB ' + str(formatData(netout, 'GB', 3)) + 'GB'
		elif self.args.clone is not None:

			response = self.proxmox.upload('pve', 'cloudinit', 'abc.iso', 'iso')
			print json.dumps(response)

			'''getClusterVmNextId = self.proxmox.getClusterVmNextId()
			
			cloneConfig = {}
			cloneConfig['node'] = self.args.clone[0]
			cloneConfig['hostname'] = self.args.clone[1]
			cloneConfig['newvmid'] = str(getClusterVmNextId['data'])
			cloneConfig['cpus'] = str(self.args.clone[2])
			cloneConfig['mem'] = str(self.args.clone[3])
			cloneConfig['storage'] = str(self.args.clone[4])

			storage = 'local-zfs'
			print 'Node:                ' + cloneConfig['node']
			print 'Hostname:            ' + cloneConfig['hostname']
			print 'New VMID:            ' + cloneConfig['newvmid']
			print 'CPU:                 ' + cloneConfig['cpus']
			print 'RAM:                 ' + cloneConfig['mem']
			print 'Additional Storage:  ' + cloneConfig['storage']
			print '[d] Type of storage: ' + storage
			print '[d] Bus/Device:      ' + 'virtio (id = 1)'

			clonePostData = {	'newid': cloneConfig['newvmid'], 
								'full': '1',
								'name': cloneConfig['hostname']
							}
			response = self.proxmox.cloneVirtualMachine(cloneConfig['node'], '100', clonePostData)
			if response is None:
				print 'Failed to clone VM'
			else:
				if response['status']['ok'] is False:
					print "Unknown error"
					print json.dumps(response)
				else:
					print 'Cloning VM ' + cloneConfig['newvmid'] + '...'
					upid = response['data']
					while (True):
						time.sleep(1)
						getNodeTaskStatusByUPID = self.proxmox.getNodeTaskStatusByUPID(cloneConfig['node'], upid)
						if getNodeTaskStatusByUPID['data']['status'] == 'stopped':
							print 'VM ' + cloneConfig['newvmid'] + ' is ready. Starting configuration on hardware...'
							break

					
					allocPostData = {	'filename': 'vm-' + cloneConfig['newvmid'] + '-disk-2',
										'size': cloneConfig['storage'],
										'vmid': cloneConfig['newvmid'],
										'format': 'raw'
									}
					response = self.proxmox.allocDiskImages(cloneConfig['node'], storage, allocPostData)
					
					configPostData = {	'sockets': '2' if int(cloneConfig['cpus']) >= 2 else '1',
										'cores': str(int(cloneConfig['cpus']) / 2) if int(cloneConfig['cpus']) >= 2 else '1',
										'cpu': 'host',
										'memory': cloneConfig['mem'],
										'virtio1': 'file=' + storage + ':vm-' + cloneConfig['newvmid'] + '-disk-2',
										'ide0': 'file=local:iso/cloudinit.iso,media=cdrom,size=10M'
									}
					response = self.proxmox.configVirtualmachine(cloneConfig['node'], cloneConfig['newvmid'], configPostData)

					print 'Configuration on hardware is complete. VM is ready to start.'
					response = self.proxmox.startVirtualMachine(cloneConfig['node'], cloneConfig['newvmid'])
					print json.dumps(response)'''


if __name__ == "__main__":
	# Disable warning for SSL verification
	warnings.filterwarnings("ignore")

	proxmoxcli = ProxmoxCLI()
	proxmoxcli.parse_option()

