#!/bin/bash

COMMAND=$(echo "$1" | tr "[:upper:]" "[:lower:]")

case $COMMAND in
	'start')
		python /etc/vgpu/mdev-create.py;;
	'stop')
		echo "pass";;
	*)
		echo "unrecognized command";;
esac	








