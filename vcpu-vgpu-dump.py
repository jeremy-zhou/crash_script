#!/usr/bin/python2

import os
import sys

import ConfigParser
import collections
import re
import subprocess
import uuid

def parse_args(arg_file_name):
	cf = ConfigParser.ConfigParser()
	cf.read(arg_file_name)
	
	secs = cf.sections()
	vcpu = cf.options('vcpu-vgpu')

	items = cf.items('vcpu-vgpu')

	args = {}
	args['vcpus_per_vm'] = int(cf.get('vcpu-vgpu','vcpus_per_vm'))
	args['vgpu_type'] = cf.get('vcpu-vgpu','vgpu_type')
	vms_raw = cf.get('vcpu-vgpu','vms')
	vms_raw = vms_raw.strip()
	vms_raw_list = vms_raw.split(',')
	vms_list = []
	for vm_raw in vms_raw_list:
		vms_list.append(vm_raw.strip())
	args['vms'] = vms_list
	return args

class GPU_Device:
	def __init__(self, devname, typename):
		self.dev_name = devname
		self.type_name = typename
		self.node = get_numa_node(devname)
		avail = -1	
		with open(os.path.join(_MDEV_PATH, devname, \
					"mdev_supported_types", \
					typename, \
					"available_instances")) as f:
			avail = int(f.read().strip())
		self.total = avail
		self.used = 0

	def avail(self):
		return self.total - self.used

	def get_sock(self):
		assert(self.avail() >= 1)
		self.used += 1
		return self.dev_name
		
class Node:
	def __init__(self, num):
		self.node = num

		self.cpu_list = []
		self.cpu_total = 0
		self.cpu_used = 0

		self.vgpu_list = []
		self.exhausted_time = 0

	def setcpuinfo(self, lcpu):
		self.cpu_total = len(lcpu)
		self.cpu_used = 0
		self.cpu_list = lcpu

	def get_exhausted_cpu_list(self, arg_cpu_num):
		avail = self.cpu_avail()	
		idx_list = [2,4,11,13,21,23,33,35]
		ret_list = []
		if avail != 0:
			ret_list.extend(self.get_cpu_list(avail))	
		for i in range(arg_cpu_num - avail):
			ret_list.append(self.cpu_list[idx_list[i]]) 
		self.exhausted_time = 1
		return ret_list

	def cpu_avail(self):
		return self.cpu_total - self.cpu_used
	
	def get_cpu_list(self, arg_cpu_num):
		assert(self.cpu_avail() >= arg_cpu_num)
		cpu_list_ret = self.cpu_list[self.cpu_used:self.cpu_used+arg_cpu_num]	
		self.cpu_used += arg_cpu_num 
		return cpu_list_ret
	
	def addvgpuinfo(self, dev):
		self.vgpu_list.append(dev)

	def vgpu_avail(self):
		avail = 0
		for gpu in self.vgpu_list:
			avail += gpu.avail()
		return avail

	def get_gpu_dev(self):
		for gpu in self.vgpu_list:
			if gpu.avail():
				return gpu.get_sock()	
		return None






_NODE_LIST = []

_MDEV_PATH = '/sys/class/mdev_bus'
_NUMA_FILE = 'numa_node'

_NODE_NUM = -1

'''
'/sys/class/mdev_bus/
                     0000:3b:00.0'
'                    0000:86:00.0'
'                    0000:af:00.0'
                     .............'
'''
def per_mdev_device():
    for gpu_device in sorted(os.listdir(_MDEV_PATH)):
        yield gpu_device

'''
read numa_node file from '/sys/class/mdev_bus/0000:3b:00.0/numa_node'

'''
def get_numa_node(device):
    with open(os.path.join(_MDEV_PATH, device, _NUMA_FILE), 'r') as f:
        return int(f.read().strip())

'''
dev_uuid is a directory
check if dev_uuid in this folder of devices
/sys/class/mdev_bus/0000:3b:00.0/a655318f-7394-406f-8e7d-b3247cc9b62d
'''
def numa_node(dev_uuid):
    	for device in per_mdev_device():
        	path = os.path.join(_MDEV_PATH, device)
        	if dev_uuid in os.listdir(path):
            		return get_numa_node(device)

    	return 0


def get_nodes_num(str0):
    	ret = re.sub('available:', '', str0, 1)
    	ret = re.sub('nodes.*', '', ret, 1)
    	ret = ret.strip()
    	return int(ret)

def get_cpulist(str0):
    	ret = re.sub('node\s+\d+\s+cpus:', '', str0, 1)
    	ret = ret.strip()
    	lpro = ret.split()
    	num_list = list(map(int, lpro))
    	return num_list

