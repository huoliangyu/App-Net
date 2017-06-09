# App-Net

We provide a measurment framework for testbed-driven comparison of Application-Network-Interaction (App-Net) approaches. This repository contains the source coude for Application-Network Interaction building blocks, as discussed in this [paper](https://github.com/ldecicco/tapas). 

# Prerequisites
All our machines in the testbed run Ubuntu 14.04. 
For prerequisites concerning the applied Tapas player, please see the according [repository]( http://ieeexplore.ieee.org/abstract/document/7810252/). 

# Testbed Deployment
The provided entities are deployed within our [testbed](https://github.com/lsinfo3/App-Net/blob/master/BACKGROUND.md) as follows:
![alt_text](https://github.com/lsinfo3/App-Net/blob/master/illustrations/deployment.PNG)

# Measurement Setup
### Host1
To start the tapas instances, message broker, and policy manager, run the startExperiments.sh script. 
The otption -m indicates the mechanism which shall be applied (spm | qoeff | nade | baseline).
The option -b indicates the bandwidth pattern (static | alternating | sawtooth). 
The possibility to identify an experiment is given by the flag -i. In our deployment, the script is executed on Host1. 
```
$ bash startExperiment.sh -m qoeff -b static -i exp_1
```
### Host2
The startExperiment.sh script also starts the message broker on Host2. 
If, as in our case, the message broker is located on another machine, it must be ensured that it can receive commands from the machine executing startExperiment.sh. In our deployment, we realized this be using netcat. To make the machine hosting the message broker constantly listening, please run the beReady.sh script on the respective machine. 
```
$ bash beReady.sh 
```

### Host3
Host 3 acts as a router. 
On this machines, several tasks are performed. 
* We use the tool TraSh for traffic shaping to limit the bandwidth and simulate a bottleneck link
* TraSh is also used for all network control actions, e.g. bandwdith reservation, flow prioritization
* Network monitoring is located on this host
* The Get Request Fetcher (GRF) is used to detect browsing events (only relevant for multi-application scenarios)
To start an experiment, please run the script startExperiments_router.sh. First of all, it limits the bandwidth. The flag -p denotes the pattern (static, alternating, sawtooth). The flags -h and -l indicate the bandwidth limits. If static bandwidth should be applied, please use the same values for -h and -l. Furthermore, this script starts the respective network monitoring and network control. Please specify the applied mechanism by the -m flag.  

