#!/usr/bin/python

import os
import sys
import ConfigParser

_CONF_FILE = '/etc/vcpu-vgpu/vcpu-vgpu.dump'

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

def get_devuuid_list():
	conf = open(_CONF_FILE, 'r')
	line_0 = True
	dev_uuid = {}
	for line in conf:
		if line_0:
			line_0 = False
			continue
		line = line.strip('\n')	
		line = line.split('\t')	
		vm_name = line[0].strip()
		dev = line[4].strip()
		uuid = line[5].strip()	
		dev_uuid[uuid] = dev
	return dev_uuid

def create_mdev(arg_dev_uuid_dict, arg_grid_type):

	for key, value in arg_dev_uuid_dict.items():
		
		path = os.path.join('/sys/class/mdev_bus/{}/mdev_supported_types/{}/create'.format(value, arg_grid_type))
    		with open(path, 'w') as f:
        		f.write(key)

args = parse_args('/etc/vcpu-vgpu/vcpu-vgpu.conf')
dev_list = get_devuuid_list()
create_mdev(dev_list, args['vgpu_type'])
fo = open('/tmp/vmname.txt','a+')
for key, value in dev_list.items():
	fo.write('{} {}\n'.format(key, value))
fo.close()
