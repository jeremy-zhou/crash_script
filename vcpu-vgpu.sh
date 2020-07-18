#!/bin/bash

COMMAND=$(echo "$1" | tr "[:upper:]" "[:lower:]")

case $COMMAND in
	'start')
		python /etc/vcpu-vgpu/vcpu-vgpu-dump.py
		python /etc/vcpu-vgpu/mdev-create.py
		;;
	'stop')
		echo "pass";;
	*)
		echo "unrecognized command";;
esac	








