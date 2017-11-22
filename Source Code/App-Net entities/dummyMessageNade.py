import zmq
import time

context_send_nc = zmq.Context()
socket_send_nc = context_send_nc.socket(zmq.PUB)
socket_send_nc.bind("tcp://*:6666")


time.sleep(4)

while True:
	socket_send_nc.send_string("%s %s %s %f %i" %("6", "register","172.16.25.2:20",(float(0.7)),1))
	time.sleep(10)
	socket_send_nc.send_string("%s %s %s %f %i" %("6", "update", "172.16.25.2:20",(float(0.7)),1))
	time.sleep(10)
	socket_send_nc.send_string("%s %s %s %f %i" %("6", "delete", "172.16.25.2:20",(float(0.7)),1))
	time.sleep(10)
