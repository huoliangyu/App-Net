#!/usr/bin/python

# We construct the following queue system:
#               1:           root qdisc
#               |
#              1:1           child class maximum 1000kbit
#             /   \
#            /     \
#          1:10     1:11      leaf classes with 300kbit and 200kbit
#           |        |        1:11: 300kbit ceil
#          10:      11:       qdiscs
#         (sfq)    (sfq)

# import modules
import tcSFQConfig
# import tcSFQConfigTestBed

# import class
from tc import Tc
from tc import NoInterfaceError

class TcSFQ(Tc):
    """
    TcSFQ: strategy class for normal use without filter's
    special payload matching. TcSFQ inherits/derives from
    Tc.
    Attributes from Tc:
    Tc.
    """

    # Constructor
    def __init__(self):
        Tc.__init__(self)

    def startStrategy(self):
        """
        Start your strategy. Check, if your specified interface from
        your TcSFQConfiguration file is available. Otherwise, this
        class will catch a NoInterfaceError and brief the user.
        """
        try:
            self.clearRoot()
            self.addRootQdisc()
            self.addClass("parent 1:","classid 1:1", \
                tcSFQConfig.CHILD_CLASS_MAXIMUM)
            self.addClass("parent 1:1", "classid 1:10", \
                tcSFQConfig.LEAF_CLASS_1_10_MAXIMUM)
            self.addClassCeil("parent 1:1", "classid 1:11", \
                tcSFQConfig.LEAF_CLASS_1_11_MAXIMUM, \
                tcSFQConfig.LEAF_CLASS_1_11_CEIL)
            self.addSFQ("parent 1:10", "handle 10:")
            self.addSFQ("parent 1:11", "handle 11:")
            return "SFQ strategy is successfully set!"
        except NoInterfaceError as e:
            print "No Interface Error occured!"
            return "Your specified interface was not found! No strategy set!"

    def addRootQdisc(self):
        """
        Add a qdisc to your root interface.
        Default is also set here
        """
        cmd = "tc qdisc add dev %s root handle 1: htb default 11" \
                %(self.interface)
        print cmd
        self.executeCmd(cmd)

    def addClass(self, parent, classid, rate):
        cmd = "tc class add dev %s %s %s htb rate %s" \
                %(self.interface, parent, classid, rate)
        print cmd
        self.executeCmd(cmd)

    def addClassCeil(self, parent, classid, rate, ceil):
        cmd = "tc class add dev %s %s %s htb rate %s ceil %s" \
                %(self.interface, parent, classid, rate, ceil)
        print cmd
        self.executeCmd(cmd)

    def addSFQ(self, parent, handle):
        cmd = "tc qdisc add dev %s %s %s sfq perturb 10" \
                %(self.interface, parent, handle)
        print cmd
        self.executeCmd(cmd)

    def changeBandwidth(self, parent, classid, rate):
        cmd = "tc class change dev %s parent %s classid %s htb rate %s" \
                %(self.interface, parent, classid, rate)
        print cmd
        self.executeCmd(cmd)

    def changeBandwidthCeil(self, parent, classid, rate, ceil):
        cmd = "tc class change dev %s parent %s classid %s htb rate %s \
                ceil %s" \
                %(self.interface, parent, classid, rate, ceil)
        print cmd
        self.executeCmd(cmd)

    def addFilter(self, cmd):
        
        # split command
        splittedCmd = cmd.split()
        dstIP = splittedCmd[2]
        dstPort = splittedCmd[3]
        flowid = splittedCmd[4]
        prio = splittedCmd[5]

        cmd = "tc filter add dev %s protocol ip parent 1: prio %s u32 \
                match ip dst %s/32 match ip dport %s 0xffff flowid %s" \
                %(self.interface, prio, dstIP, dstPort, flowid)
        print cmd
        self.executeCmd(cmd)

    def deleteFilter(self, cmd):

        # split command
        splittedCmd = cmd.split()
        dstIP = splittedCmd[2]
        dstPort = splittedCmd[3]
        flowid = splittedCmd[4]
        prio = splittedCmd[5]

        cmd = "tc filter del dev %s protocol ip parent 1: prio %s u32 \
                match ip dst %s/32 match ip dport %s 0xffff flowid %s" \
                %(self.interface, prio, dstIP, dstPort, flowid)
        print cmd
        self.executeCmd(cmd)

