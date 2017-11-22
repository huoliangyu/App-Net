
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
import math



#info coming from the applications:
#client id  -->  client id=ip_port
#client sends: resolution, current level, ssim-value

#info coming from the network: current bandwidth estimation

#return: bandwidth slice for each client, so that each client can request a bitrate resulting in a fair ssim for all clients

client_res={}

mapping=getMapping()
init_ssim=1
available_e=getAvailableEncodings()


param_bw=sys.argv[1]
param_bw_usage=sys.argv[2]
path_for_log=sys.argv[3]

de_event_log=open(str(path_for_log)+"/pm_nade_event_log.txt","w");
de_event_log.write("#timestamp;res;share\n");
de_event_log.flush()

class Orchestrator(): 
	def __init__(self,init_ssim=1.0,given_bw=0,client_res={},client_bitrate={},client_ssim={},client_index={},bw_required=0, last_update={}, state_changed='',bw_usage=1.0, bw_client={}, last_request_client={}, clients_bw_estimation={},counter=0,last_measure=0):
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
		self.last_measure=last_measure;

		self.dl_times=[];
		self.idle_times=[];
		self.bw_estimation_list=[];
		self.dl_share=1.0;
		self.clients_idle_time={};
		self.clients_dl_time={};

		self.level_match=getLevels();

		self.clients_flow_id={};
		self.clients_ip_port={};
		self.flow_id = 0;
		print (self.level_match)



		print("my bw is "+str(self.given_bw))
		print("bw usage is "+str(self.bw_usage))

		supervise_thread = threading.Thread(target=actualizeClientRes,args=(self,))
		supervise_thread.daemon = True
  	    	supervise_thread.start()


		connectZMQ(self)

def startOrchestrator():
	orch=Orchestrator(init_ssim=1.0,given_bw=param_bw,client_res=client_res,bw_usage=param_bw_usage);

def computeBitrates(self):
	bandwidth_share = {}
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

	#now, bitrates per client for specified ssim are known	
	#does this match the available bitrate?? -->check and optimize
	self.bw_required=sum(self.client_bitrate.values())
	ssim=self.init_ssim
	bandwidth_to_allocate = float(self.given_bw)*0.9
	#bandwidth_to_allocate = float(self.given_bw)*(float(float(len(self.client_res))/float(len(self.client_res)+1)));
	print colored('bandwidth to allocat is '+str(bandwidth_to_allocate),'yellow');
	while self.bw_required>float(float(self.bw_usage)*float(bandwidth_to_allocate)) and ssim>0.5:
		ssim=ssim-0.001
		self.bw_required=0;
		for client in self.client_res.keys():
			bitrate_opt=getMapping_ssim_resolution(ssim, self.client_res[client])
			available_bitrates=available_e[self.client_res[client]]
			
			chosen_bitrate=min(available_bitrates, key=lambda x:(abs(x-math.floor(bitrate_opt/100)*100)))
							
			#new_list = [x-bitrate_opt for x in available_bitrates]
			#ind = new_list.index(min)
			bandwidth_share[client]=float(float(chosen_bitrate)/float(self.given_bw));
			self.client_bitrate[client]=chosen_bitrate
			#print colored('bandwidth to allocate = '+str(bandwidth_to_allocate),'red')
			#print colored('availabel _bw = '+str(self.given_bw))
			#print (str(self.client_bitrate.values()))
		self.bw_required=sum(self.client_bitrate.values())

	#self.client_bitrate=enhanceSSIM(self)
	return bandwidth_share


