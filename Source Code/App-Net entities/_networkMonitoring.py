import commands, os, sys, re, time
from time import sleep
import datetime
#import zmq
#import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import threading


if len(sys.argv)<2:
	print "Give the folder to save Log!"
	sys.exit()
print 'Argument List:', str(sys.argv)


path_for_log=sys.argv[1]
sleep_time=float(sys.argv[2])
alpha=float(sys.argv[3])

print "i log to: "+str(path_for_log)
print "i sleep for "+str(sleep_time)+" secs"
print "my alpha is "+str(alpha)


now = datetime.datetime.now()
now = now.strftime("%Y-%m-%d %H:%M")
networkEntityLog=open(str(path_for_log)+"/networkEntityLog_"+now+".txt","w")
networkEntityLog.write("#timestamp;sleeptime;alpha;realTP_prio;smoothedTP_prio\n")


def doLogging():
	while True:
		print("lala")
		sleep(5)

tp_logger_thread = threading.Thread(target=doLogging)
tp_logger_thread.daemon = True
tp_logger_thread.start()



counter=0;
prioList=[];
beList=[];

stats_str=commands.getoutput('tc -s qdisc show dev enp0s31f6')
begin=stats_str.find("Sent")
end=stats_str.find("bytes")
c_be_packets=stats_str[begin:end].replace("Sent","")
l_be_packets=c_be_packets

while True:
	
	stats_str=commands.getoutput('tc -s qdisc show dev enp0s31f6')

	begin=stats_str.find("Sent")
	end=stats_str.find("bytes")

	begin_be=stats_str.find("Sent",begin)
	end_be=stats_str.find("bytes", end)

	c_be_packets=stats_str[begin_be:end_be].replace("Sent","")
	print("===")
	print(c_be_packets)
	throughput_be=(float(c_be_packets)-float(l_be_packets))/sleep_time


	beList.append(throughput_be);
	#x_prio=pd.Series(prioList);
	#z_be = pd.ewma(x_prio, com=alpha/(1.0-alpha), adjust=False);
	#be_send = z_be[len(z_be)-1];
	be_send=0
	networkEntityLog.write(str(time.time())+";"+str(sleep_time)+";"+str(alpha)+";"+str(throughput_be)+";"+str(be_send)+"\n");
	networkEntityLog.flush()
	print("[Network Monitoring] Throuhput = "+str((throughput_be*8)/1000)+" kbit/s")
	l_be_packets=c_be_packets
	counter=counter+1;
	time.sleep(sleep_time)
	


