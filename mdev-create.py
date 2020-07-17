#!/usr/bin/python

import os
import sys

_CONF_FILE = '/tmp/vcpu_gpu.conf'

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



dev_list = get_devuuid_list()
create_mdev(dev_list, "nvidia-18")
fo = open('/tmp/vmname.txt','a+')
for key, value in dev_list.items():
	fo.write('{} {}\n'.format(key, value))
fo.close()
