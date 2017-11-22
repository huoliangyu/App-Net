#!/usr/bin/python

# We construct the following queue system
#
#                               1:
#               _________________|_________________
#              /                 |                 \
#             /                  |                  \
#           1:1                 1:2                 1:3
#            |                   |                   |
#          11:                 12:                 13:
#     _______|_______     _______|_______     _______|_______
#    |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
# 111:112:113:114:115:121:122:123:124:125:131:132:133:134:135:
#
# root 1: htb
# classes: 1:1 htb rate 3000kbit, 1:2 htb 3000kbit, 1:3 htb 3000kbit
# prio qdisc 111:, 112:, 113:, 114:, 115:,
# prio qdisc 121:, 122:, 123:, 124:, 125:,
# prio qdisc 131:, 132:, 133:, 134:, 135:,

# import modules
import tcPRIOConfig
from tcPRIOConfig import GW_CLASS

# import classes
from tc import Tc
from tc import NoInterfaceError

class TcPRIO(Tc):
    """
    TcPRIO: strategy class for Testbed use.
    Special filter for payload matching.
    """

    def __init__(self, optionSFQ):
        """
        Constructor. Inherits from TC
        """
        Tc.__init__(self)
        self.optionSFQ = optionSFQ

    def startStrategy(self):
        """
        Start your strategy.
        """
        try:
            self.clearRoot()
            self.addRootQdisc()
            self.clearRoot()
            self.addRootQdisc()
            self.addClass("1:", \
                    tcPRIOConfig.GW_CLASS["GW1_CLASS"], \
                    tcPRIOConfig.GW1_bandwidth)
            self.addClass("1:", \
                    tcPRIOConfig.GW_CLASS["GW2_CLASS"], \
                    tcPRIOConfig.GW2_bandwidth)
            self.addClass("1:", \
                    tcPRIOConfig.GW_CLASS["GW3_CLASS"], \
                    tcPRIOConfig.GW3_bandwidth)
            # first run through three PRIO qdiscs
            for i in range(1,4):
                self.addPRIO("1:%s" %i, \
                    tcPRIOConfig.GW["GW%s" %i], \
                    "5", \
                    tcPRIOConfig.GW_PRIOMAP[i - 1])
                if self.optionSFQ:
                    for j in range(1,6):
                        self.addSFQ("1%s:%s" %(i,j), "1%s%s" %(i,j))
                else:
                    for j in range(1,6):
                        self.addFIFO("1%s:%s" %(i,j), "1%s%s" %(i,j))
            # Add filter for gateways on root qdisc
            self.addRootFilter("Cmd AddRootFilter %s * %s 1" \
                    %(tcPRIOConfig.GW_IPs["GW1_IP"], \
                    tcPRIOConfig.GW_CLASS["GW1_CLASS"]))
            self.addRootFilter("Cmd AddRootFilter %s * %s 1" \
                    %(tcPRIOConfig.GW_IPs["GW2_IP"], \
                    tcPRIOConfig.GW_CLASS["GW2_CLASS"]))
            self.addRootFilter("Cmd AddRootFilter %s * %s 1" \
                    %(tcPRIOConfig.GW_IPs["GW3_IP"], \
                    tcPRIOConfig.GW_CLASS["GW3_CLASS"]))
            # add hash tables to PRIO qdiscs
            for i in range(1,4):
                cmd = "tc filter add dev %s parent 1%s: protocol ip \
                        prio 1 u32" %(self.interface, i)
                self.executeCmd(cmd)

        except NoInterfaceError as e:
            print "No Interface Error occured!"
            return "Your specified interface was not found! No strategy set!"

    #### Construction methods ####

    def addRootQdisc(self):
        # add root qdisc without default
        cmd = "tc qdisc add dev %s root handle 1: htb" \
                %(self.interface)
        self.executeCmd(cmd)

    def addClass(self, parent, classid, rate):
        # add three classes
        cmd = "tc class add dev %s parent %s classid %s htb rate %s" \
                % (self.interface, \
                parent, \
                classid, \
                rate)
        self.executeCmd(cmd)

    def addClassCeil(self, parent, classid, rate, ceil):
        pass
    
    def addPRIO(self, parent, handle, bands, priomap):
        cmd = "tc qdisc add dev %s parent %s handle %s prio bands %s \
                priomap %s" %(self.interface, parent, handle, bands, priomap)
        self.executeCmd(cmd)
    
    def addSFQ(self, parent, handle):
        cmd = "tc qdisc add dev %s parent %s \
                handle %s sfq perturb 10" \
                %(self.interface, parent, handle)
        self.executeCmd(cmd)

    def addFIFO(self, parent, handle):
        cmd = "tc qdisc add dev %s parent %s \
                handle %s pfifo limit %s" \
                %(self.interface, parent, handle, tcPRIOConfig.PFIFO_LIMIT)
        self.executeCmd(cmd)
        print "FIFO to dev %s parent %s handle %s added." \
                %(self.interface, parent, handle)
        
    #### Communication methods ####

    def addRootFilter(self, cmd):
        """
        Install a filter on the root qdisc 1:. This matches a flow to a gateway.
        Normally, we do not have to do any changes during runtime.
        """

        # split cmd
        splittedCmd = cmd.split()
        dstIP = splittedCmd[2]
        dstPort = splittedCmd[3]
        flowid = splittedCmd[4]
        prio = splittedCmd[5]

        # We do not have to convert since we do not need to seek for the
        # corresponding IP address in the packet's payload.
        cmd = "tc filter add dev %s protocol ip parent 1:0 prio %s u32 \
                match ip dst %s/32 classid %s" \
                %(self.interface, prio, dstIP, flowid)
        print cmd
        self.executeCmd(cmd)

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
                %(self.interface, tcPRIOConfig.GW[dstGW], prio)
        cmdMatchIP = "match u32 0x%s 0xffffffff at 52 " \
                %(dstIPHex)
        cmdMatchPort = "match u16 0x%s 0xffff at 58 " \
                %(dstPortHex)
        cmdFlowId = tcPRIOConfig.GW_PRIORITY[flowid]

        # make cmd and execute
        cmd = cmdHeader + cmdMatchIP + cmdMatchPort + cmdFlowId
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

        handle = self.getFilterNumber(dstPort, dstIP, tcPRIOConfig.GW[dstGW])   
        # print handle
        
        # make command
        for i in handle:
            # print "." + i + "."
            cmdHeader = "tc filter del dev %s parent %s protocol ip prio %s handle %s u32 " \
            %(self.interface, tcPRIOConfig.GW[dstGW], prio, i)
            cmd = cmdHeader
            self.executeCmd(cmd)

