import time
import zmq
import datetime
import sys

if len(sys.argv)<2:
	print "Give the folder to save log!"
	sys.exit()
print 'Argument List:', str(sys.argv)

for arg in sys.argv:
    path_for_log=arg

now = datetime.datetime.now()
now = now.strftime("%Y-%m-%d %H:%M")
timestamp = int(time.time())
fo = open(str(path_for_log)+"/zmqLog_"+now+".txt", "w")

'''
Create the log file. 
timestamp: unix timestamp of message in/out
message_out: the message broker is sender (acts as PUBlisher)
message_in: the message broker is receiver (acts as SUBscriber)
NM: communication with network monitoring
AM: communication with application monitoring
PM: communication with policy manager
AC: communication with application control 
NC: communication with network control 
'''
fo.write("#timestamp,message_out,message_in,NM,AM,PM,AC,NC\n");

# Communication with Policy Manager
# Sends client information to PM (Message Broker -> PM, listenTo=1)
# Sends network informatino to PM (Message Broker -> PM, listenTo=2)
# Message Broker is PUBlisher
'''=================================='''
'''Communication with Policy Manager'''
contextDE = zmq.Context()
socketDE = contextDE.socket(zmq.PUB)
socketDE.bind("tcp://*:1111")
'''=================================='''

# Communication with the Tapas Player 
# Sends information about the PM's prioritization decision (Message Broker -> Application)
# Message Broker is PUBlisher
'''=================================='''
'''Communication with Tapas Player'''
contextTapas = zmq.Context()
socketTapas = contextTapas.socket(zmq.PUB)
socketTapas.bind("tcp://*:4444")
'''=================================='''

# Communication with Network Control 
# Send information about the PM's prioritization decision (Message Broker -> Network)
# Message Broker is PUBlisher
'''========================================================'''
'''Communication with Network Control'''
context_send_nc = zmq.Context()
socket_send_nc = context_send_nc.socket(zmq.PUB)
socket_send_nc.bind("tcp://*:6666")
'''========================================================'''

# Communication with Tapas Player (Application Monitoring -> Message Broker)
# Receives information about application parameters (e.g. buffer state)
# Message Broker is SUBscriber
'''========================================================'''
'''Communication with all Tapas instances'''
contextPI = zmq.Context()
socketPI = contextPI.socket(zmq.SUB)
socketPI.connect("tcp://192.168.1.10:9000")
socketPI.connect("tcp://192.168.1.10:9001")
socketPI.connect("tcp://192.168.1.10:9002")
socketPI.connect("tcp://192.168.1.10:9003")
socketPI.connect("tcp://192.168.1.10:9004")
socketPI.connect("tcp://192.168.1.10:9005")
socketPI.connect("tcp://192.168.1.10:9006")

listenToPI="2"

if isinstance(listenToPI, bytes):
    listenToPI = listenToPI.decode('ascii')
    socketPI.setsockopt_string(zmq.SUBSCRIBE, listenToPI)
'''========================================================='''



# Communication with Get Request Fetcher (Application Monitoring -> Message Broker)
# Receives information about new web page loading events
# Message Broker is SUBscriber
'''========================================================='''
'''Communication with GRF'''
contextGRF = zmq.Context()
socketGRF = contextGRF.socket(zmq.SUB)
socketGRF.connect("tcp://192.168.1.5:7777");

listenToGRF="7"

if isinstance(listenToGRF,bytes):
	listenToGRF = listenToGRF.decode('ascii')
	socketGRF.setsockopt_string(zmq.SUBSCRIBE, listenToGRF)
'''========================================================='''


# Communication with Policy Manager (PM -> Message Broker)
# Receives information about decisions
# Message Broker is SUBscriber
'''========================================================='''
'''Receive information about PM decision'''
context_ansDE = zmq.Context()
socket_ansDE = context_ansDE.socket(zmq.SUB)
socket_ansDE.connect("tcp://192.168.1.10:5555")

