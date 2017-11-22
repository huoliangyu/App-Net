#!/usr/bin/python

# import
import time
import signal
import re
import sys
import trashCONFIG
import tcConfig

# class import
from network_components import ThreadedTCPServer, TCPServerRequestHandlerStream
from tcSFQ import TcSFQ, TcSFQTestBed
from tcPRIO import TcPRIO, TcPRIO2
from tcPRIOHTB import TcPRIOHTB
from tcPRIOCeil import TcPRIOCeil
from tcTHROTTLING import TcTHROTTLING
# from tcHTB import TcHTB
from threading import Thread

class TraSh:
    def __init__(self):
        # Create ThreadedTCPServer and start server_thread
        self.server = ThreadedTCPServer("", int(trashCONFIG.PORT), \
                TCPServerRequestHandlerStream, self)
            
        self.server_thread = Thread(target=self.server.serve_forever, \
                name="TraShTCPServer")
        self.server_thread.setDaemon(True)
        self.server_thread.start()
        self.running = True
        self.setRegexPattern()
        self.strategy = None

    def shutdown(self):
        """ Shutdown server """
        print "trash: shutdown() called!"
        if self.server != None:
            print "trash: Shutting server down!"
            self.server.socket.close()
            self.server.shutdown()
        print "trash: Serverthread stopped!"
        # Set running to false quits trash
        self.running = False

    def printStrategies(self, splittedCmd):
        """
        Print all available strategies.
        """
        if splittedCmd[1] == "all":
            strategies = "All available strategies:" + "\n"
            for s in tcConfig.STRATEGIES:
                strategies += s
                strategies += "\n"
            return strategies

    def startCommand(self, splittedCmd):
        """
        Start trash either in a normal network or in your
        testbed.
        """
        # Start trash in a normal network.
        if splittedCmd[1] == "SFQ":
            self.strategy = TcSFQ()
            self.strategyName = "SFQ"
            successful = self.strategy.startStrategy()
            return successful
        # Start trash in our testbed.
        # implements the normal sfq
        elif splittedCmd[1] == "SFQ_tb":
            print "Strategy SFQ for TestBed set!"
            self.strategy = TcSFQTestBed()
            self.strategy.startStrategy()
            self.strategyName = "SFQ_tb"
            return "Strategy is SFQ"
        # implements a prio tree with sfq on its deepest layer.
        elif splittedCmd[1] == "PRIO_SFQ_tb":
            print "Strategy PRIO for TestBed set!"
            # set SFQ option to true
            self.strategy = TcPRIO(True)
            self.strategy.startStrategy()
            self.strategyName = "PRIO_SFQ_tb"
            return "Strategy is PRIO with SFQ in testbed"
        # implements a prio tree with fifo on its deepest layer.
        elif splittedCmd[1] == "PRIO_alt_FIFO_tb":
            print "Strategy PRIO for TestBed set!"
            self.strategy = TcPRIO(False)
            self.strategy.startStrategy()
            self.strategyName = "PRIO_FIFO_tb"
            return "Strategy is PRIO FIFO"
        # implement a prio tree with a various amount of priorities.
        elif splittedCmd[1] == "PRIO_FIFO_tb":
            print "Strategy PRIO2 for TestBed set!"
            self.strategy = TcPRIO2(False)
            self.strategy.startStrategy()
            self.strategyName = "PRIO2_FIFO_tb"
            return "Strategy is PRIO2 FIFO"
        # -----------------------------------------------------
        # --- implement PRIO with FIFO and ceil for tb
        # -----------------------------------------------------
        elif splittedCmd[1] == "PRIO_FIFO_ceil_tb":
            print "Strategy PRIO with FIFO and ceil for TestBed set!"
            self.strategy = TcPRIOCeil(False)
            self.strategy.burst = False
            self.strategy.startStrategy()
            self.strategyName = "PRIO_FIFO_ceil_tb"
            return "Strategy is PRIO FIFO with CEIL rate"
        # -----------------------------------------------------
        # --- implement PRIO with FIFO, ceil, burst, and tb
        # -----------------------------------------------------
        elif splittedCmd[1] == "PRIO_FIFO_ceil_burst_tb":
            print "Strategy PRIO with FIFO, ceil, and burst for TestBed set!"
            self.strategy = TcPRIOCeil(False)
            # set a further parameter for bursts
            self.strategy.burst = True
            self.strategy.startStrategy()
            self.strategyName = "PRIO_FIFO_ceil_burst_tb"
            return "Strategy is PRIO FIFO ceil and burst!"
        # ----------------------------------------------------------
        # Strategy THROTTLING
        # ----------------------------------------------------------
        elif splittedCmd[1] == "THROTTLING":
            print "Strategy is THROTTLING!"
            self.strategy = TcTHROTTLING()
            self.strategy.startStrategy()
            self.strategyName = "THROTTLING"
            return "Strategy is THROTTLING"
        # ----------------------------------------------------------
        # Strategy PRIO_HTB: min_bandwith with priorities
        # ----------------------------------------------------------
        elif splittedCmd[1] == "PRIO_HTB":
            print "Strategy is PRIO_HTB!"
            self.strategy = TcPRIOHTB()
            self.strategy.startStrategy()
            self.strategyName = self.strategy.getStrategyName()
            return "Strategy is PRIO_HTB"
        else:
            print "Unknown strategy! Not implemented yet!"
            return "Unknown strategy."
            
    def printCommands(self):
        """
        Print all available commands.
        """
        commandString = "-------- PRINT help -------- \n"
        commandString += "List all \n"
        commandString += "Start STRATEGY_NAME \n"
        commandString += "StopTrash \n"
        commandString += "Cmd \n"
        commandString += "Report (Filter|Class|All|Qdisc)( -p| -s| -d) \n"
        commandString += "-------- PRINT help --------"
        return commandString

    def cmdCommand(self, splittedCmd,  cmd):
        """
        Decode the received command.
        """
        if self.strategyName == "THROTTLING":
            print "[trash] executing a THROTTLING command!"
            return self.strategy.doYourThing(cmd)
        else:
            if splittedCmd[1].lower() == "changebandwidth": \
            # change bandwidth: increase or decrease
            # Change bandwidth of classid 1:1 to 300 kbit
            # Example: Cmd. 1: 1:1 300kbit
            # splittedCmd[0]: Cmd.
            # splittedCmd[1]: ChangeBandwidth.
            # splittedCmd[2]: 1:
            # splittedCmd[3]: 1:1
            # splittedCmd[4]: 300kbit
                print "Changing Class " + splittedCmd[3]  + " bandwidth."
                self.strategy.changeBandwidth(splittedCmd[2], \
                                                        splittedCmd[3], \
                                                        splittedCmd[4])
                return "Changing Class Bandwidth:"
            elif splittedCmd[1].lower() == "changebandwidthceil":
                print "Changing Class " + splittedCmd[3] + " bandwidth \
                and ceil"
                self.strategy.changeBandwidthCeil(splittedCmd[2], \
                                                                  splittedCmd[3], \
                                                                  splittedCmd[4], \
                                                                  splittedCmd[5])
            elif splittedCmd[1].lower() == "addfilter": \
            # add flow to a class
            # add IP 172.16.0.2 Port 1234 to flowid 1:10 with prio 1
            # Example: Cmd. AddFilter. 172.16.0.2 1234 1:10 1 (tcSFQ)
            # Example: Cmd. AddFilter. GW1. 172.16.0.2 1234 1:10 1 (tcPRIO)
            # splittedCmd: splittedCmd[1] splittedCmd[2] ...
                self.strategy.addFilter(splittedCmd)
                return "Add filter expression:"
            elif splittedCmd[1].lower() == "deletefilter": \
            # delete flow from a class
            # delete IP 172.16.0.2 Port 1234 from flowid 1:10
            # Example: Cmd. DeleteFilter. 172.16.0.2 1234 1:10 1
            #   (tcSFQ)
            # Example: Cmd. DeleteFilter. GW1. 172.16.0.2 1234 1:10 1
            #   (tcPRIO)
            # See AddFilter for command syntax.
                self.strategy.deleteFilter(splittedCmd)
                return "Delete filter from queue"

	    elif splittedCmd[1].lower() == "changerateandceilgwclass" : 
		self.strategy.changeRateandCeilGWClass(splittedCmd[2],splittedCmd[3])
		return "Changing rate and ceil for current strategy"

            else :
                return "Unknown command: " + cmd

    def setRegexPattern(self):
        """
        Set all necessary decoder for the commands
        """
        self.helpCommands = re.compile(r'help',  re.I)
        self.listStrategy = re.compile(r'List all', re.I)
        self.startPattern = re.compile(r'Start (\w+)', re.I)
        self.stopPattern = re.compile(r'StopTraSh', re.I)
        self.cmdPattern = re.compile(r'Cmd', re.I)
        self.clearPattern = re.compile(r'Clear', re.I)
        self.reportPattern = re.compile(r'Report (Filter|Class|All|Qdisc)( -p| -s| -d)?',re.I)
    
    def executeCmd(self, cmd):
        """ 
        Execute the cmds called by the network components.
        This method calls startCmd and cmdommand.
        return: return a message you want to send to the client.
            If no return message is given the return message will
            be None.
        FirstCommand    Second Command  Arguments
        StopTraSh
        Start SFQ
        StartTestBed SFQ/PRIO
        Cmd ChangeBandwidth/ChangeBandwidthCeil/AddFilter/DeleteFilter \
                Arguments
        Clear
        Report
        """

        matchHelp = self.helpCommands.match(cmd)
        matchList = self.listStrategy.match(cmd)
        matchCmd = self.cmdPattern.match(cmd)
        matchStart = self.startPattern.match(cmd)
        matchStop = self.stopPattern.match(cmd)
        matchClear = self.clearPattern.match(cmd)
        matchReport = self.reportPattern.match(cmd)
        
        if matchHelp:
            return self.printCommands()

        if matchList:
            splittedCmd = cmd.split()
            return self.printStrategies(splittedCmd)

        if matchStart:
            splittedCmd = cmd.split()
            return self.startCommand(splittedCmd)
        elif matchStop:
            splittedCmd = cmd.split()
            print "Quit command!"
            self.shutdown()
            return "Shutdown"
        
        if self.strategy is not None :
            if matchCmd:
                splittedCmd = cmd.split()
                return self.cmdCommand(splittedCmd,  cmd)
            elif matchClear:
                splittedCmd = cmd.split()
                self.strategy.clearRoot()
                statement = self.strategy.report(['report','qdisc'])
                return "Statement: " + statement
            elif matchReport:
                splittedCmd = cmd.split()
                statement = self.strategy.report(splittedCmd)
                return "Statement: " + statement + " end of statement."
            else :
                return "Command not known!"
        else :
            return "No strategy set. First, set a strategy!"
            