class TcPRIO2(Tc):
    """
    TcPRIO2: strategy class for Testbed use.
    Special filter for payload matching.
    """

    def __init__(self, optionSFQ):
        """
        Constructor. Inherits from TC
        """
        Tc.__init__(self)
        self.optionSFQ = optionSFQ

    def startStrategy(self):
        """
        Start your strategy.
        """
        try:
            self.clearRoot()
            self.addRootQdisc()
            self.clearRoot()
            self.addRootQdisc()
            self.addClass("1:", \
                    tcPRIOConfig.GW_CLASS["GW1_CLASS"], \
                    tcPRIOConfig.GW1_bandwidth)
            self.addClass("1:", \
                    tcPRIOConfig.GW_CLASS["GW2_CLASS"], \
                    tcPRIOConfig.GW2_bandwidth)
            self.addClass("1:", \
                    tcPRIOConfig.GW_CLASS["GW3_CLASS"], \
                    tcPRIOConfig.GW3_bandwidth)

            # first run through three PRIO qdiscs
            for i in range(1,4):
                self.addPRIO("1:%s" %i, \
                    tcPRIOConfig.GW["GW%s" %i], \
                    tcPRIOConfig.AMOUNT_PRIOS, \
                    tcPRIOConfig.GW_PRIOMAP[i - 1])
                if self.optionSFQ:
                    for j in range(1,tcPRIOConfig.AMOUNT_PRIOS + 1):
                        self.addSFQ("1%s:%s" %(i,j), "1%s%s" %(i,j))
                else:
                    for j in range(1,tcPRIOConfig.AMOUNT_PRIOS + 1):
                        self.addFIFO("1%s:%s" %(i,j), "1%s%s" %(i,j), j)

            # Add filter for gateways on root qdisc
            self.addRootFilter("Cmd AddRootFilter %s * %s 1" \
                    %(tcPRIOConfig.GW_IPs["GW1_IP"], \
                    tcPRIOConfig.GW_CLASS["GW1_CLASS"]))
            self.addRootFilter("Cmd AddRootFilter %s * %s 1" \
                    %(tcPRIOConfig.GW_IPs["GW2_IP"], \
                    tcPRIOConfig.GW_CLASS["GW2_CLASS"]))
            self.addRootFilter("Cmd AddRootFilter %s * %s 1" \
                    %(tcPRIOConfig.GW_IPs["GW3_IP"], \
                    tcPRIOConfig.GW_CLASS["GW3_CLASS"]))
            
            # add hash tables to PRIO qdiscs
            for i in range(1,4):
                cmd = "tc filter add dev %s parent 1%s: protocol ip \
                        prio 1 u32" %(self.interface, i)
                self.executeCmd(cmd)

        except NoInterfaceError as e:
            print "No Interface Error occured!"
            return "Your specified interface was not found! No strategy set!"

    #### Construction methods ####

    def addRootQdisc(self):
        # add root qdisc without default
        cmd = "tc qdisc add dev %s root handle 1: htb" \
                %(self.interface)
        self.executeCmd(cmd)

    def addClass(self, parent, classid, rate):
        # add three classes
        cmd = "tc class add dev %s parent %s classid %s htb rate %s" \
                % (self.interface, \
                parent, \
                classid, \
                rate)
        self.executeCmd(cmd)

    def addClassCeil(self, parent, classid, rate, ceil):
        pass
    
    def addPRIO(self, parent, handle, bands, priomap):
        cmd = "tc qdisc add dev %s parent %s handle %s prio bands %s \
                priomap %s" %(self.interface, parent, handle, bands, priomap)
        self.executeCmd(cmd)
    
    def addSFQ(self, parent, handle):
        cmd = "tc qdisc add dev %s parent %s \
                handle %s sfq perturb 10" \
                %(self.interface, parent, handle)
        self.executeCmd(cmd)

    def addFIFO(self, parent, handle, queue_number):
        queue_size = 0
	if len(tcPRIOConfig.PFIFO_LIMIT) == 1: 
            queue_size = tcPRIOConfig.PFIFO_LIMIT
	else: 
	    if len(tcPRIOConfig.PFIFO_LIMIT) != tcPRIOConfig.AMOUNT_PRIOS:
	        sys.exit("Error, length of tcPRIOConfig.PFIFO_LIMIT is not equal to tcPRIOConfig.AMOUNT_PRIOS!")			  
	    queue_size = tcPRIOConfig.PFIFO_LIMIT[queue_number-1]

	cmd = "tc qdisc add dev %s parent %s \
        	handle %s pfifo limit %s" \
		%(self.interface, parent, handle, queue_size)
        self.executeCmd(cmd)
	print "FIFO to dev %s parent %s handle %s with queue size %s added." \
        	% (self.interface, parent, handle, queue_size)
       
 
    #### Communication methods ####

    def addRootFilter(self, cmd):
        """
        Install a filter on the root qdisc 1:. This matches a flow to a gateway.
        Normally, we do not have to do any changes during runtime.
        """

        # split cmd
        splittedCmd = cmd.split()
        dstIP = splittedCmd[2]
        dstPort = splittedCmd[3]
        flowid = splittedCmd[4]
        prio = splittedCmd[5]

        # We do not have to convert since we do not need to seek for the
        # corresponding IP address in the packet's payload.
        cmd = "tc filter add dev %s protocol ip parent 1:0 prio %s u32 \
                match ip dst %s/32 classid %s" \
                %(self.interface, prio, dstIP, flowid)
        print cmd
        self.executeCmd(cmd)

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
                %(self.interface, tcPRIOConfig.GW[dstGW], prio)
        cmdMatchIP = "match u32 0x%s 0xffffffff at 52 " \
                %(dstIPHex)
        cmdMatchPort = "match u16 0x%s 0xffff at 58 " \
                %(dstPortHex)
        cmdFlowId = tcPRIOConfig.GW_PRIORITY[flowid]

        # make cmd and execute
        cmd = cmdHeader + cmdMatchIP + cmdMatchPort + cmdFlowId
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

        handle = self.getFilterNumber(dstPort, dstIP, tcPRIOConfig.GW[dstGW])   
        #print handle
        
        # make command
        for i in handle:
            #print "." + i + "."
            cmdHeader = "tc filter del dev %s parent %s protocol ip prio %s handle %s u32 " \
            %(self.interface, tcPRIOConfig.GW[dstGW], prio, i)
            cmd = cmdHeader
            self.executeCmd(cmd)

if __name__ == "__main__":
    tcPRIO = TcPRIO()
    tcPRIO.startStrategy()
    print "Adding filter ..."
    cmd = "tc filter add dev eth0 parent 11: protocol ip prio 1 u32 \
            match u16 0x0050 0xffff at 56"
    tcPRIO.executeCmd(cmd)
    print "Filter added ..."
