import zmq
import time

context_send_nc = zmq.Context()
socket_send_nc = context_send_nc.socket(zmq.PUB)
socket_send_nc.bind("tcp://*:6666")


time.sleep(4)

while True:
	socket_send_nc.send_string("%s %s %i" %("6","172.16.15.2:20",int(float(1))))
	time.sleep(10)
	socket_send_nc.send_string("%s %s %i" %("6","172.16.15.2:20",int(float(0))))
	time.sleep(10)