class TcSFQTestBed(Tc):
    """
    TcSFQTestBed: Special strategy class for the testbed. 
    Filter's payload matching is special.
    """
    # Constructor
    def __init__(self):
        Tc.__init__(self)

    def startStrategy(self):
        """
        Start your strategy. Check, if your specified interface from
        your TcSFQConfiguration file is available. Otherwise, this
        class will catch a NoInterfaceError and brief the user.
        """
        try:
            self.clearRoot()
            self.addRootQdisc()
            self.addClass("parent 1:","classid 1:1", \
                tcSFQConfig.CHILD_CLASS_MAXIMUM)
            self.addClass("parent 1:1", "classid 1:10", \
                tcSFQConfig.LEAF_CLASS_1_10_MAXIMUM)
            self.addClassCeil("parent 1:1", "classid 1:11", \
                tcSFQConfig.LEAF_CLASS_1_11_MAXIMUM, \
                tcSFQConfig.LEAF_CLASS_1_11_CEIL)
            self.addSFQ("parent 1:10", "handle 10:")
            self.addSFQ("parent 1:11", "handle 11:")
            self.report()
            return "SFQ strategy is successfully set!"
        except NoInterfaceError as e:
            print "No Interface Error occured!"
            return "Your specified interface was not found! No strategy set!"

    def addRootQdisc(self):
        """
        Add a qdisc to your root interface.
        Default is also set here
        """
        cmd = "tc qdisc add dev %s root handle 1: htb default 11" \
                %(self.interface)
        print cmd
        self.executeCmd(cmd)

    def addClass(self, parent, classid, rate):
        cmd = "tc class add dev %s %s %s htb rate %s" \
                %(self.interface, parent, classid, rate)
        print cmd
        self.executeCmd(cmd)

    def addClassCeil(self, parent, classid, rate, ceil):
        cmd = "tc class add dev %s %s %s htb rate %s ceil %s" \
                %(self.interface, parent, classid, rate, ceil)
        print cmd
        self.executeCmd(cmd)

    def addSFQ(self, parent, handle):
        cmd = "tc qdisc add dev %s %s %s sfq perturb 10" \
                %(self.interface, parent, handle)
        print cmd
        self.executeCmd(cmd)

    def report(self):
        """
        Show all queues on our root qdisc.
        Show the number of sent packets and bytes.
        """

        cmd = "tc -s qdisc ls dev %s" % (self.interface)
        returnSequence1 = self.executeCmd(cmd)
        print cmd
        # cmd = "tc qdisc show dev %s" % (self.interface)
        # returnSequence2 = self.executeCmd(cmd)
        # returnSequence1 += returnSequence2
        # print cmd
        return returnSequence1
    
    def changeBandwidth(self, parent, classid, rate):
        cmd = "tc class change dev %s parent %s classid %s htb rate %s" \
                %(self.interface, parent, classid, rate)
        print cmd
        self.executeCmd(cmd)

    def addFilter(self,cmd):
        """
        Set a filter for a flow.
        To identify the flow, give the dstIP and the dstPort.
        dstIP and dstPort are then converted into hexadecimal.
        """

        # split cmd
        splittedCmd = cmd.split()
        dstIP = splittedCmd[2]
        dstPort = splittedCmd[3]
        flowid = splittedCmd[4]
        prio = splittedCmd[5]

        # convert ip from decimal to hexadecimal presentation.
        ipArray = str(dstIP).split('.')
        dstIPHex = "%.2X%.2X%.2X%.2X" \
                % (int(ipArray[0]),int(ipArray[1]), \
                int(ipArray[2]),int(ipArray[3]))

        # convert port from decimal to hexadecimal presentation.
        dstPortHex = "%.4X" % (int(dstPort))
        
        # create the tc filter command with given priority.
        # match on IP adress at byte 48 from the start of the
        # packet's IP header.
        # match on Port at byte 54 from the start of the 
        # packet's IP header.
        # Move the flow to the given flowid.
        tcHead = "tc filter add dev %s protocol ip parent 1: prio %s u32 " \
                %(self.interface, prio)
        matchIP = "match u32 0x%s 0xffffffff at 48 " \
                %(dstIPHex)
        matchPort = "match u16 0x%s 0xffff at 54 " \
                %(dstPortHex)
        flowId = "flowid %s" %(flowid)
        
        cmd = tcHead + matchIP + matchPort + flowId

        print cmd
        self.executeCmd(cmd)

    def deleteFilter(self, cmd):

        # split command
        splittedCmd = cmd.split()
        dstIP = splittedCmd[2]
        dstPort = splittedCmd[3]
        flowid = splittedCmd[4]
        prio = splittedCmd[5]

        # convert ip from decimal to hexadecimal presentation.
        ipArray = str(dstIP).split('.')
        dstIPHex = "%.2X%.2X%.2X%.2X" \
                % (int(ipArray[0]),int(ipArray[1]), \
                int(ipArray[2]),int(ipArray[3]))

        # convert port from decimal to hexadecimal presentation.
        dstPortHex = "%.4X" % (int(dstPort))
        
        # create the tc filter command with given priority.
        # match on IP adress at byte 48 from the start of the
        # packet's IP header.
        # match on Port at byte 54 from the start of the 
        # packet's IP header.
        # Move the flow to the given flowid.
        tcHead = "tc filter del dev %s protocol ip parent 1: prio %s u32 " \
                %(self.interface, prio)
        matchIP = "match u32 0x%s 0xffffffff at 48 " \
                %(dstIPHex)
        matchPort = "match u16 0x%s 0xffff at 54 " \
                %(dstPortHex)
        flowId = "flowid %s" %(flowid)
        
        cmd = tcHead + matchIP + matchPort + flowId

        print cmd
        self.executeCmd(cmd)
    
# main for testing ...
if __name__ == "__main__":
    tcSFQ = TcSFQ()
    tcSFQ.clearRoot()
    tcSFQ.addRootQdisc()
    tcSFQ.addClass("parent 1:","classid 1:1",tcSFQConfig.CHILD_CLASS_MAXIMUM)
    tcSFQ.addClass("parent 1:1", "classid 1:10", \
            tcSFQConfig.LEAF_CLASS_1_10_MAXIMUM)
    tcSFQ.addClassCeil("parent 1:1", "classid 1:11", \
            tcSFQConfig.LEAF_CLASS_1_11_MAXIMUM, \
            tcSFQConfig.LEAF_CLASS_1_11_CEIL)
    tcSFQ.addSFQ("parent 1:10", "handle 10:")
    tcSFQ.addSFQ("parent 1:11", "handle 11:")
    tcSFQ.changeClass("1:1","1:10","500kbit")
