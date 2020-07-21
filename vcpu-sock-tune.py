#!/usr/bin/python2

import os
import sys
import hooking


def tune_socket():
    	domxml = hooking.read_domxml()
    	domain = domxml.getElementsByTagName('domain')[0]
	vcpu = domain.getElementsByTagName('vcpu')[0]
	has_cur_attr = vcpu.hasAttribute('current')
	cpu_num_assigned = -1
	if has_cur_attr:
		cpu_num_assigned = int(vcpu.getAttribute('current'))
		vcpu.childNodes[0].data = cpu_num_assigned
	else:
		cpu_num_assigned= int(vcpu.childNodes[0].data)

    	cpu = domain.getElementsByTagName('cpu')[0]
	top = cpu.getElementsByTagName('topology')[0]
	top.setAttribute('sockets','1')
    	top.setAttribute('cores',str(cpu_num_assigned))
    	top.setAttribute('threads','1')
	
    	hooking.write_domxml(domxml)

tune_socket()
