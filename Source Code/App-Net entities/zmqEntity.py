import time
import zmq
import datetime
import sys



if len(sys.argv)<2:
	print "Give the folder to save Log!"
	sys.exit()
print 'Argument List:', str(sys.argv)

for arg in sys.argv:
    path_for_log=arg

now = datetime.datetime.now()
now = now.strftime("%Y-%m-%d %H:%M")
timestamp = int(time.time())
fo = open(str(path_for_log)+"/zmqLog_"+now+".txt", "w")
fo.write("#timestamp,zmg_is_sender,zmg_is_receiver,networkEntity,packetInterceptor,decisionEntity,Tapas,networkControl\n");

# Needed for communication with deciscionEntity
# sends message about buffer-state (app-monitoring, listenTo=1)
# sends message about network-parameter (network-monitoring, listenTo=2)
# in this case: PUBlisher
'''=================================='''
'''communication with deciscion entity'''
contextDE = zmq.Context()
socketDE = contextDE.socket(zmq.PUB)
socketDE.bind("tcp://*:1111")
'''=================================='''


'''=================================='''
'''communication with tapas player'''
contextTapas = zmq.Context()
socketTapas = contextTapas.socket(zmq.PUB)
socketTapas.bind("tcp://*:4444")
'''=================================='''


'''========================================================'''
'''Needed for telling NetworkControl if prioritization should be performed'''
context_send_nc = zmq.Context()
socket_send_nc = context_send_nc.socket(zmq.PUB)
socket_send_nc.bind("tcp://*:6666")
'''========================================================'''


'''===================================='''
'''communication with the tapas instances'''
'''receive app related information'''
# Needed for communication with packetInterceptor
# receives messages about buffer-state etc
# in this case: SUBscriber
contextPI = zmq.Context()
socketPI = contextPI.socket(zmq.SUB)
print("Make Connection to PacketInterceptor")
socketPI.connect("tcp://192.168.1.10:9000")
socketPI.connect("tcp://192.168.1.10:9001")
socketPI.connect("tcp://192.168.1.10:9002")
socketPI.connect("tcp://192.168.1.10:9003")
socketPI.connect("tcp://192.168.1.10:9004")
socketPI.connect("tcp://192.168.1.10:9005")
socketPI.connect("tcp://192.168.1.10:9006")

# define sth the client is listening to
# later: define one for each client with sth client-specific
# for example listen to own port
listenToPI="2"

if isinstance(listenToPI, bytes):
    listenToPI = listenToPI.decode('ascii')
    socketPI.setsockopt_string(zmq.SUBSCRIBE, listenToPI)
'''=================================='''




'''Receive information about get-request from the grf (get request fetcher)
former: it was the packet interceptor
ip is .5 and we use the port 7777 with listen_to 7'''

contextGRF = zmq.Context()
socketGRF = contextGRF.socket(zmq.SUB)
socketGRF.connect("tcp://192.168.1.5:7777");

listenToGRF="7"

if isinstance(listenToGRF,bytes):
	listenToGRF = listenToGRF.decode('ascii')
	socketGRF.setsockopt_string(zmq.SUBSCRIBE, listenToGRF)




'''===================================='''
'''receive information about prioritziation'''
context_ansDE = zmq.Context()
socket_ansDE = context_ansDE.socket(zmq.SUB)
socket_ansDE.connect("tcp://192.168.1.10:5555")

listenToAnsDE="5"

if isinstance(listenToAnsDE, bytes):
    listenToAnsDE = listenToAnsDE.decode('ascii')
    socket_ansDE.setsockopt_string(zmq.SUBSCRIBE, listenToAnsDE)
'''=================================='''



'''===================================='''
'''communication with Network Entity'''
# Needed for communication with packetInterceptor
# receives messages about buffer-state etc
# in this case: SUBscriber
contextNE = zmq.Context()
socketNE = contextNE.socket(zmq.SUB)
print("Make Connection to NetworkEntity")
socketNE.connect("tcp://192.168.1.5:3333")

