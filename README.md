# App-Net

Measurment framework for testbed-driven comparison of Application-Network-Interaction (App-Net). This repository contains the source coude for Application-Network Interaction building blocks, as discussed in this [paper]( http://ieeexplore.ieee.org/abstract/document/7810252/)

# Key building blocks: App-Net
The key building blocks for App-Net are Application Monitoring (AM), Network Monitoring (NM), Application Control (AC), Network Control (NC), and a Policy Manager (PM), which decides about control actions based on monitoring information. The message broker depicted below facilitates the interaction between the involved entities. 
Information from AM (e.g. buffer filling level, current video quality, device properties) and NM (e.g. current throughput) are sent to the message broker. The message broker is responsible for forwarding information where it is needed, hence, the monitoring information is communicated to the PM. The PM runs algorithms to decide about appropriate control actions. This information is sent to the PM, which forwards network control instructions to NC, and application control instructions to AC, respectively. 

![alt text](https://github.com/lsinfo3/App-Net/blob/master/illustrations/message_broker.png)

# Testbed
We deployed the entities within a physical testbed, as illustrated below. It consists of a media server, which stores the Big Buck Bunny video in several resolutions and bitrate encodings to support adaptive streaming (HAS).
A second machine acts as a router and provides functionalities for rate limiting, configurations of queues with fixed bandwidth or differente priorities, and regular probing of throughput. 
The video clients, which use the [TAPAS](https://github.com/ldecicco/tapas) DASH player, are running on another machine, which also runs the Policy Manager. 
Finally, one machine runs the message broker, which is based on ZeroMQ (http://zeromq.org/).

![alt text](https://github.com/lsinfo3/App-Net/blob/master/illustrations/testbed.PNG)

# Implemented mechanisms 
![alt text](https://github.com/lsinfo3/App-Net/blob/master/illustrations/mechanisms.PNG)
