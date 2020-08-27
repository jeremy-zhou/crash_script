#!/usr/bin/python2

import os
import sys

import collections
import re
import subprocess
import uuid


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
	
def yield_pack(cpu_info_output):
	proc_id = None
	phy_id = None
	core_id = None
	for i, line in enumerate(cpu_info_output):
		if re.findall('processor\s+:', line):
			proc_id = get_processor(line)
			if proc_id is not None  and phy_id is not None  and core_id is not None:
				yield(proc_id,phy_id,core_id) 
				proc_id = None
				phy_id = None
				core_id = None
		if re.findall('physical\s+id\s+:', line):
			phy_id = get_physical_id(line)
			if proc_id is not None  and phy_id is not None  and core_id is not None:
				yield(proc_id,phy_id,core_id) 
				proc_id = None
				phy_id = None
				core_id = None
		if re.findall('core\s+id\s+:', line):
			core_id = get_core_id(line)
			if proc_id is not None  and phy_id is not None  and core_id is not None:
				yield(proc_id,phy_id,core_id) 
				proc_id = None
				phy_id = None
				core_id = None


def get_processor(val):
	ret = re.sub('processor\s+:\s+', '', val, 1)
	ret = ret.strip()
	return int(ret)

def get_physical_id(val):
	ret = re.sub('physical\s+id\s+:\s+', '', val, 1)
	ret = ret.strip()
	return int(ret)

def get_core_id(val):
	ret = re.sub('core\s+id\s+:\s+', '', val, 1)
	ret = ret.strip()
	return int(ret)

G_NUMA = []
class CCore:
	def __init__(self,core_id,processor_id):
		self.core_id = core_id
		self.processors = []	
		self.processors.append(processor_id)	
	def new_processor(self,core_id,processor_id):
		assert(self.core_id == core_id)
		self.processors.append(processor_id)	

class CNuma:
	def __init__(self,numa_id):
		self.numa_id = numa_id 
		self.cores = []
	def new_processor(self,core_id,processor_id):
		for core in self.cores:
			if core.core_id == core_id:
				core.new_processor(core_id, processor_id)	
				break
		else:
			core_new = CCore(core_id,processor_id)
			self.cores.append(core_new)

def get_numa(phy):
	for numa in G_NUMA:
		if numa.numa_id == phy:
			return numa
	else:
		numa = CNuma(phy)
		G_NUMA.append(numa)
		return numa

def construct_numa(processor, phy, core):
	numa = get_numa(phy)
	numa.new_processor(core,processor)		

l = subprocess.check_output(['cat', '/proc/cpuinfo'])
l = l.decode('utf-8')
l = l.splitlines()
pack_gen = yield_pack(l)
for i in pack_gen:
	print('{} {} {}'.format(i[0],i[1],i[2]))
	construct_numa(i[0],i[1],i[2])

for numa in G_NUMA:
	print('numa id: {}'.format(numa.numa_id))
	for core in numa.cores:
		print('  core id: {}'.format(core.core_id))
		for proc in core.processors:
			print('    processor {}'.format(proc))




