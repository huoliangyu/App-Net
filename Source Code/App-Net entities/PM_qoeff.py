
from resQoeMatching import getMapping,getAvailableEncodings,getMapping_ssim_resolution,getLevels
import operator
import threading
import zmq
import time
from datetime import datetime
from termcolor import colored, cprint
import sys
import pandas as pd
import numpy as np




#information coming from the application:
#client ids-->  client id=ip_port
#each client sends: resolution, current level, ssim 

#information from the network: current bandwidth estimation

#returns: bitrate for each client to request, so that ssim is fair among all clients
client_res={}


mapping=getMapping()
init_ssim=1
available_e=getAvailableEncodings()


param_bw=sys.argv[1]
param_bw_usage=sys.argv[2]
path_for_log=sys.argv[3]
param_monitoring_type=sys.argv[4]


de_event_log=open(str(path_for_log)+"/PM_qoeff_event_log.txt","w");
de_event_log.write("#timestamp;bw;event;network;bwe_dict\n");
de_event_log.flush()

class Orchestrator(): 
	def __init__(self,init_ssim=1.0,given_bw=0,client_res={},client_bitrate={},client_ssim={},client_index={},bw_required=0, last_update={}, state_changed='',bw_usage=1.0, bw_client={}, last_request_client={}, clients_bw_estimation={},counter=0, monitoring_type='',last_measure=0):
		self.init_ssim=init_ssim;
		self.given_bw=given_bw
		self.client_res=client_res
		self.client_bitrate=client_bitrate
		self.client_ssim=client_ssim
		self.client_index=client_index
		self.bw_required=bw_required
		self.state_changed=False;
		self.bw_usage = bw_usage
		self.bw_client=bw_client;
		self.last_request_client={};
		self.clients_bw_estimation={}
		self.counter = counter;
		self.last_update=last_update
		self.monitoring_type=monitoring_type;
		self.last_measure=last_measure;

		self.dl_times=[];
		self.idle_times=[];
		self.bw_estimation_list=[];
		self.dl_share=1.0;
		self.clients_idle_time={};
		self.clients_dl_time={};

		self.level_match=getLevels();
		print (self.level_match)



		print("my bw is "+str(self.given_bw))
		print("bw usage is "+str(self.bw_usage))

		supervise_thread = threading.Thread(target=actualizeClientRes,args=(self,))
		supervise_thread.daemon = True
  	    	supervise_thread.start()


		connectZMQ(self)

def startOrchestrator():
	orch=Orchestrator(init_ssim=1.0,given_bw=param_bw,client_res=client_res,bw_usage=param_bw_usage,monitoring_type=param_monitoring_type);

def computeBitrates(self):
	num_clients_per_bitrate={}
	#go through every IP_PORT combination
	for client in self.client_res.keys():
		#is the clients resolution already been processed
		#used to count the clients per resolution
		clients_resolution=self.client_res[client]
		if clients_resolution in num_clients_per_bitrate.keys():
			num_clients_per_bitrate[clients_resolution]=num_clients_per_bitrate[clients_resolution]+1
		else:
			num_clients_per_bitrate[clients_resolution]=1
		bitrate_opt=getMapping_ssim_resolution(init_ssim, clients_resolution)
		available_bitrates=available_e[clients_resolution]
		chosen_bitrate=min(available_bitrates, key=lambda x:abs(x-bitrate_opt))
		self.client_bitrate[client]=(chosen_bitrate)
		index=available_bitrates.index(chosen_bitrate)
		self.client_index[client]=index
		self.client_ssim[client]=mapping[str(chosen_bitrate),clients_resolution]

		#mean ssim und mean bitrate before optim
		mean_ssim=sum(self.client_ssim.values())/len(self.client_ssim);
		mean_bitrate=sum(self.client_bitrate.values())/len(self.client_bitrate)

	#now, bitrates per client for specified ssim are known	
	#does this match the available bitrate?? -->check and optimize
	self.bw_required=sum(self.client_bitrate.values())
	ssim=self.init_ssim
	while self.bw_required>float(float(self.bw_usage)*float(self.given_bw)) and ssim>0.5:
		ssim=ssim-0.001
		self.bw_required=0;
		for client in self.client_res.keys():
			clients_resolution=self.client_res[client]
			bitrate_opt=getMapping_ssim_resolution(ssim, self.client_res[client])
			available_bitrates=available_e[self.client_res[client]]
			chosen_bitrate=min(available_bitrates, key=lambda x:abs(x-bitrate_opt))
			self.client_bitrate[client]=chosen_bitrate
			self.client_ssim[client]=mapping[str(chosen_bitrate),clients_resolution]
			index=available_bitrates.index(chosen_bitrate)
			self.client_index[client]=index
		self.bw_required=sum(self.client_bitrate.values())

	mean_ssim=sum(self.client_ssim.values())/len(self.client_ssim);
	mean_bitrate=sum(self.client_bitrate.values())/len(self.client_bitrate)
	#self.client_bitrate=enhanceSSIM(self)
	return self.client_bitrate