# define sth the client is listening to
# later: define one for each client with sth client-specific
# for example listen to own port
listenToNE="3"

if isinstance(listenToNE, bytes):
    listenToNE = listenToNE.decode('ascii')
    socketNE.setsockopt_string(zmq.SUBSCRIBE, listenToNE)
'''=================================='''


print("2")
poller = zmq.Poller()
poller.register(socketNE, zmq.POLLIN)
poller.register(socketPI, zmq.POLLIN)
poller.register(socket_ansDE, zmq.POLLIN)
poller.register(socketGRF, zmq.POLLIN)

#maybe second while true can be removed
while True:
	try:
        	socks = dict(poller.poll())
    	except KeyboardInterrupt:
        	break

	if socketNE in socks:
		print('==> received information from networkEntity')
		#if something is received from the networkEntity
		stringNE = socketNE.recv(zmq.DONTWAIT)
		#print("received from 3333")
		fo.write(str(time.time())+";0;1;1;0;0;0;0\n")
		listenToNE,cur_throughputBE, cur_throughputPrio = stringNE.split()
		socketDE.send_string("%s %s %f %f" % ("1", "networkInfo", float(cur_throughputBE), float(cur_throughputPrio)))
		#print("sent over 1111")
		fo.write(str(time.time())+";1;0;0;0;1;0;0\n")
		fo.flush()

	if socketPI in socks:
	#if something is received from the packetInterceptor
		stringPI = socketPI.recv_string(zmq.DONTWAIT)
		#print("receive from 2222 packetInterceptor")
		print("received from client an info!!")
		fo.write(str(time.time())+";0;1;0;0;0;1;0\n")
		listenToPI,cur_buffer,chunkSize,quali,segmentDur, clientInfo, t_pid = stringPI.split()
		print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
		print("buffer "+str(cur_buffer))
		print("chunkSize "+str(chunkSize))
		print("quali "+str(quali))
		print("segmentDur "+str(segmentDur))
		print("clientInfo "+str(clientInfo))
		print("t_pid "+str(t_pid))
		socketDE.send_string("%s %s %f %f %f %f %s %s" % ("1", "appInfo" , float(cur_buffer), float(chunkSize), float(quali), float(segmentDur), clientInfo, str(t_pid)))
		#print("sent over 1111")
		fo.write(str(time.time())+";1;0;0;0;1;0;0\n")
		fo.flush()		
#print("[ZMQ-Entity] ZMQ-Entity received Data from PacketInterceptor. Current Buffer is %s, chunkSize is %s quali is %s " % (cur_buffer,chunkSize, quali))


	if socketGRF in socks:
		stringGRF = socketGRF.recv_string(zmq.DONTWAIT)
		fo.write(str(time.time())+";0;1;0;1;0;0;0\n")
		listenToGRF,s_addr,s_port = stringGRF.split()
		print('new webpage load:')
		print(str(s_addr)+" "+str(s_port))
		socketDE.send_string("%s %s %s %s" % ("1","websiteInfo",  str(s_addr), str(s_port)))
		#was wir weiter senden wollen: socketDE.send_string
		fo.write(str(time.time())+";1;0;0;0;1;0;0\n")
		fo.flush()
		
	
	if socket_ansDE in socks:
		print('==> received information from decision entity')
		string_ansDE = socket_ansDE.recv(zmq.DONTWAIT)
		fo.write(str(time.time())+";0;1;0;0;1;0;0\n")
		listenToAnsDE, clientInfo ,prio= string_ansDE.split()
		#send prioritization information to Network Entity and to Tapas Player
		socketTapas.send_string("%s %i" % (clientInfo, int(float(prio))))
		print("info for "+str(clientInfo))
		fo.write(str(time.time())+";1;0;0;0;0;1;0\n")
		socket_send_nc.send_string("%s %s %i" %("6",clientInfo, int(float(prio))))
		fo.write(str(time.time())+";1;0;0;0;0;0;1\n")
		fo.flush()
		

	
	
	


