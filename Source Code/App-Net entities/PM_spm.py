#!/usr/bin/python
import os,sys,inspect

from client import *
import zmq
import time
import datetime
from twisted.internet import reactor 
#from utils import Logger,log
from twisted.python import usage, log
from utils import Logger, log_it
import pandas as pd
import numpy as np
import numpy.testing.utils as NTU
import matplotlib.pyplot as plt
import numpy as np
from termcolor import colored, cprint
import threading

if len(sys.argv)<2:
	print "Give the folder to save log!"
	sys.exit()
print 'Argument List:', str(sys.argv)

path_for_log=sys.argv[1]
maxConsecutivePrio=float(sys.argv[2])
safetyMarginDownTime=float(sys.argv[3])
prioBan=float(sys.argv[4])
buffer_falser=float(sys.argv[5])


now = datetime.datetime.now()
now=now.strftime("%Y-%m-%d %H:%M")
de_event_log=open(str(path_for_log)+"/pm_spm_event_log_"+now+".txt","w");
de_event_log.write("#timestamp;event;affected_client;numel_be;numel_prio\n");
de_event_log.flush()


class DecisionEntity():


	def __init__(self,cur_throughputBE=0.0,cur_throughputPrio=0,
		cur_bufferSize=0,cur_chunkSize=0,cur_chunkLength=0,
		cur_quality=0,cur_clients_be=[],cur_clients_prio=[],log_sub_dir='', log_period=0.1, 				  client_map='',a='',beTimeSeriesList=[],smoothedTimeSeries=[], request_order=''):

		self.cur_throughputBE=cur_throughputBE
		self.cur_throughputPrio=cur_throughputPrio
		self.cur_bufferSize=cur_bufferSize
		self.cur_chunkSize=cur_chunkSize
		self.cur_chunkLength=cur_chunkLength
		self.cur_quality=cur_quality
		self.cur_clients_be=cur_clients_be
		self.cur_clients_prio=cur_clients_prio

		self.logger = None
       	 	self.log_file = None
        	self.log_dir='logs'
        	self.log_sub_dir=log_sub_dir
        	self.log_period = log_period
        	self.log_prefix='' 
        	self.log_comment='' 

		self.beTimeSeriesList=[];
		self.smoothedTimeSeries=[];
		
		self.client_map={}
		self.a={}
		self.request_order=[];
		supervise_thread = threading.Thread(target=actualizeQueue,args=(self,))
		supervise_thread.daemon = True
  	    	supervise_thread.start()
		connectZMQ(self)

def actualizeQueue(self):
	num_clients=len(self.client_map)
	for client_c in self.client_map.keys():
		reverse_list=self.request_order[::-1]
		c_pos=reverse_list.index(client_c)
		if c_pos>4*num_clients:
			self.client_map.pop(client_c, None)
			if client_c in self.cur_clients_be:
				removeClientBE(self,client_c);
				de_event_log.write(str(time.time())+";remove;"+str(client_c)+";"+str(len(self.cur_clients_be))+";"+str(len(self.cur_clients_prio))+"\n");
				de_event_log.flush()
			elif client_c in self.cur_clients_prio:
				removeClientPrio(self,client_c);
				de_event_log.write(str(time.time())+";remove;"+str(client_c)+";"+str(len(self.cur_clients_be))+";"+str(len(self.cur_clients_prio))+"\n");
				de_event_log.flush()
	time.sleep(2)
	actualizeQueue(self)
		
def updateRequestOrder(self,clientInfo,t_pid):
	c_identifier=str(clientInfo.split(":")[0])+"_"+str(t_pid)
	self.request_order.append(c_identifier)
	
def addBrowsingInstance(self,ip_address,src_port):
	c_identifier=str(ip_address)+"_"+str(src_port)
	self.request_order.append(c_identifier)
	addClientBE(self,c_identifier)
	self.client_map[c_identifier]=0
	de_event_log.write(str(time.time())+";newBrowser;"+str(c_identifier)+";"+str(len(self.cur_clients_be))+";"+str(len(self.cur_clients_prio))+"\n");

