#!/usr/bin/python
import os
import sys
import hooking
import traceback

import collections
import re
import subprocess


_CONF_FILE = '/etc/vcpu-vgpu/vcpu-vgpu.dump'

_NODE_LIST = []
_NODE_NUM = -1

class Node:
	def __init__(self, num):
		self.numa_num = num
		self.cpu_list = ''

def get_node_cpu(arg_numa_num):
	
	for numa_node in _NODE_LIST:
		if numa_node.numa_num == arg_numa_num:
			return numa_node.cpu_list
	return None

def get_nodes_num(str0):
    	ret = re.sub('available:', '', str0, 1)
    	ret = re.sub('nodes.*', '', ret, 1)
    	ret = ret.strip()
    	return int(ret)

def get_cpulist(str0):
    	ret = re.sub('node\s+\d+\s+cpus:', '', str0, 1)
    	ret = ret.strip()
    	ret = ret.replace(' ',',')	
    	return ret

def get_node_num(str0):
	ret = re.sub(':.*', '', str0, 1)
	ret = re.sub('node', '', ret, 1)
	ret = re.sub('cpus', '', ret, 1)
	ret = ret.strip()
	return int(ret)

def get_nodeinfo():
    	l = subprocess.check_output(['numactl', '--hardware'])
    	l = l.decode('utf-8')
	l = l.splitlines()
	for i, val in enumerate(l):
		if re.findall('available:\s+\d+\s+nodes', val):
			global _NODE_NUM
	            	_NODE_NUM = get_nodes_num(val)
	        elif re.findall('node\s+\d+\s+cpus:', val):
			node_ins = Node(get_node_num(val))
			node_ins.cpu_list = get_cpulist(val)
			_NODE_LIST.append(node_ins)
	        else:
	            pass
	assert(_NODE_NUM == len(_NODE_LIST))
	

def get_vm_name():
	domxml = hooking.read_domxml()
    	domain = domxml.getElementsByTagName('domain')[0]
	name = domain.getElementsByTagName('name')[0]
    	name_text = name.childNodes[0]
	return name_text.data
	
    	
def get_node(arg_vm_name):
	conf = open(_CONF_FILE, 'r')
	line_0 = True
	for line in conf:	
		if line_0:
			line_0 = False
			continue
		line = line.strip('\n')	
		line = line.split('\t')	
		vm_name = line[0].strip()
		
		if vm_name != arg_vm_name:
			continue
		
		return int(line[1].strip())
	return None


def vcpupin(arg_cpu_node):
	domxml = hooking.read_domxml()
    	domain = domxml.getElementsByTagName('domain')[0]
	vcpu = domain.getElementsByTagName('vcpu')[0]
	vcpu.setAttribute('cpuset',get_node_cpu(arg_cpu_node))	
		
	hooking.write_domxml(domxml)	

def numatune(arg_cpu_node):
	domxml = hooking.read_domxml()
    	domain = domxml.getElementsByTagName('domain')[0]
	numatunes = domain.getElementsByTagName('numatune')
	numatune = None
	if len(numatunes) == 0:
		numatune = domxml.createElement('numatune')
		domain.appendChild(numatune)
	else:
		numatune = numatunes[0]
	memories = numatune.getElementsByTagName('memory')	
	memnodes = numatune.getElementsByTagName('memnode')	
	memory = None
	if len(memories) == 0:
		memory = domxml.createElement('memory')
		numatune.appendChild(memory)	
	else:
		memory = memories[0]
	memory.setAttribute('mode', 'strict')
	memory.setAttribute('nodeset', str(arg_cpu_node))
	
	memnode = None
	if len(memnodes) == 0:
		memnode = domxml.createElement('memnode')
		numatune.appendChild(memnode)	
	else:
		memnode = memnodes[0]
	memnode.setAttribute('cellid', '0')
	memnode.setAttribute('mode', 'strict')		
	memnode.setAttribute('nodeset', str(arg_cpu_node))	
		
	hooking.write_domxml(domxml)

get_nodeinfo()
vm_name = get_vm_name()
node_num = get_node(vm_name)
vcpupin(node_num)
numatune(node_num)
