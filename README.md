# Simulation-and-PE
Course projects of Simulation and Performance evaluation in UNITN

A very simple wireless communication system is sketched in Fig. 1. A square area of nor-
malized length 1 is given, with 10 communication nodes n1 . . . n10 distributed uniformly at
random in the area (the red dots). Each node is equipped with an omnidirectional an-
tenna and can transmit to and receive packets from all other nodes within a normalized
communication range r = 0.25.

The transmission speed is fixed and identical for all nodes B = 8 Mbit/s. The propagation
delay is negligible, i.e., it can be approximated to zero. The packet size Sp is a random
variable in bytes, drawn from a distribution fS (s) identical for all nodes. Packet size respect
the most common protocols limits and has a minimum packet size of 32 bytes (typical of
some sensor networks) and a maximum packet size of 8192 bytes (Ethernet “jumbo frames”).
The actual maximum packet size is specified by the parameter n in the dataset. The packet
inter-arrival time Tp is random, drawn from a distribution fT (t) identical for all nodes. One
parameter of fT (t) is not specified and must be used to change the traffic offered by the
stations to the channel, so that the response of the system to a varying load can be studied.
The distributions fS (s), fT (t), the nodes positions (x1 , y1 ) . . . (x10 , y10), and the buffer size
of the transmission queues Cb are assigned to each student similarly to what we have done
for the datasets of the first assignment. Appendix A reports all the possible distributions
that can be assigned in the datasets. Appendix B reports one sample dataset for reference.
The true datasets are in the file students-data.zip; download, unzip it and search for your
data in the file surname.data. If you don’t find it send us and e-mail.
The communication protocol is extremely simple and similar to the continuous time
Aloha protocol:

• All packets are sent in “local broadcast”, i.e., all nodes within the communication
range r from the sender will receive the packet if there are no collisions, but will not
re-transmit them;
• Packets are not acknowledged;
• Two packets that “overlap” in time (also partially) at a receiver will be both lost (for
that specific node), not for the others;
• If one packet is generated at a node and the node is idle (not transmitting or receiving),
it is transmitted immediately;
• If one packet is generated at a node while this node is either transmitting or receiving,
will be enqueued locally at the node for later transmission;
• A node start transmitting if it has a packet in its queue and it is not receiving (or
transmitting) any packet.

