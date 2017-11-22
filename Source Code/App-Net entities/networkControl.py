import zmq
import os
import socket
import commands
import subprocess  
from subprocess import Popen, PIPE
import time
import threading
import fileinput
import sys
import datetime


#proc = Popen(['sudo python path_to_trash/trash.py'], shell=True, stdin=None, stdout=True, stderr=None, close_fds=True)
proc = Popen(['python /home/susanna/GIT-repos/trash/trash.py'], shell=True, stdin=None, stdout=True, stderr=None, close_fds=True)


bandwidth_pattern=str(sys.argv[1])
higher_limit=float(sys.argv[2])
lower_limit=float(sys.argv[3])
mechanism=str(sys.argv[4])

now = datetime.datetime.now()
now = now.strftime("%Y-%m-%d %H:%M")
#networkControlLog=open("/networkControlLog_"+now+".txt","w")
#networkControlLog.write("#timestamp;available_bw\n")


class NetworkControl():


	def __init__(self,curr_bw=''):

		self.curr_bw=lower_limit
		time.sleep(1);
		self.socket_trash = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket_trash.connect(('localhost',10101))


		if mechanism=="nade":
			#Nade requires another alternative for bandwidth throttling and other commands for changing rate limits
			self.socket_trash.send("start THROTTLING\n")
			time.sleep(5);
			if bandwidth_pattern=="alternating":
				bw_change_thread = threading.Thread(target=changebwNade,args=(self,higher_limit,lower_limit,))
				bw_change_thread.daemon = True
				bw_change_thread.start()
			if bandwidth_pattern=="sawtooth":	
				bw_change_thread = threading.Thread(target=decreasebwNade,args=(self,higher_limit,lower_limit,))
				bw_change_thread.daemon = True
				bw_change_thread.start()
		else:
			self.socket_trash.send("start PRIO_HTB \n")
			time.sleep(5);
			if bandwidth_pattern=="alternating":
				bw_change_thread = threading.Thread(target=changebw,args=(self,higher_limit,lower_limit,))
				bw_change_thread.daemon = True
				bw_change_thread.start()
			if bandwidth_pattern=="sawtooth":	
				bw_change_thread = threading.Thread(target=decreasebw,args=(self,higher_limit,lower_limit,))
				bw_change_thread.daemon = True
				bw_change_thread.start()

		if mechanism=="nade" or mechanism=="spm":
			zmq_thread = threading.Thread(target=connectZMQ(self),args=(self,))
			zmq_thread.daemon = True
			zmq_thread.start()
	


	
def startEntity():
	te = NetworkControl();			



def changebw(self,higher_limit,lower_limit):
	time.sleep(30)
	if self.curr_bw==higher_limit:
		print("[NetworkControl] Bandwidth decrease")
		self.socket_trash.send("CMD changeRateandCeilGWClass GW1 "+str(lower_limit)+"kbit\n")
		self.curr_bw=lower_limit
		changebw(self,higher_limit,lower_limit);
	if self.curr_bw==lower_limit:
		print("[NetworkControl] Bandwidth increase")
		self.socket_trash.send("CMD changeRateandCeilGWClass GW1 "+str(higher_limit)+"kbit\n")
		self.curr_bw=higher_limit
		changebw(self,higher_limit,lower_limit);

		
def decreasebw(self,higher_limit,lower_limit):
	time.sleep(1)
	if self.curr_bw > lower_limit: 
		decrease_factor=float((higher_limit-lower_limit)/30)
		self.curr_bw = self.curr_bw-decrease_factor;
		self.socket_trash.send("CMD changeRateandCeilGWClass GW1 "+str(self.curr_bw)+"kbit\n")
		#networkControlLog.write(str(time.time())+";"+str(self.curr_bw)+"\n")
		print('current_bw:'+str(self.curr_bw))
		decreasebw(self,higher_limit,lower_limit)
	else:
		self.curr_bw = higher_limit
		self.socket_trash.send("CMD changeRateandCeilGWClass GW1 "+str(self.curr_bw)+"kbit\n")
		#networkControlLog.write(str(time.time())+";"+str(self.curr_bw)+"\n")
		print('current_bw:'+str(self.curr_bw))
		decreasebw(self,higher_limit,lower_limit)

