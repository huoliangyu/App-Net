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

# with tcPRIO2
# prio qdisc 111:, 112:, 113:, 114:, 115:, 116:, ... AMOUNT_PRIOS;
# prio qdisc 121:, 122:, 123:, 124:, 125:, 116:, ... AMOUNT_PRIOS;
# prio qdisc 131:, 132:, 133:, 134:, 135:, 116:, ... AMOUNT_PRIOS;

# Amount of available priorities
AMOUNT_PRIOS = 2

# PRIOMAP
GW1_PRIOMAP = "1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1"
GW_PRIOMAP = [GW1_PRIOMAP]

# gateways
GW = {"GW1" : "11:" 
    }

# gateways belong to a class
GW_CLASS = {"GW1_CLASS" : "1:1"
        }

# gateways IP
GW_IPs = {"GW1_IP" : "132.187.12.97",
        }

# bandwidth of gateways
GW1_bandwidth = "3000kbit"
GW1_ceil = "3000kbit"

#PFIFO_LIMIT = [1000,1000,1000,1000,1000,1000]; 
PFIFO_LIMIT = [50,50]; # SVC is UDP, set queue length to 50 
#PFIFO_LIMIT = [20,200,200,200,20,20]; # sigcomm 
BURST = "2Kb"


# for all gateways map priority to flowid
GW_PRIORITY = {"GW1_PRIORITY_1" : "flowid 11:1",
        "GW1_PRIORITY_2" : "flowid 11:2",
        }