def addClient(self,ip,pid,resolution):
	string_client=str(ip)+":"+str(pid);
	self.client_res[string_client]=resolution
	self.last_request_client[string_client] = time.time()




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
	'''Needed for telling NetworkControl which bandwidth needs to be reserved for who'''
	context_send = zmq.Context()
	socket_send = context_send.socket(zmq.PUB)
	socket_send.bind("tcp://*:5555")
	'''========================================================'''

	delete_me=1;

	while True:
		string_received = socket_recv.recv_string()
		string_temp=string_received.split()
		#case 1 : a new instance needs to be registered
		if string_temp[1]=="start":
			listenTo,messageType,ip,port,pid,resolution=string_received.split()
			string_client = str(ip) + ":" + str(pid);
			client_flow = str(ip)+ ":" +str(port);
			self.flow_id=self.flow_id+1;
			self.clients_flow_id[string_client] = self.flow_id;
			self.clients_ip_port[string_client] = port;
			socket_send.send_string("%s %s %s %f %i" % ("5", "register", client_flow, 0.0, self.clients_flow_id[string_client]))
			addClient(self,ip,pid,resolution)
			updateRequestOrder(self,ip,pid)
			bandwidth_share=computeBitrates(self)
			for k in bandwidth_share.keys():
				if k in self.client_res:
					socket_send.send_string("%s %s %s %f %i" % ("5", "update", k, bandwidth_share[k], self.clients_flow_id[k]))
					self.state_changed=False;
					de_event_log.write(str(time.time())+";"+str(client_res[k])+";"+str(bandwidth_share[k])+"\n")
					de_event_log.flush()
		#case 2 : an update from a client, check first if its port has changed
		if string_temp[1]=="client_update":
			print colored('CURRENTLY ACTIVE CLIENTS ->'+str(len(self.client_res.keys())))
			print colored('currently highest id ->'+str(self.flow_id))
			app_info=string_received;
			listenTo,messageType,ip,port,pid,resolution=app_info.split()
			string_client = str(ip) + ":" + str(pid);
			#if the port has changed, we need a new flow_id for that client
			if self.clients_ip_port[string_client] != port:
				old_port = self.clients_ip_port[string_client]
				old_flowid = self.clients_flow_id[string_client]
				old_client_flow = str(ip)+":"+str(old_port)
				print colored("port needs to be updated")
				client_flow = str(ip)+ ":" +str(port);
				self.clients_ip_port[string_client] = port;
				self.flow_id=self.flow_id+1;
				self.clients_flow_id[string_client] = self.flow_id;
				print colored('- - - - CHANGED THE CLIENTS FLOW flow_id')
				socket_send.send_string("%s %s %s %f %i" % ("5", "delete", old_client_flow, 0.0, old_flowid))
				socket_send.send_string("%s %s %s %f %i" % ("5", "register", client_flow, 0.0, self.clients_flow_id[string_client]))
				bandwidth_share=computeBitrates(self)
				for k in bandwidth_share.keys():
					if k in self.client_res:
						socket_send.send_string("%s %s %s %f %i" % ("5", "update", k, bandwidth_share[k], self.clients_flow_id[k]))
						self.state_changed=False;
						de_event_log.write(str(time.time())+";"+str(client_res[k])+";"+str(bandwidth_share[k])+"\n")
						de_event_log.flush();
				
			updateRequestOrder(self,ip,pid)
			if self.state_changed==True:
				bandwidth_share=computeBitrates(self)
				for k in bandwidth_share.keys():
					if k in self.client_res:
						socket_send.send_string("%s %s %s %f %i" % ("5", "update", k, bandwidth_share[k], self.clients_flow_id[k]))
						self.state_changed=False;
						de_event_log.write(str(time.time())+";"+str(client_res[k])+";"+str(bandwidth_share[k])+"\n")
						de_event_log.flush();

		if string_temp[1]=="network":
			app_info = string_received
			#print("received network/bw update");
			listenTo, messageType, new_bw = app_info.split()
			change_needed = updateAvailableBandwidth(self,new_bw)
			if change_needed == 1:
				bandwidth_share=computeBitrates(self)
				for k in bandwidth_share.keys():
					if k in self.client_res:
						socket_send.send_string(
							"%s %s %s %f %i" % ("5", "update", k, bandwidth_share[k],self.clients_flow_id[k]))
						de_event_log.write(str(time.time())+";"+str(client_res[k])+";"+str(bandwidth_share[k])+"\n")
						de_event_log.flush()







def updateAvailableBandwidth(self,new_bw):
	#print "received bandwidth update";
	#in case that there is a distance greater than 100kbit/sec, recompute the ssim vals
	if abs(float(self.given_bw)-float(new_bw))>200.0 and len(self.client_ssim)>0:
		self.given_bw = new_bw
		print colored("updated the available bandwidth to "+str(self.given_bw)+" because of NETWORK",'red')
		return 1
	else:
		return 0


def updateRequestOrder(self,client_ip,t_pid):
	c_identifier=str(client_ip+":"+str(t_pid))
	self.last_update[c_identifier]=datetime.now()

def actualizeClientRes(self):
	curr_time=datetime.now()

	for client_c in self.client_res.keys():
		

		if (curr_time-self.last_update[client_c]).total_seconds()>20:
			#a client left the system
			self.state_changed=True

			if client_c in self.client_res:
				del self.client_res[client_c];
				del self.client_bitrate[client_c];
				del self.client_ssim[client_c];
				del self.bw_client[client_c];
				del self.clients_bw_estimation[client_c];
				del self.clients_ip_port[client_c];
				del self.clients_flow_ip[client_c];

	time.sleep(2)
	actualizeClientRes(self)



if __name__ == '__main__':
 	startOrchestrator()