def get_node_num(str0):
	ret = re.sub(':.*', '', str0, 1)
	ret = re.sub('node', '', ret, 1)
	ret = re.sub('cpus', '', ret, 1)
	ret = ret.strip()
	return int(ret)

def get_nodeinfo(arg_vgpu_type):
    	l = subprocess.check_output(['numactl', '--hardware'])
    	l = l.decode('utf-8')
	l = l.splitlines()
	for i, val in enumerate(l):
		if re.findall('available:\s+\d+\s+nodes', val):
			global _NODE_NUM
	            	_NODE_NUM = get_nodes_num(val)
	        elif re.findall('node\s+\d+\s+cpus:', val):
			node_ins = Node(get_node_num(val))
			node_ins.setcpuinfo(get_cpulist(val))
			_NODE_LIST.append(node_ins)
	        else:
	            pass
	if _NODE_NUM != len(_NODE_LIST):
		return
		
	for gpu_device in per_mdev_device():
		gpu = GPU_Device(gpu_device, arg_vgpu_type)	
		for numa_node in _NODE_LIST:
			if numa_node.node == gpu.node:
				numa_node.addvgpuinfo(gpu)
		
class VmInfo:
	def __init__(self, vm_name):
		self.name = vm_name
		self.cpu_node = -1
		self.bond_cpulist = ""
		self.gpu_node = -1
		self.dev = ""
		self.uuid = str(uuid.uuid4())

def get_node_with_least_gpu():
	pos = -1
	cur = 1000
	for i, numa in enumerate(_NODE_LIST):
		gpu_avail = numa.vgpu_avail()
		if gpu_avail <= 0:
			continue
		if gpu_avail < cur:
			pos = i
			cur = gpu_avail	
	assert(pos != -1)
	return _NODE_LIST[pos]

def get_node_with_avail_cpu(arg_cpu_num):
	for i, numa in enumerate(_NODE_LIST):
		cpu_avail = numa.cpu_avail()
		if cpu_avail >= arg_cpu_num:
			return numa
	return None

def dump_result(arg_vm_list, arg_cpu_num):
	vmlist = []	
	for idx, vm_name in enumerate(arg_vm_list):
		numa = get_node_with_least_gpu()
		vm = VmInfo(vm_name)
		vm.dev = numa.get_gpu_dev()
		vm.gpu_node = numa.node
		
		if numa.cpu_avail() >= arg_cpu_num:
			vm.bond_cpulist = numa.get_cpu_list(arg_cpu_num)
			vm.cpu_node = numa.node
		else:
			cpu_node = get_node_with_avail_cpu(arg_cpu_num)
			if cpu_node is None:
				for nnode in _NODE_LIST:
					if nnode.exhausted_time == 0:
						vm.bond_cpulist = nnode.get_exhausted_cpu_list(arg_cpu_num)
						vm.cpu_node = nnode.node				
						break
			else:
				vm.bond_cpulist = cpu_node.get_cpu_list(arg_cpu_num)
				vm.cpu_node = cpu_node.node
			
		vmlist.append(vm)
	fo = open('/etc/vcpu-vgpu/vcpu-vgpu.dump','w')
	fo.write('{}\t{}\t{}\t{:>20}\t{}\t{:>15}\n'.format('name', 'cpu node', 'cpu list', \
						'gpu node', 'gpu dev', 'gpu uuid'))
	print('{}\t{}\t{}\t{:>20}\t{}\t{:>15}'.format('name', 'cpu node', 'cpu list', \
						'gpu node', 'gpu dev', 'gpu uuid'))
	for vm in vmlist:
		print('{}\t{}\t{:>35}\t{}\t{}\t{}'.format(vm.name, vm.cpu_node, \
						vm.bond_cpulist, vm.gpu_node, \
						vm.dev, vm.uuid))
		fo.write('{}\t{}\t{:>35}\t{}\t{}\t{}\n'.format(vm.name, vm.cpu_node, \
						vm.bond_cpulist, vm.gpu_node, \
						vm.dev, vm.uuid))	
	fo.close()	
		

#vm_list = ['vm0','vm1','vm2','vm3','vm4']
#cpus_num = 8
#vgpu_type="nvidia-18"
args = parse_args('/etc/vcpu-vgpu/vcpu-vgpu.conf')


get_nodeinfo(args['vgpu_type'])
if _NODE_NUM != len(_NODE_LIST):
    exit()
for node in _NODE_LIST:
	print(node.node)
	print(node.cpu_list, node.cpu_avail())
	print(node.vgpu_list, node.vgpu_avail())

dump_result(args['vms'], args['vcpus_per_vm'])






