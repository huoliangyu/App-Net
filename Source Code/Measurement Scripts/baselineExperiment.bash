 #!/bin/bash
echo "STARTED BASELINE EXPERIMENT"
numclients=$#
args=$@
echo "number of arguments is "$numclients
sleeptime[1]=$1
sleeptime[2]=$2
sleeptime[3]=$3
sleeptime[4]=$4
sleeptime[5]=$5
sleeptime[6]=$6

folder_to_log=$7

echo "sleeptime in baseline experiments is " ${sleeptime[*]}

xterm -hold -title "messageBroker" -e "echo -e \"timeout 450s bash startZMQ.sh $folder_to_log\n\" | nc 192.168.1.2 5678" &	

sleep 5

streamtime_temp=420
einh='s'
streamtime=$streamtime_temp$einh

(sleep ${sleeptime[1]}; xterm -hold -title "c1" -e "timeout $streamtime python ../tapas/play.py -m fake -u http://172.16.44.5/bbb/bbbHQ.m3u8 -l $folder_to_log")&


einh='s'
streamtime=$streamtime_temp$einh
(sleep ${sleeptime[2]}; xterm -hold -title "c2" -e "timeout $streamtime python ../tapas/play.py -m fake -u http://172.16.44.5/bbb/bbbHQ.m3u8 -l $folder_to_log")&


einh='s'
streamtime=$streamtime_temp$einh
(sleep ${sleeptime[3]}; xterm -hold -title "c3" -e "timeout $streamtime python ../tapas/play.py -m fake -u http://172.16.44.5/bbb/bbbMQ.m3u8 -l $folder_to_log")&


einh='s'
streamtime=$streamtime_temp$einh

(sleep ${sleeptime[4]}; xterm -hold -title "c4" -e "timeout $streamtime python ../tapas/play.py -m fake -u http://172.16.44.5/bbb/bbbMQ.m3u8 -l $folder_to_log")&


einh='s'
streamtime=$streamtime_temp$einh

(sleep ${sleeptime[5]}; xterm -hold -title "c5" -e "timeout $streamtime python ../tapas/play.py -m fake -u http://172.16.44.5/bbb/bbbLQ.m3u8 -l $folder_to_log")&


einh='s'
streamtime=$streamtime_temp$einh

(sleep ${sleeptime[6]}; xterm -hold -title "c6" -e "timeout $streamtime python ../tapas/play.py -m fake -u http://172.16.44.5/bbb/bbbLQ.m3u8 -l $folder_to_log")&

echo "the sleeptimes are: "${sleeptime[*]}

#max run-duration is 12 min = 720 seconds
echo "sleeping to not stop the script"
sleep 600
sudo killall xterm
