#!/usr/bin/python2

import os
import sys
import hooking


def tune_socket():
    	domxml = hooking.read_domxml()
    	domain = domxml.getElementsByTagName('domain')[0]
	cpu = domain.getElementsByTagName('cpu')[0]

	cpu.setAttribute('mode','host-passthrough')
	cpu.setAttribute('migratable','off')
	if cpu.hasAttribute('match'):
		cpu.removeAttribute('match')
	if cpu.hasAttribute('check'):
		cpu.removeAttribute('check')

	disable_hypervisor = domxml.createElement('feature')
	disable_hypervisor.setAttribute('policy','disable')
	disable_hypervisor.setAttribute('name','hypervisor')
	cpu.appendChild(disable_hypervisor)
	
    	hooking.write_domxml(domxml)

tune_socket()
