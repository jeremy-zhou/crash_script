#!/bin/bash

function lldp_func(){
	echo '[+] tune lldp.'

	nic_name=()
	nic_mac=()
	nic_idx=0
	ovirtmgmt_mac=''
	bridge_nic=''
	nics=`ip a | awk '/^[0-9]+:/{print $2}'`
	nics=($nics)

	for nic in ${nics[@]}; do
		nic_dev=${nic%%:}
		if [ "$nic_dev" == "lo" ];then
			continue
		fi
	
		if [ "$nic_dev" == ";vdsmdummy;" ];then
			continue
		fi

		if [ "$nic_dev" == "ovirtmgmt" ]; then
			ovirtmgmt_mac=`ifconfig $nic_dev |grep "ether" | awk '{print $2}'`
			continue
		fi
			
		nic_name[$nic_idx]=$nic_dev
		nic_mac[$nic_idx]=`ifconfig $nic_dev |grep "ether" | awk '{print $2}'`
		let nic_idx=nic_idx+1
	done
	
	nic_idx=0
	while [ $nic_idx -lt ${#nic_name[@]} ]
	do
		if [ "${nic_mac[$nic_idx]}" == "$ovirtmgmt_mac" ]; then
			bridge_nic=${nic_name[$nic_idx]}
			break
		fi
		let nic_idx=nic_idx+1
	done

	if [ -z $bridge_nic ]; then
		echo '[-] failed to get bridge mac.'
		return
	fi
	
	adm_status=`lldptool get-lldp -i $bridge_nic adminStatus`
	adm_status=${adm_status##*=}
	if [ "$adm_status" == "disabled" ]; then
		echo "[+] admin status is already disabled on $bridge_nic"
		return
	fi
	echo $adm_status > /tmp/lldp.pre
	dum=`lldptool set-lldp -i $bridge_nic adminStatus=disabled`
	adm_status=`lldptool get-lldp -i $bridge_nic adminStatus`
	adm_status=${adm_status##*=}
	if [ "$adm_status" == "disabled" ]; then
		echo "[+] disable lldp for $bridge_nic successfully!"
		return
	fi
	echo "[-] failed to disable lldp for $bridge_nic"
}

function lldp_rollback() {
	echo '[+] rollback lldp'

	nic_name=()
	nic_mac=()
	nic_idx=0
	ovirtmgmt_mac=''
	bridge_nic=''
	nics=`ip a | awk '/^[0-9]+:/{print $2}'`
	nics=($nics)

	for nic in ${nics[@]}; do
		nic_dev=${nic%%:}
		if [ "$nic_dev" == "lo" ];then
			continue
		fi
	
		if [ "$nic_dev" == ";vdsmdummy;" ];then
			continue
		fi

		if [ "$nic_dev" == "ovirtmgmt" ]; then
			ovirtmgmt_mac=`ifconfig $nic_dev |grep "ether" | awk '{print $2}'`
			continue
		fi
			
		nic_name[$nic_idx]=$nic_dev
		nic_mac[$nic_idx]=`ifconfig $nic_dev |grep "ether" | awk '{print $2}'`
		let nic_idx=nic_idx+1
	done
	
	nic_idx=0
	while [ $nic_idx -lt ${#nic_name[@]} ]
	do
		if [ "${nic_mac[$nic_idx]}" == "$ovirtmgmt_mac" ]; then
			bridge_nic=${nic_name[$nic_idx]}
			break
		fi
		let nic_idx=nic_idx+1
	done

	if [ -z $bridge_nic ]; then
		echo '[-] failed to get bridge mac.'
		return
	fi

	adm_status=`lldptool get-lldp -i $bridge_nic adminStatus`
	adm_status=${adm_status##*=}
	if [ "$adm_status" != "disabled" ]; then
		echo "[-] admin status is enabled."
		return
	fi

	adm_pre=''
	if [ -f /tmp/lldp.pre ]; then
		adm_pre=`cat /tmp/lldp.pre`
	fi
	if [ -z $adm_pre ];then
		echo "[-] failed to get previous lldp conf"
		return
	fi

	dum=`lldptool set-lldp -i $bridge_nic adminStatus=$adm_pre`
	adm_status=`lldptool get-lldp -i $bridge_nic adminStatus`
	adm_status=${adm_status##*=}
	if [ "$adm_status" == "$adm_pre" ]; then
		echo "[+] admin status is rollbacked successfully on $bridge_nic."
		return
	fi	
	echo "[-] failed to rollback lldp for $bridge_nic"
}

COMMAND=$(echo "$1" | tr "[:upper:]" "[:lower:]")

case $COMMAND in
	'start')
		lldp_func;;
	'stop')
		echo "pass";;
	*)
		echo "unrecognized command";;
esac	