def log_reg(self):
	dictionary=dict(
           throughput_be=float(getThroughputBE(self)),   
           throughput_prio=float(getThroughputPrio(self)),   
           clients_be=int(getClientsBE(self)),                         
           clients_prio=int(getClientsPrio(self)),
	   consecutive_prio=str(getAllConsecutivePrioPerClient(self))
	) 
	log_it(self,dictionary)
	
	
def log_it(self,dictionary):
	opts=[
	   ('throughput_prio',float,''),
	   ('clients_prio',int,''),
	   ('consecutive_prio',int,''),
	   ('clients_be',int,''),
	   ('now','',''),
	   ('throughput_be',float,''),
	]
	
        if not self.logger:
           	self.logger = Logger(opts, log_period=self.log_period, 
                log_prefix=self.log_prefix, comment=self.log_comment, 
                log_dir=self.log_dir)	

	
	self.logger.log_2(dictionary)
	del dictionary
	time.sleep(0.1)

def startEntity():
	
	testEntity=DecisionEntity(cur_throughputBE=0,cur_throughputPrio=0,cur_bufferSize=0,
	cur_chunkSize=0,cur_chunkLength=0,cur_quality=0,cur_clients_be=[],cur_clients_prio=[],log_sub_dir='',log_period=0.1);
	
	self.a={}
	self.client_map={}
	self.beTimeSeriesList=[];
	self.smoothedTimeSeries=[];
	try:
        	reactor.run()
   	except Exception, e:
      		pass

	
def connectZMQ(self):
	context_recv = zmq.Context()
	socket_recv = context_recv.socket(zmq.SUB)
	#receive from zmq
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
		string_temp=string_received.split()
		if string_temp[1]=="websiteInfo":
			app_info=string_received
			listenTo, identifier, src_addr, src_port = app_info.split()
			print("new website info")
			print(str(src_addr))
			print(str(src_port))
			addBrowsingInstance(self,src_addr,src_port)

		if string_temp[1]=="appInfo":
			app_info=string_received
			listenToApp,identifierApp,cur_buffer,chunkSize,quali, segmentDur, clientInfo, t_pid = app_info.split()
			print("new app info")
			checkClient(self,clientInfo,t_pid)
			updateRequestOrder(self,clientInfo,t_pid)
			updateAppParams(self,cur_buffer, chunkSize, quali, segmentDur, clientInfo)
			prio=makeDecision(self,cur_buffer, chunkSize, quali, segmentDur, clientInfo, t_pid)
			socket_send.send_string("%s %s %i" %("5", clientInfo ,prio))
			

		if string_temp[1]=="networkInfo":
			network_info=string_received
			listenToNet,identifierNet, throughputBE, throughputPrio = network_info.split()
			self.beTimeSeriesList.append(float(throughputBE))
			print("new net info")
			throughputBE_smoothed=throughputBE
			updateNetworkParams(self,throughputBE_smoothed, throughputPrio)
			delete_me=delete_me+1;



'''checkClient: check if the client is known already.
if not, open a new log-file for the client!'''
def checkClient(self,clientInfo,t_pid):
	c_identifier=str(clientInfo.split(":")[0])+"_"+str(t_pid)
	if c_identifier in self.client_map:	
		return
	else:
		now = datetime.datetime.now()
		now=now.strftime("%Y-%m-%d %H:%M")
		print colored("detected new TAPAS instance: "+str(c_identifier),'blue')	
		self.client_map[c_identifier]=0
		a_key=c_identifier
		de_log=open(str(path_for_log)+"/decisionEntityLog_"+now+"_"+c_identifier+".txt","w")
		de_log.write("#"+str(clientInfo)+";"+str(t_pid))
		de_log.write("#timestamp;tp_be_smoothed;tp_prio_smoothed;seg_size;buffer;estDT_be;estDT_prio;prio\n");
		self.a[a_key]=de_log
		de_event_log.write(str(time.time())+";newTapas;"+str(c_identifier)+";"+str(len(self.cur_clients_be))+";"+str(len(self.cur_clients_prio))+"\n");
		de_event_log.flush()


def initializeClients(clients):
	for x in clients:
		xsplit=x.split(':')
		c=Client(xsplit[0],xsplit[1],0,0,0)
		clientMap[xsplit[0]]=c

def updateThroughput(tp):
	self.tp=tp

def updateThroughputSmoothed(tp_smoothed):
	self.tp_smoothed=tp_smoothed