def enhanceSSIM(self):
	#wie viel bb muss da sein um ueberhaupt noch was verbessern zu koennnen
	excess=float(self.given_bw)-float(self.bw_required)
	ssim_enhancement={};
	bitrate_diff={};
	min_cost_enhancement=0
	#conditions: we still need to have bandwidth  left
	#the bandwidth left is greater than the minimum distance for a higher level
	i=1
	while excess>0 and  min_cost_enhancement<=excess:
		ssim_enhancement={};
		temp_bitrate={};
		temp_ssim={};
		#check which client provides which potential for ssim-enhancement and how expensive this is
		for curr_client in self.client_res.keys():
			#can the client be set to higher level??
			bitrate_index=self.client_index[curr_client]
			clients_resolution=self.client_res[curr_client]
			available_bitrates=available_e[clients_resolution]
			bitrate_before=available_bitrates[bitrate_index]
			ssim_before=mapping[str(bitrate_before),clients_resolution]
			if bitrate_index<len(available_bitrates)-1:
				print('bitrate index is '+str(bitrate_index))
				print('len_available_bitrates is '+str(len(available_bitrates)))
				bitrate_after=available_bitrates[bitrate_index+1]
				ssim_after=mapping[str(bitrate_after),clients_resolution]

				temp_bitrate[curr_client]=bitrate_after;
				temp_ssim[curr_client]=ssim_after;

				ssim_enhancement[curr_client]=ssim_after-ssim_before
				bitrate_diff[curr_client]=bitrate_after-bitrate_before

		ssim_enhancement = sorted(ssim_enhancement.items(), key=operator.itemgetter(1), reverse=True)
		print ('ssim_enhancement is '+str(ssim_enhancement))
		print ('self.client_bitrate'+str(self.client_bitrate))

		print ('ssim_client_ssim is '+str(self.client_ssim))


		if len(ssim_enhancement)>0:
			for k in range(0,len(ssim_enhancement)-1):
				max_enhancement_client=ssim_enhancement[k][0]
				if bitrate_diff[max_enhancement_client]<=excess:
					self.client_bitrate[max_enhancement_client]=temp_bitrate[max_enhancement_client];
					self.client_ssim[max_enhancement_client]=temp_ssim[max_enhancement_client]
					self.client_index[max_enhancement_client]=self.client_index[max_enhancement_client]+1

					clients_resolution=self.client_res[max_enhancement_client];
					available_bitrates=available_e[clients_resolution]
					clients_index=self.client_index[max_enhancement_client]
					bitrate_diff[max_enhancement_client]=available_bitrates[clients_index+1]-available_bitrates[clients_index];

					#found the client for enhancement --> break
					break

			self.bw_required=sum(self.client_bitrate.values())
			excess=float(self.given_bw)-float(self.bw_required)
			print('MIN_COST_ENHANCEMENT IS '+str(min_cost_enhancement))
			print('EXCESS IS '+str(excess))
			print('BANDWIDTH REQUIRED IS '+str(self.bw_required))
			print('BANDWIDTH AVAILABLE IS '+str(self.given_bw))
			print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
			print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
			print('new_vals:')
			print(self.client_bitrate);
			print(self.client_ssim);
			print(self.client_res)

			mean_ssim=sum(self.client_ssim.values())/len(self.client_ssim);
			mean_bitrate=sum(self.client_bitrate.values())/len(self.client_bitrate)
			min_cost_enhancement=min(bitrate_diff.values())

			print('==========================')
			print('==========================')
			print('mean ssim after optimizing '+str(mean_ssim))
			print('mean bitrate after optimizing '+str(mean_bitrate))
			print('==========================')
			print('==========================')

		else:
			break

	return self.client_bitrate

