import commands, os, sys, re, time
from time import sleep
import datetime
import zmq
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


if len(sys.argv)<2:
	print "Give the folder to save Log!"
	sys.exit()
print 'Argument List:', str(sys.argv)


path_for_log=sys.argv[1]
sleep_time=float(sys.argv[2])
alpha=float(sys.argv[3])
mechanism=str(sys.argv[4])


now = datetime.datetime.now()
now = now.strftime("%Y-%m-%d %H:%M")

'''Create Log File
timestamp: unix timestamp 
sleeptime: throughput probing interval (sec)
alpha: coefficient for exponentially weighted moving average (EWMA)
realTP_be: throughput in the best-effort queue, wihtout smoothing by EWMA, this value is only for evaluation purpose
smoothedTP_be: throughput in the best-effort queue, smoothed with EWMA, this value is sent to PM
realTP_prio: throughput in prioritized queue, without smoothing, this value is only for evaluation purpose
smoothedTP_prio: throughput in the prioritized queue, smoothed with EWMA, this value is sent to PM
'''
networkEntityLog=open(str(path_for_log)+"/networkEntityLog_"+now+".txt","w")
networkEntityLog.write("#timestamp;sleeptime;alpha;realTP_be;smoothedTP_be;realTP_prio;smoothedTP_prio\n")

context = zmq.Context()
socket_zmq = context.socket(zmq.PUB)
socket_zmq.bind("tcp://*:3333")

counter=0;
prioList=[];
beList=[];

stats_str=commands.getoutput('tc -s qdisc show dev enp0s31f6')

begin=stats_str.find("Sent")
end=stats_str.find("bytes")

begin_prio=stats_str.find("Sent",begin+1)
end_prio=stats_str.find("bytes", end+1)

begin_be=stats_str.find("Sent", begin_prio+2)
end_be=stats_str.find("bytes", end_prio+2)

c_prio_packets=stats_str[begin_prio:end_prio].replace("Sent","")
c_be_packets=stats_str[begin_be:end_be].replace("Sent","")


l_prio_packets=c_prio_packets
l_be_packets=c_be_packets


stats_str_all=commands.getoutput('tc -s qdisc show dev enp0s31f6')
begin_all=stats_str_all.find("Sent")
end_all=stats_str_all.find("bytes")
c_prio_packets_all=stats_str[begin_all:end_all].replace("Sent","")
l_prio_packets_all=c_prio_packets_all


#qoe-ff/baseline/nade: only need to send overall tp 
#spm: needs tp of prio and best-effort queue

if mechanism == "spm":
	while True:

		stats_str=commands.getoutput('tc -s qdisc show dev enp0s31f6')

		begin=stats_str.find("Sent")
		end=stats_str.find("bytes")

		begin_prio=stats_str.find("Sent",begin+1)
		end_prio=stats_str.find("bytes", end+1)

		begin_be=stats_str.find("Sent", begin_prio+2)
		end_be=stats_str.find("bytes", end_prio+2)

		
		c_prio_packets=stats_str[begin_prio:end_prio].replace("Sent","")
		c_be_packets=stats_str[begin_be:end_be].replace("Sent","")
	
		throughput_prio=0
		#throughput_prio=(float(c_prio_packets)-float(l_prio_packets))/sleep_time
		throughput_be=(float(c_be_packets)-float(l_be_packets))/sleep_time
		

		prioList.append(throughput_prio);
		beList.append(throughput_be);

		x_prio=pd.Series(prioList);
		x_be=pd.Series(beList);

		z_prio = pd.ewma(x_prio, com=alpha/(1.0-alpha), adjust=False);
		z_be = pd.ewma(x_be, com=alpha/(1.0-alpha), adjust=False);

		prio_send = z_prio[len(z_prio)-1];
		be_send = z_be[len(z_be)-1];

		networkEntityLog.write(str(time.time())+";"+str(sleep_time)+";"+str(alpha)+";"+str(throughput_be)+";"+str(be_send)+";"+str(throughput_prio)+";"+str(prio_send)+"\n");
		networkEntityLog.flush()
		socket_zmq.send_string("%s %f %f" % ("3", float((be_send*8)/1000), float((prio_send*8)/1000)))
		print("[Network Entity] Throughput Best-Effort= "+str(float((throughput_be*8)/1000))+ " kbit/s")
		print("[Network Entity] Throuhput Prio= "+str((throughput_prio*8)/1000)+" kbit/s")
		l_prio_packets=c_prio_packets
		l_be_packets=c_be_packets
		counter=counter+1;
		time.sleep(sleep_time)

else:
		while True:
			stats_str=commands.getoutput('tc -s qdisc show dev enp0s31f6')

			begin=stats_str.find("Sent")
			end=stats_str.find("bytes")

			begin_prio=stats_str.find("Sent",begin)
			end_prio=stats_str.find("bytes", end)

			c_prio_packets=stats_str[begin_prio:end_prio].replace("Sent","")

			throughput_prio=(float(c_prio_packets)-float(l_prio_packets_all))/sleep_time
			prioList.append(throughput_prio);
			x_prio=pd.Series(prioList);
			z_prio = pd.ewma(x_prio, com=alpha/(1.0-alpha), adjust=False);
			prio_send = z_prio[len(z_prio)-1];

			networkEntityLog.write(str(time.time())+";"+str(sleep_time)+";"+str(alpha)+";"+str(throughput_prio)+";"+str(prio_send)+"\n");
			networkEntityLog.flush()

			socket_zmq.send_string("%s %f" %("3", float((prio_send*8/1000))))
			print("[Network Entity] Throuhput All= "+str((throughput_prio*8)/1000)+" kbit/s")

			l_prio_packets_all=c_prio_packets
			counter=counter+1;

			time.sleep(sleep_time)