def getThroughput(self):
	return self.tp

def getThroughputSmoothed(self):
	return self.tp_smoothed

def updateClientsBuffer(ip_address,buffer):
	updateBuffer(clientMap[str(ip_address)],buffer)
	#print 'made a buffer update'

def updateNetworkParams(self, throughputBE,throughputPrio):

	self.cur_throughputBE=throughputBE
	self.cur_throughputPrio=throughputPrio
	
def updateAppParams(self, bufferSize,chunkSize,quality, segmentDur,clientInfo):
	#print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
	#print("[Decision Entity] Updated Application Data")
	#print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
	self.cur_bufferSize=bufferSize
	self.cur_chunkSize=chunkSize
	self.cur_quality=quality

def getClients(self):
	'''
	Get the clients that have been initialized
	'''
	return self.clients

def setThroughputBE(throughputBE):
	'''
	Sets the current throughput of best-effort queue
	'''
	print 'Updated the throughput'
	self.throughputBE=throughputBE

def setThroughputPrio(throughputPr):
	'''
	Sets the current throughput of prio queue 
	'''
	self.throughputPrio=throughputPr

def getThroughputBE(self):
	'''
	Get the current throughput of BE-Queue
	'''
	return self.cur_throughputBE

def getThroughputPrio(self):
	'''
	Get the current throughput of Prio-Queue
	'''
	return self.cur_throughputPrio

def getBufferSize(self):
	'''
	Get the current buffersize of client
	'''
	return self.buffersize

def getChunkSize(self):
	'''
	Get the size of chunk requested by the client
	'''
	return self.chunkSize

def getChunkLength(self):
	'''
	Get the length in seconds of chunk requested by client
	'''
	print("ChunkLength= "+str(self.cur_chunkLength))
	return str(self.cur_chunkLength)

def getQuality(self):
	'''
	Returns the quality of chunk requested by the client
	'''
	return self.quality
	
def computeEDTBE(self):
	'''
	Computes how long the download will take in best effort queue
	'''
	return

def computeEDTPQ(self):
	'''
	Computes how long the download will take in prioritization queue
	'''
	return

def incrementConsecutivePrioPerClient(self,client_ip):
	self.client_map[client_ip]=self.client_map[client_ip]+1

def resetConsecutivePrioPerClient(self,client_ip):
	self.client_map[client_ip]=0

def getConsecutivePrioPerClient(self,client_ip):
	'''
	hold the consecutive prios in a list per client 	
	'''
	return self.client_map[client_ip]

def getAllConsecutivePrioPerClient(self):
	ret_string=''
	for key, value in self.client_map.iteritems():
		ret_string=ret_string+'ip_addr: '+str(key)+ ' prios:'+str(value)
	return ret_string

def getClientsBE(self):
	return len(self.cur_clients_be)

def getClientsPrio(self):
	return len(self.cur_clients_prio)

def assignClientToQueue (self, prio, client_ip):
	if prio==0:
		if client_ip in self.cur_clients_be:
			return
   		elif client_ip in self.cur_clients_prio:
			removeClientPrio(self, client_ip)
			addClientBE(self, client_ip)
		else:
			addClientBE(self,client_ip)
	elif prio ==1:
		if client_ip in self.cur_clients_prio:
			return
		elif client_ip in self.cur_clients_be:
			removeClientBE(self, client_ip)
			addClientPrio(self, client_ip)
		else:
			addClientPrio(self, client_ip)
			


def addClientBE(self, client_ip):
	self.cur_clients_be.append(client_ip)
	

def removeClientBE(self, client_ip):
	self.cur_clients_be.remove(client_ip)
	

def addClientPrio(self, client_ip):
	self.cur_clients_prio.append(client_ip)

def removeClientPrio(self, client_ip):
	self.cur_clients_prio.remove(client_ip)
	

