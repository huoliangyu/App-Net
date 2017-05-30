import zmq
import os
import socket
import commands
import subprocess  
from subprocess import Popen, PIPE
import time
import threading
import fileinput



proc = Popen(['sudo python path_to_trash/trash.py'], shell=True, stdin=None, stdout=True, stderr=None, close_fds=True)

class NetworkControl():

	def __init__(self,curr_bw=''):


		time.sleep(1);
		self.socket_trash = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket_trash.connect(('localhost',10101))
		self.socket_trash.send("start PRIO_HTB \n")
		time.sleep(5);

		self.curr_bw=1440
		

		#use this in scenarios with varying bandwidth
		#bw_change_thread = threading.Thread(target=changebw,args=(self,))
		#bw_change_thread.daemon = True
		#bw_change_thread.start()



		connectZMQ(self)

def startEntity():
	te = NetworkControl();



def changebw(self):
	time.sleep(30);
	if self.curr_bw==1600:
		self.socket_trash.send("CMD changeRateandCeilGWClass GW1 1200kbit\n")
		self.curr_bw=1200
		changebw(self);
	if self.curr_bw==1200:
		self.socket_trash.send("CMD changeRateandCeilGWClass GW1 1600kbit\n")
		self.curr_bw=1600
		changebw(self);



def connectZMQ(self):
	context = zmq.Context()
	socket = context.socket(zmq.SUB)
	print("[Network Control] Network Control connected to Decision Entity")
	socket.connect("tcp://192.168.1.2:6666")

	listenTo="6"
	if isinstance(listenTo, bytes):
	        listenTo = listenTo.decode('ascii')
	        socket.setsockopt_string(zmq.SUBSCRIBE, listenTo)
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
			print clientInfo

		else: 
			print "deprio clients"
			self.socket_trash.send("CMD deletefilter GW1 "+str(client_ip)+" "+str(client_port)+" GW1_PRIORITY_1 1\n")

			print clientInfo


if __name__=='__main__':
	startEntity()


