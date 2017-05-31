 #!/bin/bash

numclients=$#
args=$@
echo "number of arguments is "$numclients
echo $args
sleeptime[1]=$1
sleeptime[2]=$2
sleeptime[3]=$3
sleeptime[4]=$4
sleeptime[5]=$5
sleeptime[6]=$6

zmqPort[1]=$7
zmqPort[2]=$8
zmqPort[3]=$9
zmqPort[4]=${10}
zmqPort[5]=${11}
zmqPort[6]=${12}

folder_to_log=${13}
bw=${14}
bw_usage=${15}
folder=${16}
nm_monitoring=${17}

echo "zmq port 3 is" ${zmqPort[3]}
echo "zmq port 4 is" ${zmqPort[4]}
echo "zmq port 5 is" ${zmqPort[5]}
echo "zmq port 6 is" ${zmqPort[6]}

xterm -hold -title "policyManager" -e "timeout 445s python orchestrator_nade.py $bw $bw_usage $folder"&

xterm -hold -title "messageBroker" -e "echo -e \"timeout 450s bash startZMQ_nade.sh $folder_to_log\n\" | nc 192.168.1.2 5678" &	

sleep 7

echo "sleeptime in baseline experiments is " ${sleeptime[*]}

streamtime_temp=420
einh='s'
streamtime=$streamtime_temp$einh

(sleep ${sleeptime[1]}; xterm -hold -title "c1" -e " timeout $streamtime python ../tapas_nade/play.py -p ${zmqPort[1]} -m fake -r 1080p -i 192.168.1.10 -u http://172.16.44.5/bbb/bbbHQ.m3u8  -l $folder_to_log")&

(sleep ${sleeptime[2]}; xterm -hold -title "c2" -e "timeout $streamtime python ../tapas_nade/play.py -p ${zmqPort[2]} -m fake -r 1080p -i 192.168.1.10 -u http://172.16.44.5/bbb/bbbHQ.m3u8  -l $folder_to_log")&

(sleep ${sleeptime[3]}; xterm -hold -title "c3" -e "timeout $streamtime python ../tapas_nade/play.py -p ${zmqPort[3]} -m fake -r 720p -i 192.168.1.10 -u http://172.16.44.5/bbb/bbbMQ.m3u8  -l $folder_to_log")&

(sleep ${sleeptime[4]}; xterm -hold -title "c4" -e "timeout $streamtime python ../tapas_nade/play.py -p ${zmqPort[4]} -m fake -r 720p -i 192.168.1.10 -u http://172.16.44.5/bbb/bbbMQ.m3u8  -l $folder_to_log")&

(sleep ${sleeptime[5]}; xterm -hold -title "c5" -e "timeout $streamtime python ../tapas_nade/play.py -p ${zmqPort[5]} -m fake -r 360p -i 192.168.1.10 -u http://172.16.44.5/bbb/bbbLQ.m3u8  -l $folder_to_log")&

(sleep ${sleeptime[6]}; xterm -hold -title "c6" -e "timeout $streamtime python ../tapas_nade/play.py -p ${zmqPort[6]} -m fake -r 360p -i 192.168.1.10 -u http://172.16.44.5/bbb/bbbLQ.m3u8  -l $folder_to_log")&

echo "the sleeptimes are: "${sleeptime[*]}


echo "sleeping to not stop the script"
sleep 600
sudo killall xterm
