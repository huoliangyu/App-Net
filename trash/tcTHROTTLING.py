import tcTHROTTLINGConfig
from tcTHROTTLINGConfig import GW

from tc import Tc
from tc import NoInterfaceError
from collections import deque
from flow import Flow
import re

class TcTHROTTLING(Tc):
    """
    Class representing the throttling approach.
    Creating classes for each application. This allows direct shaping
    of the bandwidth
    """
    def __init__(self):
        Tc.__init__(self)
        self.name = "THROTTLING"
        
        queuesize = tcTHROTTLINGConfig.YouTube_QueueSize
        self.availableYoutubeClasses = {"GW1" : [],  \
                "GW2" : [],  "GW3" : []}
        
        self.availableAppClasses = {"GW1": [],  \
                "GW2" : [],  "GW3" : []}
                
                
        self.youtubeDefaultPriority = 3
        self.appDefaultPriority = 5
        self.prioritizedApps = {"GW1" : None,  "GW2" : None,  "GW3" : None}
        self.prioritizedAppClasses = {"GW1" : None,  "GW2" : None,  "GW3" : None}

        self.youtubeStart = 500
        self.appStart = 800
        
        self.flowMapping = dict()
	self.currentRate = dict()        

    def getStrategyName(self):
        return self.name
        
    def addRootQdisc(self):
        """
        Add a qdisc to your root interface.
        Default is also set here
        """
        print "[TcTHROTTLING] Add the root qdisc!"
        cmd = "tc qdisc add dev %s root handle 1: htb" \
                %(self.interface)
        self.executeCmd(cmd)
     
    def startStrategy(self):
        """
        Start the throttling strategy. Read the throttling config!
        """
        print "[TcTHROTTLING] Setting throttling strategy."
        try:
            # clear the root
            self.clearRoot()
            
            # set a htb queue on the root
            self.addRootQdisc()
            
            # set one class with limited bandwidth for each gateway
            for i in range(1, len(tcTHROTTLINGConfig.GW) + 1):
                
                # get all attributes
                classid = tcTHROTTLINGConfig.GW["GW%s" %i]
                rate = tcTHROTTLINGConfig.GW_bandwidth["GW%s" %i]
                ceil = rate
                ip = tcTHROTTLINGConfig.GW_IPs["GW%s" %i]
                amountYoutubeClass = tcTHROTTLINGConfig.YouTube_QueueSize
                amountAppClass = tcTHROTTLINGConfig.App_QueueSize
                gateway = "GW%s" %i
                self.addGWClass(classid,  rate,  ceil)
                
                # install classes for each gateway
                # (first version starts with only one class for youtube and a default class)
                # second versoin now starts with one class for youtube, one for apps and a default class
                # for all other traffic
                burst = tcTHROTTLINGConfig.burst
                self.addGWClassDefaultPRIO(classid,  "1:%s00" %i, tcTHROTTLINGConfig.minBW,  rate, burst,   "1");
                for j in range(0,  amountYoutubeClass):
                    classNumber = self.youtubeStart + int(j)
                    self.addGWClassPRIO(classid,  "1:%s%s" %(i,  classNumber), \
                                        tcTHROTTLINGConfig.minBW,  \
                                        rate,  \
                                        str(self.youtubeDefaultPriority));

                # App class getting prioritized
                self.prioritizedAppClasses["GW%s" %i] = "%s%s" %(i, self.appStart + int(0))
               # self.addGWClassPRIO(classid, "1:%s%s" %(i, self.appStart + int(0)), \
                #        tcTHROTTLINGConfig.minBW, \
                 #       rate, \
                  #      str(self.appDefaultPriority - 1));

                for j in range(1,  amountAppClass):
                    classNumber = self.appStart + int(j)
                    self.addGWClassPRIO(classid,  "1:%s%s" %(i,  classNumber), \
                                        tcTHROTTLINGConfig.minBW,  \
                                        tcTHROTTLINGConfig.minBW,  \
                                        str(self.appDefaultPriority));
                    
                #self.addRootFilter("1:0",  "1",  ip,  classid)
                self.addClassFilterDefault("1:0",  "8",  ip,  "1:%s00" %i)
                
                # fill youtube queue
                for i in range(0,  amountYoutubeClass):
                    self.availableYoutubeClasses[gateway].append(i)
                    
                for i in range(1,  amountAppClass):
                    self.availableAppClasses[gateway].append(i)
            self.printInformation()
        except NoInterfaceError as e:
            print "No Interface Error occured!"
            return "Your specified interface was not found! No strategy set!"

    def printInformation(self):
        for i in range(1,  len(self.prioritizedAppClasses) + 1):
            number = self.prioritizedAppClasses["GW%s" %i]
            print "Prioritized App Class GW%s: " %(i) + str(number) 

    def addGWClass(self,  classid,  rate,  ceil):
        print "[TcTHROTTLING] Add class."
        burst = tcTHROTTLINGConfig.burst
        cmd = "tc class add dev %s \
        parent 1: \
        classid %s \
        htb rate %s \
        burst %s \
        ceil %s" % (self.interface, classid, rate, burst, ceil)
        print "[TcTHROTTLING] Command: " + cmd
        self.executeCmd(cmd)
        
    def addGWClassDefaultPRIO(self,  parent,  classid,  rate,  ceil, burst, priority):
        print "[TcTHROTTLING] Add class " + str(classid) +\
        " with priority" + str(priority)
        burst = tcTHROTTLINGConfig.burst
        cmd = "tc class add dev %s \
        parent %s \
        classid %s \
        htb rate %s \
        ceil %s \
        burst %s \
        prio %s" % (self.interface,  parent,  classid,  rate,  ceil, burst, priority)
        self.executeCmd(cmd)
    
    def addGWClassPRIO(self,  parent,  classid,  rate,  ceil,  priority):
        print "[TcTHROTTLING] Add class " + str(classid) +\
        " with priority" + str(priority)
        cmd = "tc class add dev %s \
        parent %s \
        classid %s \
        htb rate %s \
        ceil %s \
        prio %s" % (self.interface,  parent,  classid,  rate,  ceil, priority)
        self.executeCmd(cmd)
        
    def addRootFilter(self,parent,  prio,  dstIP,  flowid):
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
        
    def doYourThing(self,  cmd):
        """
        Decode the command and continue with
        adding youtube flow,
        removing youtube flow,
        changing bandwidth of a class,
        changing bandwidth and ceil of a class,
        or printing help.
        """
        splittedCmd = cmd.split()
        if splittedCmd[0].lower() == "cmd":
            print "[TcTHROTTLING] command execution was called."
            if splittedCmd[1].lower() == "addyoutube":
                print "[TcTHROTTLING] Add YouTube Flow. Check Syntax."
                if len(splittedCmd) != 6:
                    return "[TcTHROTTLING] Not enough arguments!"
                else:
                    return self.addYoutubeFlow(splittedCmd[2], \
                                               splittedCmd[3], \
                                               splittedCmd[4], \
                                               splittedCmd[5].upper())
                                           
            elif splittedCmd[1].lower() == "delyoutube":
                print "[TcTHROTTLING] Delete YouTube Flow. Check Syntax."
                if len(splittedCmd) != 6:
                    return "[TcTHROTTLING] Not enough arguments!"
                else:
                    return self.delYoutubeFlow(splittedCmd[2], \
                                               splittedCmd[3], \
                                               splittedCmd[4], \
                                               splittedCmd[5].upper())
                                              
            elif splittedCmd[1].lower() == "changebw":
                print "[TcTHROTTLING] Change Class Bandwidth"
                return self.changeClassBandwidth(splittedCmd[2], \
                                                 splittedCmd[3],  "10")
                                                 
            elif splittedCmd[1].lower() == "changebwandceil":
                print "NOT IMPLEMENTED! [TcTHROTTLING] Change Class Bandwidth and Ceil."
                return "[TcTHROTTLING] Change Class Bandwidth and Ceil."
                
            elif splittedCmd[1].lower() == "help":
                print "[TcTHROTTLING] Print Help."
                return "[TcTHROTTLING] Print Help."
                
            elif splittedCmd[1].lower() == "changedefbw":
                print "[TcTHROTTLING] Change default class bandwidth!"
                gw = splittedCmd[2].lower()
                bw = splittedCmd[3].lower()
                return self.changeDefaultClassBandwidth(gw,  bw)

            elif splittedCmd[1].lower() == "changedefbwandceil":
                print "[TcTHROTTLING] Change default class bandwidth!"
                gw = splittedCmd[2].lower()
                bw = splittedCmd[3].lower()
		old_bw = splittedCmd[4].lower()
                return self.changeDefaultClassBandwidthAndCeil(gw,  bw, old_bw)




                
            elif splittedCmd[1].lower() == "addapp":
                print "[TcTHROTTLING] Add a app flow! Check Syntax."
                if len(splittedCmd) != 6:
                    return "[TcTHROTTLING] Not enough arguments!"
                else:
                    return self.addAppFlow(splittedCmd[2], \
                                                splittedCmd[3], \
                                                splittedCmd[4], \
                                                splittedCmd[5].upper())
                
            elif splittedCmd[1].lower() == "delapp":
                print "[TcTHROTTLING] Delete a app flow! Check Syntax."
                if len(splittedCmd) != 6:
                    return "[TcTHROTTLING] Not enough arguments!"
                else:
                    return self.delAppFlow(splittedCmd[2], \
                                                splittedCmd[3], \
                                                splittedCmd[4], \
                                                splittedCmd[5].upper())

            elif splittedCmd[1].lower() == "prioapp":
                print "[TcTHROTTLING] Prioritize a app flow! Check Syntax."
                if len(splittedCmd) != 3:
                    return "[TcTHROTTLING] Not enough arguments!"
                else:
                    return self.prioritizeApp(splittedCmd[2])
                    
            elif splittedCmd[1].lower() == "changeceil":
                print "[TcTHROTTLING] Change ceil of a app flow!"
                if len(splittedCmd) != 4:
                    return "[TcTHROTTLING] Not enough arguments!"
                else:
                    return self.changeFlowCeil(splittedCmd[2], \
                                               splittedCmd[3])
                
            else:
                print "[TcTHROTTLING] Command is not known!"
                return "[TcTHROTTLING] Command is not known!"
                
    def changeDefaultClassBandwidth(self,  gw,  bw):
        """
        Change bw of default class.
        """
        if gw == "gw1":
            flowClass = "1:100"
            ceil = tcTHROTTLINGConfig.GW_bandwidth["GW1"]
            parent = "1:1"
        elif gw == "gw2":
            flowClass = "1:200"
            ceil = tcTHROTTLINGConfig.GW_bandwidth["GW2"]
            parent = "1:2"
        elif gw == "gw3":
            flowClass = "1:300"
            ceil = tcTHROTTLINGConfig.GW_bandwidth["GW3"]
            parent = "1:3"
        else:
            return "[TcTHROTTLING] Unknown gateway!"        
        rate = bw
        burst = tcTHROTTLINGConfig.burst
        cmd = "tc class change dev %s parent %s classid %s htb rate %s ceil %s burst %s prio %s" \
        % (self.interface, parent,  flowClass,  rate,  ceil, burst,   "1")
        print cmd
        self.executeCmd(cmd)
        return "[TcTHROTTLING] Bandwidth of default GW1's default class changed."

    def changeDefaultClassBandwidthAndCeil(self,  gw,  bw, old_bw):
        """
        Change bw and ceil of default class.
        """
        if gw == "gw1":
            flowClass = "1:100"
            parent = "1:1"
        elif gw == "gw2":
            flowClass = "1:200"
            parent = "1:2"
        elif gw == "gw3":
            flowClass = "1:300"
            parent = "1:3"
        else:
            return "[TcTHROTTLING] Unknown gateway!"        
        rate = bw
        burst = tcTHROTTLINGConfig.burst
        cmd = "tc class change dev %s parent %s classid %s htb rate %s ceil %s burst %s prio %s" \
        % (self.interface, parent,  flowClass,  bw,  bw, burst,  "1")
        print cmd
        self.executeCmd(cmd)
	
	# sudo tc class change dev eth1 classid 1:1 htb rate 500kbit ceil 600kbit burst 1223 prio 1
	cmd = "tc class change dev %s classid %s htb rate %s ceil %s burst %s prio %s" \
        % (self.interface, "1:1",  bw,  bw, burst, "1")
        print cmd
        self.executeCmd(cmd)
	

	print "+++++++++++++++++++++++++"
	print tcTHROTTLINGConfig.GW_bandwidth[gw.upper()]
	tcTHROTTLINGConfig.GW_bandwidth[gw.upper()] = bw
	print tcTHROTTLINGConfig.GW_bandwidth[gw.upper()]
	print "+++++++++++++++++++++++++"

	# adjust mappings Susi
	for flowid in self.currentRate.keys():
		rate = float(re.sub(r'[^0-9\.]','',self.currentRate[flowid]))
		old_bw = float(re.sub(r'[^0-9\.]','',str(old_bw)))
		bw = float(re.sub(r'[^0-9\.]','',str(bw)))
		new_rate = (rate/old_bw) * bw
		prio = 10
		self.changeClassBandwidth(flowid,str(new_rate)+'kbit',prio)

	print bw
	print "==============================="
	for flowid in self.currentRate.keys():
		print "%s: %s" % (flowid, self.currentRate[flowid])
	print "==============================="

	        		
        return "[TcTHROTTLING] Bandwidth of default GW1's default class changed."



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

    def addAppFlow(self,  flowID,  ip,  port,  gateway):
        """
        Add a app flow to trash
        """
        flowid = int(flowID)
        flowIP = ip
        flowPort = port
        
	print str(self.flowMapping.keys())
        if int(flowID) in self.flowMapping.keys():
            print "[TcTHROTTLING] Duplicate key entry. FlowID will not be set!"
            return "[TcTHROTTLING] Duplicate key entry. FlowID will not be set!"
        else:
            if gateway == "GW1":
                nextAvailableAppClass = self.availableAppClasses[gateway].pop()
                classNumber = 1000 + self.appStart + int(nextAvailableAppClass)
                
            elif gateway == "GW2":
                nextAvailableAppClass = self.availableAppClasses[gateway].pop()
                classNumber = 2000 + self.appStart + int(nextAvailableAppClass)
                
            elif gateway == "GW3":
                nextAvailableAppClass = self.availableAppClasses[gateway].pop()
                classNumber = 3000 + self.appStart + int(nextAvailableAppClass)
                
            else:
                return "[TcTHROTTLING] Unknown gateway! Cannot prioritize flow!"

            # add filter, class number is the second part of the id of the flow
            # for example 1:2801, then the class number is 2801.
            self.addClassFilter("1:0",  flowIP, flowPort, str(classNumber),   str(self.appDefaultPriority))
            
            filterHandle = self.getFilterNumber(flowPort,  flowIP,  "1:0")
            print "[TcTHROTTLING addApp] Filter handle is " + str(filterHandle[0])

            newFlow = Flow(flowID,  \
                           flowIP,  \
                           flowPort,  \
                           gateway,  \
                           nextAvailableAppClass,  \
                           classNumber,  \
                           self.appDefaultPriority,  \
                           filterHandle[0])

            infoString = "[TcTHROTTLING]\n"
            infoString += "flowid: " + str(flowid) + "\n"
            infoString += "flowIP: " + str(ip) + "\n"
            infoString += "flowPort: " + str(port) + "\n"
            infoString += "nextAvailableAppClass: " + str(newFlow.flowNumber) + "\n"
            print infoString
            
            self.flowMapping[flowid] = newFlow
            parent = tcTHROTTLINGConfig.GW[gateway]
            
            return "[TcTHROTTLING] App flowid successfully set!"

    def addYoutubeFlow(self,  flowID,  ip,  port,  gateway):
        """
        Add a youtube flow to its own class
        """
        flowid = int(flowID)
        flowIP = ip
        flowPort = port
        
        # check if the flowID is still set
        # if true do not set and return
        if int(flowID) in self.flowMapping.keys():
            print "[TcTHROTTLING] Duplicate key entry. FlowID will not be set!"
            return "[TcTHROTTLING] Duplicate key entry. FlowID will not be set!"
        else:
            if gateway == "GW1":
                nextAvailableYouTubeClass = self.availableYoutubeClasses[gateway].pop()
                classNumber = 1000 + self.youtubeStart + int(nextAvailableYouTubeClass)
            
            elif gateway == "GW2":
                nextAvailableYouTubeClass = self.availableYoutubeClasses[gateway].pop()
                classNumber = 2000 + self.youtubeStart + int(nextAvailableYouTubeClass)
            
            elif gateway == "GW3":
                nextAvailableYouTubeClass = self.availableYoutubeClasses[gateway].pop()
                classNumber = 3000 + self.youtubeStart + int(nextAvailableYouTubeClass)
            
            else:
                return "[TcTHROTTLING] Unknown gateway!"
                
                
            # add filter
            self.addClassFilter("1:0",  flowIP, flowPort, str(classNumber), str(self.youtubeDefaultPriority))
            
            filterHandle = self.getFilterNumber(flowPort,  flowIP,  "1:0")
        
            newFlow = Flow(flowID,  \
                           flowIP,  \
                           flowPort,  \
                           gateway,  \
                           nextAvailableYouTubeClass,  \
                           classNumber,  \
                           self.youtubeDefaultPriority,  \
                           filterHandle)

            infoString = "[TcTHROTTLING]\n"
            infoString += "flowid: " + str(flowid) + "\n"
            infoString += "flowIP: " + str(ip) + "\n"
            infoString += "flowPort: " + str(port) + "\n"
            infoString += "flowFilterHandle: " + str(filterHandle) + "\n"
            infoString += "nextAvailableYouTubeClass: " + str(newFlow.flowNumber) + "\n"
            print infoString
            
            self.flowMapping[flowid] = newFlow
            
            return "[TcTHROTTLING] flowid successfully set!"
            
    def changeClassFilter(self,  parent,  dstIP,  dstPort,  classNumber,  prio):
        """
        Change a class filter.
        """
        # convert ip from decimal to hexadecimal representation
        dstIPHex = self.decimalIP2hexadecimalIP(dstIP)

        # conver prot from decimal to hexadecimal representation
        dstPortHex = self.decimalPort2hexadecimalPort(dstPort)
        
        cmdHeader = "tc filter change dev %s parent %s protocol ip prio %s u32 " \
                %(self.interface, parent,  prio)
        #cmdMatchIP = "match u32 0x%s 0xffffffff at 52 " \
        cmdMatchIP = "match u32 0x%s 0xffffffff at 16 " \
                %(dstIPHex)
        #cmdMatchPort = "match u16 0x%s 0xffff at 58 " \
        cmdMatchPort = "match u16 0x%s 0xffff at 21 " \
                %(dstPortHex)
        cmdFlowId = "flowid 1:%s" %(classNumber)
        
        # make cmd and execute
        cmd = cmdHeader + cmdMatchIP + cmdMatchPort + cmdFlowId
        self.executeCmd(cmd)
        
    def addClassFilter(self,  parent,  dstIP,  dstPort,  flowid,  prio):
        """
        Install a class filter.
        """
        
        # convert ip from decimal to hexadecimal representation
        dstIPHex = self.decimalIP2hexadecimalIP(dstIP)

        # conver prot from decimal to hexadecimal representation
        dstPortHex = self.decimalPort2hexadecimalPort(dstPort)
        
        cmdHeader = "tc filter add dev %s parent %s protocol ip prio %s u32 " \
                %(self.interface, parent,  prio)
        #cmdMatchIP = "match u32 0x%s 0xffffffff at 52 " \
        cmdMatchIP = "match u32 0x%s 0xffffffff at 16 " \
                %(dstIPHex)
        #cmdMatchPort = "match u16 0x%s 0xffff at 58 " \
        cmdMatchPort = "match u16 0x%s 0xffff at 21 " \
                %(dstPortHex)
        cmdFlowId = "flowid 1:%s" %(flowid)
        
        # make cmd and execute
        cmd = cmdHeader + cmdMatchIP + cmdMatchPort + cmdFlowId
        print "[TcTHROTTLING] " + cmd
        self.executeCmd(cmd)
        
    def delAppFlow(self,  flowID,  ip,  port,  gateway):
        """
        Remove a app flow for a given flowid
        """
        flowid = int(flowID)
        flowIP = ip
        flowPort = port
        
        # get the class number of this flow
        if int(flowID) in self.flowMapping.keys():
            oldFlow = self.flowMapping[flowid]
            
            # remove this flow form the class map
            del self.flowMapping[flowid]
	    del self.currentRate[flowid]
            
            # add class number to gateway list
            if int(oldFlow.flowClass) == int(self.prioritizedAppClasses[gateway]):
                # remove a prioritized flow. do not add the classnumber of this flow
                # to the list containing the avaible app default classes
                print "[TcTHROTTLING delAppFlow] Remove old flow which was prioritized!"
                self.prioritizedApps[gateway] = None
            else:
                # This flow was not prioritized, so add its flow number to the list
                # containing the available default app classes
                self.availableAppClasses[gateway].append(oldFlow.flowNumber)
            
            infoString = "[TcTHROTTLING]"
            infoString += "flowid: " + str(flowid) + "\n"
            infoString += "flowIP: " + str(ip) + "\n"
            infoString += "flowPort: " + str(port) + "\n"
            infoString += "nextAvailableAppClass: " + str(self.availableAppClasses[gateway][-1]) + "\n"
            print infoString
            
            # delete filter
            # def deleteClassFilter(self,  parent,  dstIP,  dstPort,  flowid,  prio):
            self.removeFilterByHandle(oldFlow.filterHandle,  oldFlow.priority,  "1:0")
           
	    minBw = tcTHROTTLINGConfig.minBW
            self.resetFlowClass(oldFlow.gateway,  oldFlow.flowClass, minBw, minBw,  self.appDefaultPriority)

                                   
            return "[TcTHROTTLING] Flow was successfully removed!"
        else:
            print "[TcTHROTTLING] Key is not known. It will not be removed!"
            return "[TcTHROTTLING] Key is not known. It will not be removed!"
            
    def resetFlowClass(self,  gateway,  flowClass, rate, ceil, prio):
        # get the maximum bandwidth rate
        parent = tcTHROTTLINGConfig.GW[gateway]
        
        # gateways
        gatewayClass = tcTHROTTLINGConfig.GW[gateway]
        
        cmd = "tc class replace dev %s parent %s classid 1:%s htb rate %s ceil %s prio %s" \
        % (self.interface, parent, flowClass, rate,  ceil,  prio)
        report = "[TcTHROTTLING] " + cmd
        print report
        self.executeCmd(cmd)
        return str(report)
        
    def changeFlowClass(self,  flow,  newClassNumber, oldPriority,  newPriority):
        """
        Change the class of a flow.
        """
        print "[TcTHROTTLING changeFlowClass] Changing flow class of flow " + str(flow.id)
        gateway = flow.gateway
        
        # save old filter handle and old priority
        oldFilterHandle = flow.filterHandle
        oldPrio = flow.priority
        
        print "[TcTHROTTLING changeFlowClass] Set a new class filter!"
        # set a new class filter
        self.addClassFilter("1:0",  flow.ip, flow.port, str(newClassNumber),   str(newPriority))
        
        print "[TcTHROTTLING changeFlowClass] Remove old class filter!"
        # remove the old filter
        self.removeFilterByHandle(oldFilterHandle,  oldPriority,  "1:0")
        
        print "[TcTHROTTLING changeFlowClass] Get the new filter handle!"
        # get the new filter handle
        filterHandle = self.getFilterNumber(flow.port,  flow.ip,  "1:0")
        print "[TcTHROTTLING changeFlowClass] New filter handle is " + str(filterHandle[0])
        flow.filterHandle = filterHandle[0]
        
    def changeFlowCeil(self,  flowID, ceil):
        """
        Prioritize a app flow by changing the ceil parameter
        """
        
        # get the new flow
        if int(flowID) in self.flowMapping.keys():
            flow = self.flowMapping[int(flowID)]
        else:
            return "[TcTHROTTLING] Cannot change ceil. Flow is not known."
            
        flowClass = flow.flowClass
        priority = flow.priority
        minBw = tcTHROTTLINGConfig.minBW
        
        cmd = "tc class change dev %s parent %s classid 1:%s htb rate %s ceil %s prio %s" \
        % (self.interface, "1:0", flowClass,  minBw,  ceil,  priority)
        print cmd
        self.executeCmd(cmd)
        
        report = "[TcTHROTTLING changeFlowCeil] Changed flow ceil!"
        print report
        
        return str(report)
            
    def prioritizeApp(self,  flowID):
        """
        Prioritize a app flow by setting the ceil priority
        """
        
        # get the new flow
        if int(flowID) in self.flowMapping.keys():
            newFlow = self.flowMapping[int(flowID)]
        else:
            return "[TcTHROTTLING] Cannot prioritize flow. It is not known!"
        
        # get the gateway of this new flow
        gateway = newFlow.gateway

        # get the max/min bandwidth rate
        maxRate = tcTHROTTLINGConfig.GW_bandwidth[gateway]
        parent = tcTHROTTLINGConfig.GW[gateway]
        ceil = maxRate
        minRate = tcTHROTTLINGConfig.minBW
        
        """
        Decide between two cases. Do we have an old flow which is prioritized, so
        change the priority of this flow first, else prioritize the new flow.
        """
        if self.prioritizedApps[gateway] is not None:
            # Check the flowid. Is it still set?
            oldFlow = self.prioritizedApps[gateway]
            if oldFlow.id == newFlow.id:
                return "[TcTHROTTLING] Flow is already prioritized. OldNumber:"\
                + str(oldFlow.id) +\
                " NewNumber: " + str(newFlow.id) + " Do nothing!"
            else:
                print "[TcTHROTTLING] Resetting old prioritized flow class!"
                if gateway == "GW1":
                    nextAvailableAppClass = self.availableAppClasses[gateway].pop()
                    classNumber = 1000 + self.appStart + int(nextAvailableAppClass)            
                elif gateway == "GW2":
                    nextAvailableAppClass = self.availableAppClasses[gateway].pop()
                    classNumber = 2000 + self.appStart + int(nextAvailableAppClass)
                elif gateway == "GW3":
                    nextAvailableAppClass = self.availableAppClasses[gateway].pop()
                    classNumber = 3000 + self.appStart + int(nextAvailableAppClass)
                
                flowIP = oldFlow.ip
                flowPort = oldFlow.port
                flowClass = oldFlow.flowClass
                oldFlow.flowNumber = nextAvailableAppClass
                
                self.changeFlowClass(oldFlow,  classNumber, str(oldFlow.priority),  str(self.appDefaultPriority))
        
        # gateways
        gatewayClass = tcTHROTTLINGConfig.GW[gateway]
     
        self.availableAppClasses[gateway].append(newFlow.flowNumber)   
        
        # flow classid
        flowClass = newFlow.flowClass
        
        report =  "[TcTHROTTLING] Prioritizing app " \
        + str(flowID) + " corresponding to gateway class " + str(gateway)
        print report
        
        newPriority = self.appDefaultPriority - 1
        newFlow.priority = newPriority
        newFlow.flowNumber = 0

        # set the flow as the actually prioritized flow
        self.prioritizedApps[gateway] = newFlow
        classNumber = self.prioritizedAppClasses [gateway]
        newFlow.flowClass = classNumber
        
        self.changeFlowClass(newFlow,  classNumber, str(self.appDefaultPriority),  str(newPriority))
        
        return str(report)
    
    def delYoutubeFlow(self,  flowID,  ip,  port,  gateway):
        """
        Remove a youtube flow for a given flowid
        """
        flowid = int(flowID)
        flowIP = ip
        flowPort = port
        
        # get the class number of this flow
        if int(flowID) in self.flowMapping.keys():
            oldFlow = self.flowMapping[flowid]
            
            # remove this flow from the class map
            del self.flowMapping[flowid]
            
            # add class number to gateway list
            self.availableYoutubeClasses[gateway].append(oldFlow.flowNumber)
            infoString = "[TcTHROTTLING]"
            infoString += "flowid: " + str(flowid) + "\n"
            infoString += "flowIP: " + str(ip) + "\n"
            infoString += "flowPort: " + str(port) + "\n"
            infoString += "nextAvailableYouTubeClass: " + str(self.availableYoutubeClasses[gateway][-1]) + "\n"
            print infoString
            
            # delete filter
            self.removeFilterByHandle(oldFlow.filterHandle,  oldFlow.priority,  "1:0")
            
            return "[TcTHROTTLING] flowid successfully removed!"
        else:
            print "[TcTHROTTLING] Key is not known. It will not be removed!"
            return "[TcTHROTTLING] Key is not known. It will not be removed!"
        
    def deleteClassFilter(self,  gateway,  dstIP,  dstPort,  flowid,  prio):
        """
        parent = Gateway
        """
        # convert ip from decimal to hexadecimal representation
        dstIPHex = self.decimalIP2hexadecimalIP(dstIP)

        # conver prot from decimal to hexadecimal representation
        dstPortHex = self.decimalPort2hexadecimalPort(dstPort)
        
        gatewayClassid = tcTHROTTLINGConfig.GW[gateway]

        handle = self.getFilterNumber(dstPort, dstIP, "1:0")
        print handle
       
        # make command
        for i in handle:
            print "." + i + "."
            cmdHeader = "tc filter del dev %s parent %s protocol ip prio %s handle %s u32 " \
            %(self.interface, "1:0", prio, i)
            cmd = cmdHeader
            self.executeCmd(cmd)
        
        #cmdHeader = "tc filter del dev %s parent %s protocol ip prio %s u32 " \
        #        %(self.interface, "1:0",  prio)
        #cmdMatchIP = "match u32 0x%s 0xffffffff at 52 " \
        #        %(dstIPHex)
        #cmdMatchPort = "match u16 0x%s 0xffff at 58 " \
        #        %(dstPortHex)
        #cmdFlowId = "flowid " + str(flowid)
        
        # make cmd and execute
        #cmd = cmdHeader + cmdMatchIP + cmdMatchPort + cmdFlowId
        #self.executeCmd(cmd)
        
    def changeClassBandwidth(self,  flowid,  newBandwidth ,  prio):
        """
        Get the class of this flow and shape it!
        """
        # get the flow
        flow = self.flowMapping[int(flowid)]
        
        # get the gateway of this flow
        gateway = flow.gateway
        
        # get the maximum bandwidth rate
        rate = tcTHROTTLINGConfig.GW_bandwidth[gateway]
        parent = tcTHROTTLINGConfig.GW[gateway]
        ceil = rate
        
        # get port and ip
        ip = flow.ip
        port = flow.port
        
        # gateways
        gatewayClass = tcTHROTTLINGConfig.GW[gateway]
        
        # flow classid
        flowClass = flow.flowClass
        
        report =  "[TcTHROTTLING] Changing bandwidth of flow " \
        + str(flowid) + " corresponding to class " + str(gatewayClass)
        print report
        
        cmd = "tc class change dev %s parent %s classid 1:%s htb rate %s ceil %s prio %s" \
        % (self.interface, parent, flowClass,  newBandwidth,  ceil,  prio)
        print cmd
        self.executeCmd(cmd)
	self.currentRate[int(flowid)] = newBandwidth
	print ceil
	print "==============================="
	for flowid in self.currentRate.keys():
		print "%s: %s" % (flowid, self.currentRate[flowid])
	print "==============================="
	return str(report)
