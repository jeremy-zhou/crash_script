#!/usr/bin/python
import os
import sys
import hooking
import traceback

import collections
import re
import subprocess


_CONF_FILE = '/etc/vcpu-vgpu/vcpu-vgpu.dump'

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
		
		return line[1].strip()
	return None

def get_cpulist(arg_vm_name):
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
		cpu_raw = line[2]
		cpu_raw = cpu_raw.strip()
		cpu_raw = cpu_raw.strip('[')
		cpu_raw = cpu_raw.strip(']')
		cpu_raw = cpu_raw.split(', ')
		cpu_list = []
		for s in cpu_raw:
			cpu_list.append(int(s))
		return cpu_list
	return None

def vcpupin(arg_cpu_list):
	domxml = hooking.read_domxml()
    	domain = domxml.getElementsByTagName('domain')[0]
	cputunes = domain.getElementsByTagName('cputune')
	cputune = None
	if len(cputunes) == 0:
		cputune = domxml.createElement('cputune')
		domain.appendChild(cputune)
	else:
		cputune = cputunes[0]
	exist_vcpupins = cputune.getElementsByTagName('vcpupin')	
	for i in range(len(arg_cpu_list)):
		found = False
		for e_vcpupin in exist_vcpupins:
			vcpu = e_vcpupin.getAttribute('vcpu')
			if vcpu == str(i):
				e_vcpupin.setAttribute('cpuset', str(arg_cpu_list[i]))
				found = True
			else:
				continue
		if found:
			continue	
		vcpupin = domxml.createElement('vcpupin')	
		vcpupin.setAttribute('vcpu', str(i))
		vcpupin.setAttribute('cpuset', str(arg_cpu_list[i]))
		cputune.appendChild(vcpupin)	
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

vm_name = get_vm_name()
node = get_node(vm_name)
cpu_list = get_cpulist(vm_name)
fo = open('/tmp/vmname.txt','a+')
fo.write('node: {}\n'.format(node))
fo.write('name: {}\n'.format(vm_name))
for ele in cpu_list:
	fo.write('{}\n'.format(ele))
fo.close()
vcpupin(cpu_list)
numatune(node)



