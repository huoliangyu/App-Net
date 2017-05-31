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

dt_margin=${14}
bw=${15}
buffer_falser=${16}


xterm -hold -title "policyManager " -e "timeout 450s python ../decisionEntity.py $folder_to_log 5 $dt_margin $bw $buffer_falser"&

xterm -hold -title "messageBroker" -e "echo -e \"timeout 450s bash startZMQ.sh $folder_to_log\n\" | nc 192.168.1.2 5678" &	

sleep 5

echo "sleeptime in baseline experiments is " ${sleeptime[*]}

streamtime_temp=420
einh='s'
streamtime=$streamtime_temp$einh

(sleep ${sleeptime[1]}; xterm -hold -title "c1" -e " timeout $streamtime python ../tapas_spm/play.py -p ${zmqPort[1]} -m fake -r 1080p -i 192.168.1.10 -u http://172.16.44.5/bbb/bbbHQ.m3u8  -l $folder_to_log")&

(sleep ${sleeptime[2]}; xterm -hold -title "c2" -e "timeout $streamtime python ../tapas_spm/play.py -p ${zmqPort[2]} -m fake -r 1080p -i 192.168.1.10 -u http://172.16.44.5/bbb/bbbHQ.m3u8  -l $folder_to_log")&

(sleep ${sleeptime[3]}; xterm -hold -title "c3" -e "timeout $streamtime python ../tapas_spm/play.py -p ${zmqPort[3]} -m fake -r 1080p -i 192.168.1.10 -u http://172.16.44.5/bbb/bbbMQ.m3u8  -l $folder_to_log")&

(sleep ${sleeptime[4]}; xterm -hold -title "c4" -e "timeout $streamtime python ../tapas_spm/play.py -p ${zmqPort[4]} -m fake -r 1080p -i 192.168.1.10 -u http://172.16.44.5/bbb/bbbMQ.m3u8  -l $folder_to_log")&

(sleep ${sleeptime[5]}; xterm -hold -title "c5" -e "timeout $streamtime python ../tapas_spm/play.py -p ${zmqPort[5]} -m fake -r 1080p -i 192.168.1.10 -u http://172.16.44.5/bbb/bbbLQ.m3u8  -l $folder_to_log")&

(sleep ${sleeptime[6]}; xterm -hold -title "c6" -e "timeout $streamtime python ../tapas_spm/play.py -p ${zmqPort[6]} -m fake -r 1080p -i 192.168.1.10 -u http://172.16.44.5/bbb/bbbLQ.m3u8  -l $folder_to_log")&

echo "the sleeptimes are: "${sleeptime[*]}

#max run-duration is 12 min = 720 seconds
echo "sleeping to not stop the script"
sleep 600
sudo killall xterm
