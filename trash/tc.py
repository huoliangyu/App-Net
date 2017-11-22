#!/usr/bin/python

# ...
from subprocess import *

# import modules
import subprocess
import tcConfig
import re

class NoInterfaceError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Tc:
    def __init__(self):
        """
        Constructor.
        """
        self.interface = tcConfig.IF
   
    def clearRoot(self):
        """
        Clear your root.
        """
        cmd = "tc qdisc del dev %s root" %(self.interface)
        print cmd
        self.executeCmd(cmd)

    def report(self,splittedCmd):
        """
        Show all queues on our root qdisc.
        Show the number of sent packets and bytes.
        """
        parameter = "-p"
        if len(splittedCmd) == 3:
            parameter = splittedCmd[2]

        if splittedCmd[1].lower() == "all":
            cmd = tcConfig.REPORT["filter"] \
                    %(parameter, self.interface)
            returnSequence1 = self.executeCmd(cmd)
            cmd = tcConfig.REPORT["class"] \
                    %(parameter, self.interface)
            returnSequence1 += self.executeCmd(cmd)
            cmd = tcConfig.REPORT["qdisc"] \
                    %(parameter, self.interface)
            returnSequence1 += self.executeCmd(cmd)
        else :
            cmd = tcConfig.REPORT[splittedCmd[1].lower()] \
                    %(parameter, self.interface)
            print cmd
            returnSequence1 = self.executeCmd(cmd)
        # cmd = "tc qdisc show dev %s" % (self.interface)
        # returnSequence2 = self.executeCmd(cmd)
        # returnSequence1 += returnSequence2
        # print cmd
        return returnSequence1


    def executeCmd(self,cmd):

        # If the following stdout contains this regex, the interface
        # of the configuration was not found
        regex = re.compile("Cannot find device")
        # create a stdout, stderr for command's output
        stdout,stderr = subprocess.Popen(cmd.split(), stdout=PIPE, \
                stderr=PIPE).communicate()
        print "stderr: " + stderr
        # match from the beginning
        matcher = regex.match(stderr)
        # if matcher, then there is no interface
        if matcher:
            print "Result: " + matcher.group()
            raise NoInterfaceError(4)
        elif len(stderr) > 0:
            print "Result: " + stderr
            print "Cmd was: " + cmd + "\n"
        return stdout
        
    def removeFilterByHandle(self,  filterHandle,  prio,  parentId):
        print filterHandle
        # make command
	if isinstance(filterHandle, basestring):
	    cmdHeader = "tc filter del dev %s parent %s protocol ip prio %s handle %s u32 " \
	    %(self.interface, parentId, prio,  filterHandle)
	    cmd = cmdHeader
	    self.executeCmd(cmd)
	else:
	    for i in filterHandle:
	        cmdHeader = "tc filter del dev %s parent %s protocol ip prio %s handle %s u32 " \
		%(self.interface, parentId, prio, i)
	        cmd = cmdHeader
	        self.executeCmd(cmd)

    def getFilterNumber(self, dstPort, dstIp, parentGW):
        print "[tc] GetFilterNumber called!"
        dstPortHEX = self.decimalPort2hexadecimalPort(dstPort)
        dstIpHEX = self.decimalIP2hexadecimalIP(dstIp)
        cmd = "/bin/sh -c".split()
        cmd.append("tc filter show dev %s parent %s \
                   | tr '\\n' 'a' \
                   | sed -re 's/filter/\\nfilter/g' \
                   | grep -E \"%s.+%s\" \
                   | grep -o 8[0-9a-f][0-9a-f]::[0-9a-f][0-9a-f][0-9a-f]" % (self.interface, parentGW, dstIpHEX.lower(), dstPortHEX.lower()))
	stdout,stderr = subprocess.Popen(cmd, stdout=PIPE, stderr=PIPE).communicate()
        stdout = stdout[:-1] # delete \n at the end
        return stdout.split("\n")

    def decimalIP2hexadecimalIP(self, dstIP):
        # convert ip from decimal to hexadecimal representation.
        ipArray = str(dstIP).split('.')
        dstIPHex = "%.2X%.2X%.2X%.2X" \
                % (int(ipArray[0]),int(ipArray[1]), \
                int(ipArray[2]),int(ipArray[3]))
        return dstIPHex

    def decimalPort2hexadecimalPort(self, dstPort):
        # convert port from decimal to hexadecimal representation
        dstPortHex = "%.4X" % (int(dstPort))
        return dstPortHex