def makeDecision(self,bufferstate, size_of_segment, qualityLevel, segmentDur, client_ip, t_pid):
	
	from cStringIO import StringIO

	c_identifier=str(client_ip.split(":")[0])+"_"+str(t_pid)

	real_buffer = bufferstate
	bufferstate=float(max(0.0,float(float(bufferstate)+buffer_falser)))

	decisionEntityLog=self.a[c_identifier]

	thrBE=getThroughputBE(self)	
	thrPrio=getThroughputPrio(self)
	totalClientsBE=getClientsBE(self)
	totalClientsPrioQueue=getClientsPrio(self)

	prio=0
	consecutivePrioPerClient=getConsecutivePrioPerClient(self,str(c_identifier))

	if consecutivePrioPerClient < maxConsecutivePrio:
		if abs(float(thrBE)-0)==0:
			thrBE=1
		if c_identifier in self.cur_clients_be:
			totalClientsBE=totalClientsBE-1
		if c_identifier in self.cur_clients_prio:
			totalClientsPrioQueue=totalClientsPrioQueue-1

		totalClientsInSystem=totalClientsBE+totalClientsPrioQueue
		print("in der be-queue sind" +str(totalClientsBE))
		print("in der prio-queue sind" +str(totalClientsPrioQueue))
		print("also insgesamt "+str(totalClientsInSystem))

		if totalClientsInSystem ==0:
			bandwidth_per_client=(float(thrBE))/float(totalClientsBE+1)
			estimatedDownTimeBE=float(1+safetyMarginDownTime)*float(float(size_of_segment)/float(bandwidth_per_client))
			prio=0
			resetConsecutivePrioPerClient(self,c_identifier)
			assignClientToQueue(self,prio,c_identifier)
			decisionEntityLog.write(str(time.time())+";"+str(thrBE)+";"+str(thrPrio)+";"+str(size_of_segment)+";"+str(bufferstate)+";"+str(estimatedDownTimeBE)+";0;"+str(prio)+"\n")
			decisionEntityLog.flush()
		else:
			bandwidth_per_client=(float(thrBE))/float(totalClientsBE+1)
			if (float(bandwidth_per_client)<0):
				bandwidth_per_client=1
			estimatedDownTimeBE=float(1+safetyMarginDownTime)*float(float(size_of_segment)/float(bandwidth_per_client))

			estimated_thrPrio=float(thrPrio)+(float(size_of_segment)/float(segmentDur))
	
		
			if float(estimatedDownTimeBE) <= float(bufferstate) or float(estimated_thrPrio) > float(prioBan): 
				print(str(estimatedDownTimeBE) +"<="+str(bufferstate) +" or "+str(estimated_thrPrio)+">"+str(prioBan))
				prio=0
				resetConsecutivePrioPerClient(self,c_identifier)
				assignClientToQueue(self,prio,c_identifier)
				decisionEntityLog.write(str(time.time())+";"+str(thrBE)+";"+str(thrPrio)+";"+str(size_of_segment)+";"+str(bufferstate)+";"+str(estimatedDownTimeBE)+";0;"+str(prio)+"\n")
				decisionEntityLog.flush()
		
			else: 
				bandwidth_prio_perClient = float((float(prioBan)-float(thrPrio))/float(totalClientsPrioQueue+1))
				estimatedDownTimePrio=float(1+safetyMarginDownTime)*float(float(size_of_segment)/float			  (bandwidth_prio_perClient)) 

				if (float(estimatedDownTimePrio) < bufferstate):
					incrementConsecutivePrioPerClient(self,c_identifier)	
					prio=1
					decisionEntityLog.write(str(time.time())+";"+str(thrBE)+";"+str(thrPrio)+";"+str(size_of_segment)+";"+str(bufferstate)+";"+str(estimatedDownTimeBE)+";"+str(estimatedDownTimePrio)+";"+str(prio)+"\n")
					decisionEntityLog.flush()
					assignClientToQueue(self,prio,c_identifier)
				else:
					prio=0
					resetConsecutivePrioPerClient(self,c_identifier)
					decisionEntityLog.write(str(time.time())+";"+str(thrBE)+";"+str(thrPrio)+";"+str(size_of_segment)+";"+str(bufferstate)+";"+str(estimatedDownTimeBE)+";"+str(estimatedDownTimePrio)+";"+str(prio)+"\n")
					decisionEntityLog.flush()
					assignClientToQueue(self,prio,c_identifier)
	
	else:
		prio=0;
		resetConsecutivePrioPerClient(self,c_identifier)
		assignClientToQueue(self,prio,c_identifier)

	if prio==1:
		print colored('PRIORITIZED','yellow')

	return prio


if __name__ == '__main__':
 	startEntity()




