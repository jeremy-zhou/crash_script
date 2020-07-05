#!/bin/bash

function usage() {
cat << EndOfHelp
	Usage: $0 <func_name> <args> | tee $0.log
	Commands - are case insensitive:
		thp - disable transparent_hugepage
		lldp - disable lldp function on nic device
EndOfHelp
}


function thp_func(){
	echo '[+] tune thp'

	thp_op=`cat /sys/kernel/mm/transparent_hugepage/enabled`
	thp_op=($thp_op)
	if [ "${thp_op[2]}" == "[never]" ]; then
		echo "[+] thp is already disabled."
		return
	fi
	
	cur_pf=`tuned-adm active`
	echo "    "$cur_pf
	cur_pf=${cur_pf##*: }
	if [ "$cur_pf" == "myprofile-nothp" ];then
		echo "[+] this pf is already tuned."
		return
	fi

	echo $cur_pf > /tmp/tuned_profile.pre
	
	if [ ! -d "/etc/tuned/myprofile-nothp" ]; then
		mkdir /etc/tuned/myprofile-nothp
	fi
	
	rm -f /etc/tuned/myprofile-nothp/*
	
	echo -e "[main]\ninclude="$cur_pf"\n\n[vm]\ntransparent_hugepages=never"  > /etc/tuned/myprofile-nothp/tuned.conf
	
	chmod +x /etc/tuned/myprofile-nothp/tuned.conf
	tuned-adm profile myprofile-nothp
	
	cur_pf=`tuned-adm active`
	echo "    "$cur_pf
	cur_pf=${cur_pf##*: }
	if [ "$cur_pf" == "myprofile-nothp" ];then
		echo "[+] pf is tuned successfully!"
	else
		echo "[-] failed to tune pf."
		return
	fi
	
	thp_op=`cat /sys/kernel/mm/transparent_hugepage/enabled`
	thp_op=($thp_op)

	if [ "${thp_op[2]}" == "[never]" ]; then
		echo "[+] thp is disabled successfully!"
		echo "[+] please reboot."
	else
		echo "[-] failed to disable thp."
	fi
}

function thp_rollback(){
	echo '[+] rollback thp state'
	pf_pre=''
	if [ -f "/tmp/tuned_profile.pre" ]; then
		pf_pre=`cat /tmp/tuned_profile.pre`
	fi
	if [ -z "$pf_pre" ]; then
		echo "[-] no previous profile found."
		return
	fi

	tuned-adm profile $pf_pre
	cur_pf=`tuned-adm active`
	echo "    "$cur_pf
	cur_pf=${cur_pf##*: }
	if [ "$cur_pf" == "$pf_pre" ];then
		echo "[+] pf is rollback successfully!"
	else
		echo "[-] failed to tune pf."
		return
	fi

	thp_op=`cat /sys/kernel/mm/transparent_hugepage/enabled`
	thp_op=($thp_op)

	if [ "${thp_op[0]}" == "[always]" ]; then
		echo "[+] thp is rollbacked successfully!"
		echo "[+] please reboot."
	else
		echo "[-] failed to rollback thp."
	fi
}

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


COMMAND=$(echo "$1"|tr "[:upper:]" "[:lower:]")

case $COMMAND in 
	'-h')
		usage
		exit 0;;
	'thp')
		thp_func;;
	'thp_rollback')
		thp_rollback;;
	'lldp')
		lldp_func;;
	'lldp_rollback')
		lldp_rollback;;
	*)
		usage
		exit 0;;
esac











