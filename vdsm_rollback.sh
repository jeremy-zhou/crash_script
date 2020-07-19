#!/bin/bash
noarch[0]=vdsm-api-main-minor.noarch 
noarch[1]=vdsm-common-main-minor.noarch 
noarch[2]=vdsm-hook-vmfex-dev-main-minor.noarch 
noarch[3]=vdsm-http-main-minor.noarch 
noarch[4]=vdsm-jsonrpc-main-minor.noarch 
noarch[5]=vdsm-python-main-minor.noarch 
noarch[6]=vdsm-yajsonrpc-main-minor.noarch

x86_64[0]=vdsm-main-minor.x86_64 
x86_64[1]=vdsm-network-main-minor.x86_64

echo "**************************************************************"
echo "                                                              "
echo "     1.get version of vdsm installed on this machine.         "
echo "                                                              "
echo "**************************************************************"

counter=0
list_action=0
while [ $counter -lt 3 ];
do
	echo $counter"th try to list vdsm..."
	yum list vdsm
	if [ $? -eq 0 ];then
		list_action=1
		break
	fi
	let counter+=1
done

if [ $list_action -eq 0 ]; then
	echo "//////////////////////////////////////////////////////////////"
	echo "                                                              "
	echo "ERROR:failed to get vdsm information installed on this machine"
	echo "                                                              "
	echo "//////////////////////////////////////////////////////////////"
	sleep 2s
	exit
fi

#installed=$(yum list vdsm | awk '/^Installed/{print $1}')
#if [ -z "$installed" ];then
#	echo "//////////////////////////////////////////////////////////////"
#	echo "                                                              "
#	echo "          ERROR: NO vdsm installed on this machine            "
#	echo "                                                              "
#	echo "//////////////////////////////////////////////////////////////" 
#	exit
#fi

vdsm=$(yum list vdsm | awk '/^vdsm.x86_64/{print $2}')
vdsm=($vdsm)
vdsm_len=${#vdsm[@]}
if [ $vdsm_len -ne 2 -a $vdsm_len -ne 1 ];
then
	echo "//////////////////////////////////////////////////////////////"
	echo "                                                              "
	echo "*****ERROR:get wrong vdsm version number on this machine******"
	echo "                                                              "
	echo "//////////////////////////////////////////////////////////////"
	sleep 2s
	exit
fi

installed_vdsm_main=${vdsm[0]%%-*}
installed_vdsm_minor=${vdsm[0]##*-}
#installed_vdsm_minor=${installed_vdsm_minor_garbage%%\.*}
echo "**************************************************************"
echo "                                                              "
echo "version of vdsm installed main: "$installed_vdsm_main" minor: "$installed_vdsm_minor
echo "                                                              "
echo "**************************************************************"
sleep 2s

echo "**************************************************************"
echo "                                                              "
counter=0
while [ $counter -lt ${#noarch[@]} ]
do
	temp=${noarch[$counter]/main/$installed_vdsm_main}
	noarch[$counter]=${temp/minor/$installed_vdsm_minor}
	echo "---"$counter"---"${noarch[$counter]}
	let counter+=1
done

counter=0
while [ $counter -lt ${#x86_64[@]} ]
do
	temp=${x86_64[$counter]/main/$installed_vdsm_main}
	x86_64[$counter]=${temp/minor/$installed_vdsm_minor}
	echo "---"$counter"---"${x86_64[$counter]}
	let counter+=1
done
echo "                                                              "
echo "**************************************************************"

echo "**************************************************************"
echo "                                                              "
echo "            2.stop vdsmd.service & supervdsmd.service         "
echo "                                                              "
echo "**************************************************************"
systemctl stop vdsmd
systemctl stop supervdsmd
sleep 1s

echo "**************************************************************"
echo "                                                              "
echo "            3.remove vdsm...                                  "
echo "                                                              "
echo "**************************************************************"
yum remove vdsm -y
sleep 2s

echo "**************************************************************"
echo "                                                              "
echo "            4.remove left components...                       "
echo "                                                              "
echo "**************************************************************"
for i in ${!noarch[@]};
do
	echo "**************************************************************"
	echo "                                                              "
	echo "          >remove "${noarch[$i]}
	echo "                                                              "
	echo "**************************************************************"
	yum remove ${noarch[$i]} -y
	sleep 2s
done

for i in ${!x86_64[@]};
do
	echo "**************************************************************"
	echo "                                                              "
	echo "          >remove "${x86_64[$i]}
	echo "                                                              "
	echo "**************************************************************"
	yum remove ${x86_64[$i]} -y
	sleep 2s
done

for vgpu in `ls /sys/bus/mdev/devices`
do
	echo "despawn vgpu device $vgpu"
	echo 1 > /sys/bus/mdev/devices/$vgpu/remove
done

echo "**************************************************************"
echo "                                                              "
echo "    5.reinstall vdsm-"$installed_vdsm_main 
echo "                                                              "
echo "**************************************************************"

yum install vdsm-$installed_vdsm_main -y
if [ $? -ne 0 ];then
	echo "//////////////////////////////////////////////////////////////"
	echo "                                                              "
	echo "ERROR:failed to install vdsm-"$installed_vdsm_main
	echo "                                                              "
	echo "//////////////////////////////////////////////////////////////"
	exit
else
	yum reinstall vdsm-$installed_vdsm_main -y
	if [ $? -ne 0 ];then
		echo "//////////////////////////////////////////////////////////////"
		echo "                                                              "
		echo "ERROR:failed to reinstall vdsm-"$installed_vdsm_main
		echo "                                                              "
		echo "//////////////////////////////////////////////////////////////"
		exit
	fi
fi 

echo "**************************************************************"
echo "                                                              "
echo "            6.start vdsmd.service & supervdsmd.service        "
echo "                                                              "
echo "**************************************************************"
systemctl start vdsmd
systemctl status vdsmd


echo "**************************************************************"
echo "                                                              "
echo "     OK,finished......"
echo "                                                              "
echo "**************************************************************"