def addClient(self,ip,pid,resolution,bw_est):
	string_client=str(ip)+":"+str(pid);
	self.client_res[string_client]=resolution
	self.last_request_client[string_client] = time.time()
	self.clients_bw_estimation[string_client] = float(bw_est)




def connectZMQ(self):
	context_recv = zmq.Context()
	socket_recv = context_recv.socket(zmq.SUB)
	socket_recv.connect("tcp://192.168.1.2:1111")

	listenTo="1"

	#define socketoptions
	if isinstance(listenTo, bytes):
	    listenTo = listenTo.decode('ascii')
    	    socket_recv.setsockopt_string(zmq.SUBSCRIBE, listenTo)

	'''========================================================'''
	'''Needed for telling client and NetworkControl if prioritization should be performed'''
	context_send = zmq.Context()
	socket_send = context_send.socket(zmq.PUB)
	socket_send.bind("tcp://*:5555")
	'''========================================================'''

	delete_me=1;

	while True:
		string_received = socket_recv.recv_string()
		#received a string, increment counter
		self.counter=self.counter+1;
		#if self.counter>100:
		#	self.monitoring_type="net"
		string_temp=string_received.split()
		print('my bandwidth is '+str(self.given_bw))
		if string_temp[1]=="start":
			listenTo,messageType,bw_est,segSize,ip,port,pid,resolution,idle_time,download_time=string_received.split()
			app_info=string_received
			print("new client coming")
			updateRequestOrder(self,ip,pid)
			addClient(self,ip,pid,resolution,bw_est)
			bitrates_to_request=computeBitrates(self)
			for k in bitrates_to_request.keys():
				if k in self.client_res:

					bitrate=bitrates_to_request[k];
					resolution=self.client_res[k];
					level=self.level_match[str(bitrate),resolution]

					socket_send.send_string("%s %s %i" %("5", k ,level))
					de_event_log.write(str(time.time())+";"+str(self.given_bw)+";"+"1"+";"+"0"+str(self.clients_bw_estimation.values())+"\n")
					de_event_log.flush()

		if string_temp[1]=="client_update":
			app_info=string_received;

			listenTo,messageType,bw_est,segSize,ip,port,pid,resolution,idle_time,download_time=app_info.split()
			bw_changed = False;
			self.dl_times.append(float(download_time));
			self.idle_times.append(float(idle_time));
			self.dl_share = float(sum(self.dl_times)/(float(sum(self.dl_times))+float(sum(self.idle_times))));
			if self.monitoring_type=="app":
				bw_changed = updateBW(self, segSize, ip, pid,bw_est,download_time,idle_time)
			updateRequestOrder(self,ip,pid)
			if self.state_changed==True or bw_changed==True:
				bitrates_to_request=computeBitrates(self)
				for k in bitrates_to_request.keys():
					if k in self.client_res:

						bitrate=bitrates_to_request[k];
						resolution=self.client_res[k];
						level=self.level_match[str(bitrate),resolution]
						socket_send.send_string("%s %s %i" %("5", k ,level))
						self.state_changed=False;
						de_event_log.write(str(time.time())+";"+str(self.given_bw)+";"+"1"+";"+"0"+str(sum(self.clients_bw_estimation.values()))+"\n")
						de_event_log.flush();

		if string_temp[1]=="network":
			app_info = string_received
			if self.monitoring_type=="net":
				print("received network/bw update");
				listenTo, messageType, new_bw = app_info.split()
				change_needed = updateAvailableBandwidth(self,new_bw)
				if change_needed == 1:
					bitrates_to_request=computeBitrates(self)
					for k in bitrates_to_request.keys():
						if k in self.client_res:

							bitrate=bitrates_to_request[k];
							resolution=self.client_res[k];
							level=self.level_match[str(bitrate),resolution]

							socket_send.send_string("%s %s %i" %("5", k ,level))







