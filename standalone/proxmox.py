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
import time, datetime

# Used to run genisoimage
import subprocess

# Used to print colored text 
from lazyme.string import palette, highlighter, formatter
from lazyme.string import color_print


# pyfancy: https://github.com/ilovecode1/Pyfancy-2
from pyfancy import *

CONFIG_FILE = 'proxmox.conf'
TEMPLATE_VMID = '104'

def formatData(bytes, unit, decimals):
	units = {'KB': 1, 'MB': 2, 'GB': 3}
	return round(bytes*1.0 / 1024**units[unit], decimals)

def execBash(cmd):
	process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE)
	output, error = process.communicate()
	exitcode = process.returncode

	return exitcode

def makeCloudInitISO(vmid):
	filename = 'VM' + vmid + '-' + datetime.datetime.now().strftime('%d_%m_%Y_%H_%M_%S') +'.iso'
	execBash('genisoimage -quiet -output cloudinit/iso/' + filename + ' -volid cidata -joliet -rock cloudinit/user-data cloudinit/meta-data')
	return filename

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

			getClusterVmNextId = self.proxmox.getClusterVmNextId()
			
			cloneConfig = {}
			cloneConfig['node'] = self.args.clone[0]
			cloneConfig['hostname'] = self.args.clone[1]
			cloneConfig['newvmid'] = str(getClusterVmNextId['data'])
			cloneConfig['cpus'] = str(self.args.clone[2])
			cloneConfig['mem'] = str(self.args.clone[3])
			cloneConfig['storage'] = str(self.args.clone[4])

			pyfancy().green('[CONF]\t').raw('Template VMID:       ' + TEMPLATE_VMID).output()
			pyfancy().green('[CONF]\t').raw('Node:                ' + cloneConfig['node']).output()
			pyfancy().green('[CONF]\t').raw('Hostname:            ' + cloneConfig['hostname']).output()
			pyfancy().green('[CONF]\t').raw('New VMID:            ' + cloneConfig['newvmid']).output()
			pyfancy().green('[CONF]\t').raw('CPU:                 ' + cloneConfig['cpus']).output()
			pyfancy().green('[CONF]\t').raw('RAM:                 ' + cloneConfig['mem'] + ' GB').output()
			pyfancy().green('[CONF]\t').raw('Additional Storage:  ' + cloneConfig['storage'] + ' GB').output()
			pyfancy().green('[CONF]\t').raw('Storage engine:      ' + self.config['storage_engine']).output()
			pyfancy().green('[CONF]\t').raw('Storage bus:         ' + self.config['storage_bus']).output()
			pyfancy().green('[CONF]\t').raw('Storage format:      ' + self.config['storage_format']).output()

			LOC = str(sys._getframe().f_lineno + 1)
			response = self.proxmox.cloneVirtualMachine(cloneConfig['node'], TEMPLATE_VMID, 
														{	
															'newid': cloneConfig['newvmid'], 
															'full': '1',
															'name': cloneConfig['hostname']
														});

			pyfancy().yellow('[DEBUG]\t').raw('cloneVirtualMachine() ' + json.dumps(response)).output()
			if response['status']['ok'] is False:
				pyfancy().red('[ERROR]\t') \
						 .red('cloneVirtualMachine()').raw(' fail at line ') \
						 .red(LOC).raw(' with HTTP code ') \
						 .red(response['status']['code']).output()
				pyfancy().red('\t').raw(response['status']['reason'] + ' ' + response['errors'].itervalues().next()).output()
				return 1
			else:
				pyfancy().green('[INFO]\t').raw('Cloning VM ' + cloneConfig['newvmid'] + ', please wait ... ').output();
			
			# Wait for cloning process complete
			UPID = response['data']
			while (True):
				time.sleep(1)
				getNodeTaskStatusByUPID = self.proxmox.getNodeTaskStatusByUPID(cloneConfig['node'], UPID)
				if getNodeTaskStatusByUPID['data']['status'] == 'stopped':
					pyfancy().green('[INFO]\t').raw('VM ' + cloneConfig['newvmid'] + ' is ready. Starting configuration on hardware ...').output()
					break
			
			LOC = str(sys._getframe().f_lineno + 1)
			newdisk = 'vm-' + cloneConfig['newvmid'] + '-disk-2'
			response = self.proxmox.allocDiskImages(cloneConfig['node'], self.config['storage_engine'], \
													{	'filename': newdisk, \
														'size': cloneConfig['storage'] + 'G', \
														'vmid': cloneConfig['newvmid'], \
														'format': self.config['storage_format'] \
													})
			pyfancy().yellow('[DEBUG]\t').raw('allocDiskImages() ' + json.dumps(response)).output()
			if response['status']['ok'] is False:
				pyfancy().red('[ERROR]\t') \
						 .red('allocDiskImages()').raw(' fail at line ') \
						 .red(LOC).raw(' with HTTP code ') \
						 .red(response['status']['code']).output()
				pyfancy().red('\t').raw(response['status']['reason'] + ' ' + response['errors'].itervalues().next()).output()
				return 1
			else:
				pyfancy().green('[INFO]\t').raw('Disk ').green(newdisk).raw(' for VM ' + cloneConfig['newvmid'] + ' is allocated.').output()

			# upload image
			cloudinitISO = makeCloudInitISO(cloneConfig['newvmid'])

			LOC = str(sys._getframe().f_lineno + 1)
			response = self.proxmox.uploadContent(cloneConfig['node'], 'cloudinit', 'cloudinit/iso/' + cloudinitISO, 'iso')
			
			pyfancy().yellow('[DEBUG]\t').raw('uploadContent() ' + json.dumps(response)).output()
			if response['status']['ok'] is False:
				pyfancy().red('[ERROR]\t') \
						 .red('uploadContent()').raw(' fail at line ') \
						 .red(LOC).raw(' with HTTP code ') \
						 .red(response['status']['code']).output()
				pyfancy().red('\t').raw(response['status']['reason']).output()
				return 1
			else:
				pyfancy().green('[INFO]\t').raw('cloudinit datasource ').green(cloudinitISO).raw(' for VM ' + cloneConfig['newvmid'] + ' is uploaded.').output()

			LOC = str(sys._getframe().f_lineno + 1)
			response = self.proxmox.configVirtualmachine(cloneConfig['node'], cloneConfig['newvmid'], \
			{	'sockets': '2' if int(cloneConfig['cpus']) >= 2 else '1', \
				'cores': str(int(cloneConfig['cpus']) / 2) if int(cloneConfig['cpus']) >= 2 else '1', \
				'cpu': 'host', \
				'memory': str(int(cloneConfig['mem'])*1024), \
				 self.config['storage_bus'] + '1': 'file=' + self.config['storage_engine'] + ':vm-' + cloneConfig['newvmid'] + '-disk-2', \
				'ide2': 'file=cloudinit:iso/' + cloudinitISO + ',media=cdrom,size=10M' \
			})

			pyfancy().yellow('[DEBUG]\t').raw('configVirtualmachine() ' + json.dumps(response)).output()
			if response['status']['ok'] is False:
				pyfancy().red('[ERROR]\t') \
						 .red('configVirtualmachine()').raw(' fail at line ') \
						 .red(LOC).raw(' with HTTP code ') \
						 .red(response['status']['code']).output()
				pyfancy().red('\t').raw(response['status']['reason']).output()
				return 1
			else:
				pyfancy().green('[INFO]\t').raw('VM ' + cloneConfig['newvmid'] + ' is successfully configured.').output()


			print 'VM is configured and is starting shortly, please wait ...'
			LOC = str(sys._getframe().f_lineno + 1)
			response = self.proxmox.startVirtualMachine(cloneConfig['node'], cloneConfig['newvmid'])

			pyfancy().yellow('[DEBUG]\t').raw('startVirtualMachine() ' + json.dumps(response)).output()
			if response['status']['ok'] is False:
				pyfancy().red('[ERROR]\t') \
						 .red('startVirtualMachine()').raw(' fail at line ') \
						 .red(LOC).raw(' with HTTP code ') \
						 .red(response['status']['code']).output()
				pyfancy().red('\t').raw(response['status']['reason'] + ' ' + response['errors'].itervalues().next()).output()
				return 1
			else:		
				time.sleep(3)
				for i in range(0, 4):
					time.sleep(1)
					getNodeTaskStatusByUPID = self.proxmox.getNodeTaskStatusByUPID(cloneConfig['node'], response['data'])
					#print json.dumps(getNodeTaskStatusByUPID['data'])
					if getNodeTaskStatusByUPID['data']['exitstatus'] != 'OK':
						getNodeTaskLogByUPID = self.proxmox.getNodeTaskLogByUPID(cloneConfig['node'], response['data'])
						pyfancy().red('[ERROR]\t').raw('Could not start VM ' + cloneConfig['newvmid'] + '. Please check configurations.').output()
						pyfancy().red('\t').raw(getNodeTaskLogByUPID['data'][1]['t']).output()
						return 1
				pyfancy().green('[INFO]\t').raw('VM ' + cloneConfig['newvmid'] + ' is successfully started.').output()
			
			return 0

if __name__ == '__main__':
	# Disable warning for SSL verification
	warnings.filterwarnings('ignore')

	proxmoxcli = ProxmoxCLI()
	proxmoxcli.parse_option()