def changebwNade(self,higher_limit,lower_limit):
	time.sleep(30)
	if self.curr_bw==higher_limit:
		print("[NetworkControl] Bandwidth decrease")
		self.socket_trash.send("CMD changedefbwandceil GW1 "+str(lower_limit)+"kbit "+str(higher_limit)+"kbit\n")
		self.curr_bw=lower_limit
		changebw(self,higher_limit,lower_limit);
	if self.curr_bw==lower_limit:
		print("[NetworkControl] Bandwidth increase")
		self.socket_trash.send("CMD changedefbwandceil GW1 "+str(higher_limit)+"kbit "+str(lower_limit)+"kbit\n")
		self.curr_bw=higher_limit
		changebw(self,higher_limit,lower_limit);

		
def decreasebwNade(self,higher_limit,lower_limit):
	time.sleep(1)
	if self.curr_bw > lower_limit: 
		bw_old = self.curr_bw
		decrease_factor=float((higher_limit-lower_limit)/30)
		self.curr_bw = self.curr_bw-decrease_factor;
		self.socket_trash.send("CMD changedefbwandceil GW1 "+str(self.curr_bw)+"kbit "+str(bw_old)+"kbit\n")
		#networkControlLog.write(str(time.time())+";"+str(self.curr_bw)+"\n")
		print("[NetworkControl] Bandwidth decreased")
		decreasebwNade(self,higher_limit,lower_limit)
	else:
		bw_old = self.curr_bw	
		self.curr_bw = higher_limit
		self.socket_trash.send("CMD changedefbwandceil GW1 "+str(self.curr_bw)+"kbit "+str(bw_old)+"kbit\n")
		#networkControlLog.write(str(time.time())+";"+str(self.curr_bw)+"\n")
		print('current_bw:'+str(self.curr_bw))
		decreasebwNade(self,higher_limit,lower_limit)
	



def connectZMQ(self):
	context = zmq.Context()
	socket = context.socket(zmq.SUB)
	print("[Network Control] Network Control connected to Decision Entity")
	socket.connect("tcp://132.187.12.97:6666")

	listenTo="6"
	if isinstance(listenTo, bytes):
	        listenTo = listenTo.decode('ascii')
	        socket.setsockopt_string(zmq.SUBSCRIBE, listenTo)
	#SPM performs prioritization of certain flows		
	if mechanism=="spm":
		while True: 
			string_received = socket.recv_string()
			listenTo, clientInfo, prio = string_received.split()
			prio=int(prio)
			client_info_splitted=clientInfo.split(":")
			client_ip=client_info_splitted[0]
			client_port=client_info_splitted[1]
			#Control whether it should be downloaded via priority queue or best-effort queue (default!)
			if prio==1: 
				self.socket_trash.send("CMD addfilter GW1 "+str(client_ip)+" "+str(client_port)+" GW1_PRIORITY_1 1\n")

			else: 
				print "deprio clients"
				self.socket_trash.send("CMD deletefilter GW1 "+str(client_ip)+" "+str(client_port)+" GW1_PRIORITY_1 1\n")
	#NADE performs bandwidth reservation for clients
	if mechanism=="nade":
		while True: 
			string_received = socket.recv_string()
			listenTo, messageType,clientInfo, share, flow_id = string_received.split()
			print clientInfo
			client_info_splitted=clientInfo.split(":")
			client_ip=client_info_splitted[0]
			client_port=client_info_splitted[1]
			#if messagetype is register, then the flow needs to be added
			if messageType=="update":
				print ("UPDATE BANDWIDTH SHARE")
				comm = "CMD changebw "+str(flow_id)+" "+str(share)+"kbit 1\n"
				self.socket_trash.send("CMD changebw "+str(flow_id)+" "+str(float(share)*float(self.curr_bw))+"kbit 1\n")
				print clientInfo

			elif messageType == "register":
				print "REGISTER NEW INSTANCE"
				comm = "CMD addapp "+str(flow_id)+" "+str(client_ip)+" "+str(client_port)+" GW1\n"
				self.socket_trash.send("CMD addapp "+str(flow_id)+" "+str(client_ip)+" "+str(client_port)+" GW1\n")


			elif messageType == "delete":
				print "DELETE OLD INSTANCE"
				comm = "CMD delapp "+str(flow_id)+" "+str(client_ip)+" "+str(client_port)+" GW1\n"
				self.socket_trash.send(comm)
	
		


if __name__=='__main__':
	startEntity()


