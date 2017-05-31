# App-Net

We provide a measurment framework for testbed-driven comparison of Application-Network-Interaction (App-Net) approaches. This repository contains the source coude for Application-Network Interaction building blocks, as discussed in this [paper](https://github.com/ldecicco/tapas). 

# Prerequisites
All our machines in the testbed run Ubuntu 14.04. 
For prerequisites concerning the applied Tapas player, please see the according [repository]( http://ieeexplore.ieee.org/abstract/document/7810252/). 

# Testbed Deployment
The provided entities are deployed within our [testbed](https://github.com/lsinfo3/App-Net/blob/master/BACKGROUND.md) as follows:
![alt_text](https://github.com/lsinfo3/App-Net/blob/master/illustrations/deployment.PNG)

# Measurement Setup
To start the tapas instances, message broker, and policy manager, run the startExperiments.sh script. 
The otption -m indicates the mechanism which shall be applied (spm | qoeff | nade | baseline).
The option -b indicates the bandwidth pattern (static | alternating | sawtooth). 
The possibility to identify an experiment is given by the flag -i. 
```
$ bash startExperiment.sh -m qoeff -b static -i exp_1
```



