#!/usr/bin/python2

import os
import sys

import collections
import re
import subprocess


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

def construct_numa():
	l = subprocess.check_output(['cat', '/proc/cpuinfo'])
	l = l.decode('utf-8')
	l = l.splitlines()
	pack_gen = yield_pack(l)
	for p_tuple in pack_gen:
		numa = get_numa(p_tuple[1])
		numa.new_processor(p_tuple[2], p_tuple[0])	

	for numa in G_NUMA:
		print('numa id: {}'.format(numa.numa_id))
		for core in numa.cores:
			print('  core id: {}'.format(core.core_id))
			for proc in core.processors:
				print('    processor {}'.format(proc))

construct_numa()


