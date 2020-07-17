#!/usr/bin/python2

import os
import sys
import hooking


def tune_socket():
    	domxml = hooking.read_domxml()
    	domain = domxml.getElementsByTagName('domain')[0]
	vcpu = domain.getElementsByTagName('vcpu')[0]
	cpu_num_assigned = vcpu.getAttribute('current')
	

    	cpu = domain.getElementsByTagName('cpu')[0]
	top = cpu.getElementsByTagName('topology')[0]
	top.setAttribute('sockets','1')
    	top.setAttribute('cores',cpu_num_assigned)
    	top.setAttribute('threads','1')

	vcpu = domain.getElementsByTagName('vcpu')[0]
    	text = vcpu.childNodes[0]
    	text.data = int(cpu_num_assigned)
	
    	hooking.write_domxml(domxml)

tune_socket()