def signal_handler(signal, frame):
    """
    Set a new signal handler for Ctrl+C.
    """
    print 'signal_handler(): You pressed Ctrl+C'
    sys.exit('Go HOME!')

def handler(signum, frame):
    print 'handler(): Signal handler called with signal', signum
    raise IOError("Could not correctly end trash!")

def main():
    # We install an interrupt handler in order to catch
    # Ctrl-C
    signal.signal(signal.SIGINT, signal_handler)
    
    trash = TraSh()

    print "main(): Program started..."
    try:
        while trash.running:
            # signal.alarm(10)
            time.sleep(1)
            #if trash.running:
                #Thread.sleep(10)
                #trash.server_thread.join(10)
    except KeyboardInterrupt:
        print "main(): try to shutdown server"
        if trash.running:
            trash.shutdown()
            print "main(): server shutdowned"
        # signal.alarm(0)

    if not trash.running:
        trash.shutdown()
        print "main(): server closed!"

    #while trash.running:
        # signal.alarm(10)
        #try:
        #    if trash.running:
        #        trash.server_thread.join(10)
        #except KeyboardInterrupt:
        #    print "main(): try to shutdown server"
        #    trash.shutdown()
        #    print "main(): server shutdowned"
        # signal.alarm(0)

# main ...
if __name__ == "__main__":
    # start the main function here
    main()
