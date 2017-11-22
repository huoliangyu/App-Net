#!/usr/bin/python

# egress interface
IF = "enp0s31f6"
#hostIP = "192.168.1.5"
#dstIP = "172.16.0.2"
srcPort = "33141"
dstPort = "33141"
U32 = "tc filter add dev %s protocol ip parent 1:0 prio 1 u32"

ADD_QDISC = "tc qdisc add dev %s root handle 1: htb default 20"
ADD_CLASS = "tc class add dev %s parent 1: classid 1:1 htb rate %s"
ADD_CLASS2 = "tc class add dev %s %s %s htb rate %s"
CHANGE_CLASS = "tc class change dev %s parent 1: classid 1:1 htb rate %s"

REPORT = {
    "filter" : "tc %s filter show dev %s",
    "class" : "tc %s class show dev %s",
    "qdisc" : "tc %s qdisc show dev %s"
        }

STRATEGIES = ["SFQ", \
        "SFQ_tb", \
        "PRIO_SFQ_tb", \
        "PRIO_HTB", \
        "PRIO_FIFO_tb", \
        "PRIO2_FIFO_tb", \
        "PRIO_FIFO_ceil_tb", \
        "PRIO2_FIFO_tb", \
        "PRIO_FIFO_ceil_tb", \
        "PRIO_FIFO_ceil_burst_tb", \
        "THROTTLING"]

if __name__=="__main__":
    strategies = "All available strategies:" + "\n"
    for s in STRATEGIES:
        strategies += s
        strategies += "\n"

    # I love python :D
    print strategies[:-1]

    if "THROTTLING" in STRATEGIES:
        print "HALLO THROTTLING"
         
