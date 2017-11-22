import tcPRIOHTBConfig
from tcPRIOHTBConfig import GW

from tc import Tc
from tc import NoInterfaceError

class TcPRIOHTB(Tc):
    """
    Class representing the throttling approach.
    Creating classes for each application. This allows direct shaping
    of the bandwidth
    """
    def __init__(self):
        Tc.__init__(self)
        self.name = "PRIO_HTB"
                
    def getStrategyName(self):
        return self.name
        
    def addRootQdisc(self):
        """
        Add a qdisc to your root interface.
        Default is also set here
        """
        print "[tcPRIOHTB] Add the root qdisc!"
        cmd = "tc qdisc add dev %s root handle 1: htb" \
                %(self.interface)
        self.executeCmd(cmd)
     
    def startStrategy(self):
        """
        Start the throttling strategy. Read the throttling config!
        """
        print "[tcPRIOHTB] Setting throttling strategy."
        try:
            # clear the root
            self.clearRoot()
            # set a htb queue on the root
            self.addRootQdisc()
            
            # to be sure, do it again
            self.clearRoot()            
            self.addRootQdisc()
            
            # set one class with limited bandwidth for each gateway
            for i in range(1, len(tcPRIOHTBConfig.GW) + 1):
                
                # get all attributes
                classid = tcPRIOHTBConfig.GW["GW%s" %i]
                gwRate = tcPRIOHTBConfig.GW_bandwidth["GW%s" %i]
                gwCeil = gwRate
                self.addGWClass(classid,  gwRate,  gwCeil)
                                
                for j in range(1, tcPRIOHTBConfig.AMOUNT_PRIOS+1):
                    parent = classid
                    classNumber = j
                    classRate = tcPRIOHTBConfig.MIN_BW
                    classCeil = gwRate
                    self.addGWClassPRIO(parent,  "1:%s%s" %(i,  classNumber), \
                                        classRate,  \
                                        classCeil,  \
                                        str(classNumber));
                    # burst = tcPRIOHTBConfig.BURST
                    # self.addGWClassPRIOBurst(parent,  "1%s:%s" %(i,  classNumber), classRate,  classCeil, burst,   str(classNumber+1));

                    # finally add a fifo for buffering
                    self.addFIFO("1:%s%s" %(i, classNumber), "11%s%s:" %(i, classNumber), j)

                   
                ip = tcPRIOHTBConfig.GW_IPs["GW%s" %i]
                #self.addRootFilter("1:0",  "1",  ip,  parent)
                self.addClassFilterDefault("1:0",  "8",  ip,  "1:%s%s" %(i, tcPRIOHTBConfig.DEFAULT_PRIO))
                                    
        except NoInterfaceError as e:
            print "No Interface Error occured!"
            return "Your specified interface was not found! No strategy set!"

    def addGWClass(self,  classid,  rate,  ceil):
        print "[tcPRIOHTB] Add GW class."
        burst = tcPRIOHTBConfig.BURST
        cmd = "tc class add dev %s \
        parent 1: \
        classid %s \
        htb rate %s \
        burst %s \
        ceil %s" % (self.interface, classid, rate, burst, ceil)
        print "[tcPRIOHTB] Command: " + cmd
        self.executeCmd(cmd)
            
    def addGWClassPRIO(self,  parent,  classid,  rate,  ceil,  priority):
        print "[tcPRIOHTB] Add class " + str(classid) +\
        " with priority" + str(priority)
        cmd = "tc class add dev %s \
        parent %s \
        classid %s \
        htb rate %s \
        ceil %s \
        prio %s" % (self.interface,  parent,  classid,  rate,  ceil, priority)
        self.executeCmd(cmd)

    def addGWClassPRIOBurst(self,  parent,  classid,  rate,  ceil, burst, priority):
        print "[tcPRIOHTB] Add class " + str(classid) +\
        " with priority" + str(priority)
        cmd = "tc class add dev %s \
        parent %s \
        classid %s \
        htb rate %s \
        ceil %s \
        burst %s \
        prio %s" % (self.interface,  parent,  classid,  rate,  ceil, burst, priority)
        self.executeCmd(cmd)
        
    def addRootFilter(self, parent,  prio,  dstIP,  flowid):
        """
        Install a filter on the root qdisc 1:. This matches a flow to a gateway.
        Normally, we do not have to do any changes during runtime.
        """
        
        # We do not have to convert since we do not need to seek for the
        # corresponding IP address in the packet's payload.
        cmd = "tc filter add dev %s protocol ip parent %s prio %s u32 \
                match ip dst %s/24 classid %s" \
                %(self.interface, parent, prio, dstIP, flowid)
        self.executeCmd(cmd)
        
    def addClassFilterDefault(self,  parent,  prio,  dstIP,  flowid):
        """
        Install a class filter for the default traffic.
        """
        cmd = "tc filter add dev %s protocol ip parent %s \
        prio %s u32 \
        match ip dst %s/24 \
        classid %s" %(self.interface,  parent,  prio,  dstIP,  flowid)
        self.executeCmd(cmd)
        
    def addFIFO(self, parent, handle, queue_number):
        queue_size = 0
	if len(tcPRIOHTBConfig.PFIFO_LIMIT) == 1: 
            queue_size = tcPRIOHTBConfig.PFIFO_LIMIT
	else: 
	    if len(tcPRIOHTBConfig.PFIFO_LIMIT) != tcPRIOHTBConfig.AMOUNT_PRIOS:
	        sys.exit("Error, length of tcPRIOHTBConfig.PFIFO_LIMIT is not equal to tcPRIOHTBConfig.AMOUNT_PRIOS!")			  
	    queue_size = tcPRIOHTBConfig.PFIFO_LIMIT[queue_number-1]

	cmd = "tc qdisc add dev %s parent %s \
        	handle %s pfifo limit %s" \
		%(self.interface, parent, handle, queue_size)
        self.executeCmd(cmd)
	print "FIFO to dev %s parent %s handle %s with queue size %s added." \
        	% (self.interface, parent, handle, queue_size)
 




        
    #### Communication methods ####
        
        
        
    def addFilter(self, splittedCmd):
        """
        Set a filter for a flow. To identify the flow, give the dstIP and
        the dstPort. The last byte of each ip address is taken in order
        to decide to which prio class the ip address belongs.
        If a flow will be shift, the filter rules for this flow must also
        be shift to the new flow's gateway.
        """

        # split cmd
        dstGW = splittedCmd[2]
        dstIP = splittedCmd[3]
        dstPort = splittedCmd[4] # wildcard * I FORGOT WHAT THIS MEANS
        flowid = splittedCmd[5]
        prio = splittedCmd[6]

        # convert ip from decimal to hexadecimal representation
        dstIPHex = self.decimalIP2hexadecimalIP(dstIP)

        # conver prot from decimal to hexadecimal representation
        dstPortHex = self.decimalPort2hexadecimalPort(dstPort)
        
        # split ip adress
        ipArray = str(dstIP).split('.')
       
        # make command
        cmdHeader = "tc filter add dev %s parent %s protocol ip prio %s  u32 " \
                %(self.interface, "1:0", prio) # %(self.interface, tcPRIOHTBConfig.GW[dstGW], prio)
        #cmdMatchIP = "match u32 0x%s 0xffffffff at 52 " \
        cmdMatchIP = "match u32 0x%s 0xffffffff at 16 " \
                %(dstIPHex)
        #cmdMatchPort = "match u16 0x%s 0xffff at 58 " \
        cmdMatchPort = "match u16 0x%s 0xffff at 22 " \
                %(dstPortHex)
        cmdFlowId = tcPRIOHTBConfig.GW_PRIORITY[flowid]
        
        # make cmd and execute
        cmd = cmdHeader + cmdMatchIP + cmdMatchPort + cmdFlowId
        #print cmd
	self.executeCmd(cmd)

	# bug add a nonsense cmd - otherwise delete does not find the filter rule
        cmdMatchIP = "match u32 0xAAAAAAAA 0xffffffff at 16 " 
        cmd = cmdHeader + cmdMatchIP + cmdMatchPort + cmdFlowId
       # print cmd
	self.executeCmd(cmd)


    def deleteFilter(self, splittedCmd):
        """
        Delete a filter from TC. To identify the flow, give the dstIP and
        the dstPort. 
        If a flow will be shift, the filter rules for this flow must also
        be shift to the new flow's gateway.
        """

        # split cmd
        dstGW = splittedCmd[2]
        dstIP = splittedCmd[3]
        dstPort = splittedCmd[4] # wildcard *
        flowid = splittedCmd[5]
        prio = splittedCmd[6]

        # convert ip from decimal to hexadecimal representation
        dstIPHex = self.decimalIP2hexadecimalIP(dstIP)

        # conver prot from decimal to hexadecimal representation
        dstPortHex = self.decimalPort2hexadecimalPort(dstPort)
        
        # split ip adress
        ipArray = str(dstIP).split('.')

        handle = self.getFilterNumber(dstPort, dstIP, "1:0") # tcPRIOHTBConfig.GW[dstGW])   
        #print handle
        
        # make command
        for i in handle:
            #print "." + i + "."
            cmdHeader = "tc filter del dev %s parent %s protocol ip prio %s handle %s u32 " \
            %(self.interface, "1:0", prio, i) #   %(self.interface, tcPRIOHTBConfig.GW[dstGW], prio, i) 
            cmd = cmdHeader
            self.executeCmd(cmd)



    def changeRateandCeilGWClass(self,gateway,rate_and_ceil):
        print "[tcPRIOHTB] Change rate of GW class"
        classid = tcPRIOHTBConfig.GW["%s" %gateway]
        gwRate = rate_and_ceil
        gwCeil = rate_and_ceil
        burst = tcPRIOHTBConfig.BURST
        cmd = "tc class change dev %s \
        parent 1: \
        classid %s \
        htb rate %s \
        burst %s \
        ceil %s" % (self.interface, classid, gwRate, burst, gwCeil)
 	print "[tcPRIOHTB] Command: " + cmd
        self.executeCmd(cmd)
       



if __name__ == "__main__":
    tcPRIOHTB = TcPRIOHTB()
    tcPRIOHTB.startStrategy()
    print "Adding filter ..."
    cmd = "tc filter add dev eth0 parent 11: protocol ip prio 1 u32 \
            match u16 0x0050 0xffff at 56"
    tcPRIOHTB.executeCmd(cmd)
    print "Filter added ..."