def updateAvailableBandwidth(self,new_bw):
	print "received bandwidth update";
	print "curr_bw is i received "+str(new_bw)
	print "bandwidth which is set is "+str(self.given_bw)
	#in case that there is a distance greater than 100kbit/sec, recompute the ssim vals
	if abs(float(self.given_bw)-float(new_bw))>100.0 and abs(float(self.given_bw)-float(self.last_measure))>100 and len(self.client_ssim)>0:
		self.given_bw = new_bw
		print colored("updated the available bandwidth to "+str(self.given_bw)+" because of NETWORK",'red')
		print colored("last measure was "+str(self.last_measure),'green');
		self.last_measure=float(new_bw);
		print colored("last measure is now "+str(self.last_measure),'green');
		return 1
	else:
		print colored("last measure was "+str(self.last_measure),'green');
		self.last_measure=float(new_bw);
		print colored("last measure is now "+str(self.last_measure),'green');
		return 0

def updateBW(self,segmentSize,client_ip,t_pid,bw_est,dl,idle):
	c_identifier=str(client_ip+":"+str(t_pid));
	self.clients_idle_time[c_identifier] = float(idle);
	self.clients_dl_time[c_identifier] = float(dl);
	curr_share = sum(self.clients_dl_time.values())/(sum(self.clients_idle_time.values())+sum(self.clients_dl_time.values()));
	print colored("curr_dl_share = "+str(self.dl_share),"green");
	print colored("temporary dl_share = "+str(curr_share),"green");
	#dl_time = time.time()-float(self.last_request_client[c_identifier]);
	bw_est_kbit=float(float(bw_est)*8/1000);
	self.clients_bw_estimation[c_identifier] = bw_est_kbit;
	self.bw_estimation_list.append(sum(self.clients_bw_estimation.values())*self.dl_share);
	to_smooth = pd.Series(self.bw_estimation_list);
	smoothed = pd.ewma(to_smooth, span=80,adjust=True);
	new_bw = smoothed[len(smoothed)-1];
	print colored("bandwidth estimation by clients = "+str(sum(self.clients_bw_estimation.values())),"red");
	print colored("smoothed_bw = "+str(new_bw),"red");

	total_bw_estimate = sum(self.clients_bw_estimation.values());
	if abs(new_bw-float(self.given_bw))>100.0:
			self.given_bw = new_bw;
			print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
			print colored("CHANGED BANDWITDH TO "+str(self.given_bw)+" because of APP",'red')
			print colored("real_bw = "+str(total_bw_estimate));
			print colored("smoothed_bw = "+str(new_bw));
			print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
			return True
	else:
			return False



def updateRequestOrder(self,client_ip,t_pid):
	c_identifier=str(client_ip+":"+str(t_pid))
	self.last_update[c_identifier]=datetime.now()

def actualizeClientRes(self):
	curr_time=datetime.now()

	for client_c in self.client_res.keys():

		if (curr_time-self.last_update[client_c]).total_seconds()>20:
			self.state_changed=True

			if client_c in self.client_res:
				del self.client_res[client_c];
				del self.client_bitrate[client_c];
				del self.client_ssim[client_c];
				del self.bw_client[client_c];
				del self.clients_bw_estimation[client_c];

	time.sleep(2)
	actualizeClientRes(self)



if __name__ == '__main__':
 	startOrchestrator()

