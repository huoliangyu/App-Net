#!/usr/bin/python

import socket
import threading
import SocketServer
import time

class ThreadedTCPRequestHandler(SocketServer.BaseRequestHandler):

    def handle(self):
        data = self.request.recv(1024)
        cur_thread = threading.currentThread()
        response = "%s: %s" % (cur_thread.getName(), data)
        self.request.send(response)

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

class TCPServerRequestHandler2(SocketServer.BaseRequestHandler):
    """
    look docs.python.org/library/socketserver.html for further
    instructions
    """

    def handle(self):
        addr = self.client_address[0]
        print "[%s] wrote: " % addr
        while True:
            s = self.request.recv(1024)
            if s:
                print "[%s] %s" % (addr, s)
            else:
                print "[%s] Verbindung geschlossen" % addr
                break



def client(ip, port, message):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((ip, port))
    sock.send(message)
    response = sock.recv(1024)
    print "Received: %s" % response
    sock.close()

if __name__ == "__main__":
    cmd = 'Test 1 2 3'
    splittedCmd = cmd.split()
    print splittedCmd[0]
    print cmd.split()[0]