listenToAnsDE="5"

if isinstance(listenToAnsDE, bytes):
    listenToAnsDE = listenToAnsDE.decode('ascii')
    socket_ansDE.setsockopt_string(zmq.SUBSCRIBE, listenToAnsDE)
'''========================================================='''

# Communication with Network Monitoring (NM -> Message Broker)
# Receives regular bandwidth updates
# Message Broker is SUBscriber
'''========================================================='''
'''Receive information from network monitoring'''
contextNE = zmq.Context()
socketNE = contextNE.socket(zmq.SUB)
print("Make Connection to NetworkEntity")
socketNE.connect("tcp://192.168.1.5:3333")

listenToNE="3"

if isinstance(listenToNE, bytes):
    listenToNE = listenToNE.decode('ascii')
    socketNE.setsockopt_string(zmq.SUBSCRIBE, listenToNE)
'''========================================================='''



poller = zmq.Poller()
poller.register(socketNE, zmq.POLLIN)
poller.register(socketPI, zmq.POLLIN)
poller.register(socket_ansDE, zmq.POLLIN)
poller.register(socketGRF, zmq.POLLIN)


while True:
	try:
        	socks = dict(poller.poll())
    	except KeyboardInterrupt:
        	break

	if socketNE in socks:
		stringNE = socketNE.recv(zmq.DONTWAIT)
		fo.write(str(time.time())+";0;1;1;0;0;0;0\n")
		listenToNE,cur_throughputBE, cur_throughputPrio = stringNE.split()
		socketDE.send_string("%s %s %f %f" % ("1", "networkInfo", float(cur_throughputBE), float(cur_throughputPrio)))
		fo.write(str(time.time())+";1;0;0;0;1;0;0\n")
		fo.flush()

	if socketPI in socks:
		stringPI = socketPI.recv_string(zmq.DONTWAIT)
		fo.write(str(time.time())+";0;1;0;0;0;1;0\n")
		listenToPI,cur_buffer,chunkSize,quali,segmentDur, clientInfo, t_pid = stringPI.split()
		#print("buffer "+str(cur_buffer))
		#print("chunkSize "+str(chunkSize))
		#print("quali "+str(quali))
		#print("segmentDur "+str(segmentDur))
		#print("clientInfo "+str(clientInfo))
		#print("t_pid "+str(t_pid))
		socketDE.send_string("%s %s %f %f %f %f %s %s" % ("1", "appInfo" , float(cur_buffer), float(chunkSize), float(quali), float(segmentDur), clientInfo, str(t_pid)))
		fo.write(str(time.time())+";1;0;0;0;1;0;0\n")
		fo.flush()		


	if socketGRF in socks:
		stringGRF = socketGRF.recv_string(zmq.DONTWAIT)
		fo.write(str(time.time())+";0;1;0;1;0;0;0\n")
		listenToGRF,s_addr,s_port = stringGRF.split()
		#print('new webpage load:')
		#print(str(s_addr)+" "+str(s_port))
		socketDE.send_string("%s %s %s %s" % ("1","websiteInfo",  str(s_addr), str(s_port)))
		fo.write(str(time.time())+";1;0;0;0;1;0;0\n")
		fo.flush()
		
	
	if socket_ansDE in socks:
		string_ansDE = socket_ansDE.recv(zmq.DONTWAIT)
		fo.write(str(time.time())+";0;1;0;0;1;0;0\n")
		listenToAnsDE, clientInfo ,prio= string_ansDE.split()
		#Send prioritization information to Network Entity and to Tapas Player
		socketTapas.send_string("%s %i" % (clientInfo, int(float(prio))))
		print("info for "+str(clientInfo))
		fo.write(str(time.time())+";1;0;0;0;0;1;0\n")
		socket_send_nc.send_string("%s %s %i" %("6",clientInfo, int(float(prio))))
		fo.write(str(time.time())+";1;0;0;0;0;0;1\n")
		fo.flush()
		

	
	
	


