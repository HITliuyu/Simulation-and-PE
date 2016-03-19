#! /usr/bin/python3
import math
import numpy
import heapq


neighbour = {0: [5, 7, 9], 1: [6, 8], 2: [3, 4], 3: [2, 9], 4: [2], 5: [0, 7], 6: [1, 7], 7: [0, 5, 6], 8: [1], 9: [0, 3]}
node_amount = 10

IDLE = 'idle'
TX = 'tx'
RX = 'rx'
BUFFERSIZE = 30
SPEED =8*1024*1024   #transmitted speed
WAITING = 0.0001

DDLTASK = 'ddl_task' #deadline task
ARITASK = 'arrival_task' #arrival task
RETXTASK = 'retransmit_task'

class EventScheduler:
    def __init__(self):
            self.queue = []
            self.time = 0
            self.last = 0

    def schedule_event(self, interval, pktsize, qnum, flag):
            t = self.time + interval
            if t > self.last:
                self.last = t
            heapq.heappush(self.queue, (t, pktsize, qnum, flag))

    def pop_event(self):
            e = heapq.heappop(self.queue)
            self.time = e[0]
            return e[1], e[2] , e[3]

    def elapsed_time(self):
            return self.time

    def last_event_time(self):
            return self.last

    def order(self):
            self.queue = sorted(self.queue, key = lambda event: event[0])


def simu(time, scale = 1):
    ###################################################################
    # initialization of record dict
    ###################################################################

    state = {x : IDLE for x in range(node_amount)}
    customer = {x : 0 for x in range(node_amount)}
    ddl = {x : 0 for x in range(node_amount)}     #record deadlines for each node
    lock = {x : [] for x in range(node_amount)}   #record senders of each node
    bufferedPktSize = {x : [] for x in range(node_amount)}
    receiver = {x:[] for x in range(node_amount)}

    bufferLoss = {x : 0 for x in range(node_amount)}   # lost pkt
    bufferTotal = {x : 0 for x in range(node_amount)} #totally generated pkt

    totalReceivedPkt = {x : 0 for x in range(node_amount)}
    successReceivedPkt = {x : 0 for x in range(node_amount)}
    collisionPkt = {x : 0 for x in range(node_amount)}

    totalSentPkt = {x : 0 for x in range(node_amount)}
    successSentPkt = {x : 0 for x in range(node_amount)}
    collisionSentPkt = {x : 0 for x in range(node_amount)}

    tx_txCollision = {x : 0 for x in range(node_amount)}
	###################################################################
    # initialization of scheduler
    ###################################################################
    sched = EventScheduler()
    for i in range(node_amount):
        sched.schedule_event(numpy.random.rayleigh(scale), numpy.random.binomial(4150,0.662) + 32, i, ARITASK)
    sched.order()

    # filename = "simudata" + str(scale) + ".csv"
    # fp = open(filename, "w")
    # fp.write("time,q0len,q1len\n")

    ###################################################################
    # main loop of simulator
    ###################################################################
    while sched.time < time:
        sched.order()
        pktsize, qnum ,tasktype = sched.pop_event()
    ###################################################################
    # arrival task handler
    ###################################################################            
        if tasktype == ARITASK:
            sched.schedule_event(numpy.random.rayleigh(scale), numpy.random.binomial(4150,0.662) + 32, qnum, ARITASK)

            bufferTotal[qnum] += 1

            if state[qnum] == IDLE:
                state[qnum] = TX
                ddl[qnum] = sched.time + pktsize/SPEED
                for q in neighbour[qnum]:
                    if state[q] == IDLE:
                        state[q] = RX
                        lock[q].append(qnum)
                        receiver[qnum].append(q)
                    elif state[q] == RX:
                        if qnum not in lock[q]:
                            lock[q].append(qnum)
                        receiver[qnum].append(q)
                    else:
                        # tx_txCollision[q] += 1

                        pass 
                sched.schedule_event((ddl[qnum] - sched.time), 0, qnum, DDLTASK)

            elif state[qnum] == TX:
                if customer[qnum] < BUFFERSIZE:
                    bufferedPktSize[qnum].append(pktsize)
                    customer[qnum] += 1
                    

                else:
                    bufferLoss[qnum] += 1 #buffer loss

            else: # if node is RX state
                if customer[qnum] < BUFFERSIZE:
                    bufferedPktSize[qnum].append(pktsize)
                    customer[qnum] +=1
                else:
                    bufferLoss[qnum] += 1 #buffer loss
    ###################################################################
    # deadline task handler
    ###################################################################
        elif tasktype == DDLTASK : #ddltask, if a packet is finished being transmitted
            for node in neighbour[qnum]:
                totalReceivedPkt[node] += 1 #pkt received by this node add one, no matter if it's collision
                if len(lock[node]) == 1 and qnum in lock[node] and state[node] == RX:
                    successReceivedPkt[node] += 1
            totalSentPkt[qnum] += 1
            for node in neighbour[qnum]:
                if len(lock[node]) == 1 and qnum in lock[node] and state[node] == RX:
                    successSentPkt[qnum] += 1
                    break


            if customer[qnum] > 0: #if there still are some pkt in the buffer, set another deadline task for next pkt in the buffer
                
                customer[qnum] -= 1
                sched.schedule_event(WAITING, 0, qnum, RETXTASK)
                for q in receiver[qnum]:
                    lock[q].remove(qnum)
                    if not lock[q]:
                        state[q] = IDLE

                for q in receiver[qnum]:    
                    if customer[q] > 0 and not lock[q]:
                        state[q] = TX
                        ddl[q] = sched.time + bufferedPktSize[q].pop(0)/SPEED
                        customer[q] -=1

                        for i in neighbour[q]:
                            if i in neighbour[qnum]: #if this node is the shared neighbour of qnum and q, we have to do special handling
                                if state[i] == IDLE:
                                    if len(lock[i]) == 0 and customer[i] == 0:
                                        state[i] = RX
                                        lock[i].append(q)
                                        receiver[q].append(i)
                                elif state[i] == RX:
                                    lock[i].append(q)
                                    receiver[q].append(i)
                                else:
                                    # tx_txCollision[i] += 1
                                    pass

                            elif state[i] == IDLE:
                                state[i] = RX
                                lock[i].append(q)
                                receiver[q].append(i)
                            elif state[i] == RX:
                                if q not in lock[i]:
                                    lock[i].append(q)
                                receiver[q].append(i)
                            else:
                                # tx_txCollision[i] += 1
                                pass 
                        sched.schedule_event((ddl[q] - sched.time), 0, q, DDLTASK)
                receiver[qnum] = []

            else: #if the buffer is empty and this is the last pkt's deadline task
                state[qnum] = IDLE
                for q in receiver[qnum]:
                    lock[q].remove(qnum)
                    if not lock[q]:
                        state[q] = IDLE
                for q in receiver[qnum]:    
                    if customer[q] > 0 and not lock[q]:
                        state[q] = TX
                        ddl[q] = sched.time + bufferedPktSize[q].pop(0)/SPEED
                        customer[q] -=1

                        for i in neighbour[q]:
                            if i in neighbour[qnum]: #if this node is the shared neighbour of qnum and q, we have to do special handling
                                if state[i] == IDLE:
                                    if len(lock[i]) == 0 and customer[i] == 0:
                                        state[i] = RX
                                        lock[i].append(q)
                                        receiver[q].append(i)
                                elif state[i] == RX:
                                    lock[i].append(q)
                                    receiver[q].append(i)
                                else:
                                    # tx_txCollision[i] += 1
                                    pass

                            elif state[i] == IDLE:
                                state[i] = RX
                                lock[i].append(q)
                                receiver[q].append(i)
                            elif state[i] == RX:
                                if q not in lock[i]:
                                    lock[i].append(q)
                                receiver[q].append(i)
                            else:
                                # tx_txCollision[i] += 1
                                pass 
                        sched.schedule_event((ddl[q] - sched.time), 0, q, DDLTASK)

                receiver[qnum] = []
                bufferedPktSize[qnum] = []
    ###################################################################
    # retransmit task handler
    ###################################################################
        else: # task type is retransmit task
            ddl[qnum] = sched.time + bufferedPktSize[qnum].pop(0)/SPEED
            sched.schedule_event((ddl[qnum] - sched.time), 0, qnum, DDLTASK)
            if state[qnum] is not TX:
                state[qnum] = TX
            
            for q in neighbour[qnum]:
                    if state[q] == IDLE:
                        state[q] = RX
                        lock[q].append(qnum)
                        receiver[qnum].append(q)
                    elif state[q] == RX:
                        if qnum not in lock[q]:
                            lock[q].append(qnum)
                        receiver[qnum].append(q)
                    else:
                        # tx_txCollision[q] += 1
                        pass 

    #     fp.write(str(sched.time) + "," + ",".join([str(el) for el in customer.values()]) + "\n")
    # fp.close()

    ###################################################################
    # print output infomation
    ###################################################################
    print("##################################\n")
    print("bufferLoss :" + str(bufferLoss) + "\n")    
    print("totally generated pkt :" + str(bufferTotal) + "\n")
    print("buffer loss rate:" + str({i:(bufferLoss[i] / bufferTotal[i]) for i in range(node_amount)}) + "\n")
    print("tx_txCollision :"+str(tx_txCollision) + "\n")

    for i in range(len(totalReceivedPkt)):
        # successReceivedPkt[i] = successReceivedPkt[i] - tx_txCollision[i]
        # successSentPkt[i] = successSentPkt[i] - tx_txCollision[i]
        collisionPkt[i] = totalReceivedPkt[i] - successReceivedPkt[i]
        collisionSentPkt[i] = totalSentPkt[i] - successSentPkt[i]

    print("totally received pkt:" + str(totalReceivedPkt) + "\n")
    print("successfully received pkt:"+ str(successReceivedPkt) + "\n")
    print("collision pkt:" + str(collisionPkt) + "\n")
    print("collision rate:" + str({i:(collisionPkt[i] / totalReceivedPkt[i]) for i in range(node_amount)}) + "\n")

    print("totally sent pkt:"+ str(totalSentPkt) + "\n")
    print("successfully sent pkt:"+ str(successSentPkt) + "\n")
    print("Sent collision pkt:"+ str(collisionSentPkt) + "\n")
    print("Sent collision rate:" + str({i:(collisionSentPkt[i] / totalSentPkt[i]) for i in range(node_amount)}) + "\n")
    
    ###################################################################
    # output save to file
    ###################################################################

    filename1 = "collision1000" + ".csv"
    #filename1 = "collision_scale" + ".csv"
    fp = open(filename1, "a")
    #fp.write(str(successReceivedPkt[0]) + "," +",".join([str(successReceivedPkt[el+1]) for el in range(node_amount-1)]) +"," + str(scale)+ "\n")
    collisionrate = {i:(collisionPkt[i] / totalReceivedPkt[i]) for i in range(node_amount)}
    fp.write(",".join([str(collisionrate[el]) for el in range(node_amount)]) +"," + str(scale) + "\n")
    fp.close()

    filename2 = "loss1000" + ".csv"
    #filename2 = "loss_scale" + ".csv"
    fp = open(filename2, "a")
    #fp.write(str(successReceivedPkt[0]) + "," +",".join([str(successReceivedPkt[el+1]) for el in range(node_amount-1)]) +"," + str(scale)+ "\n")
    lossrate = {i:(bufferLoss[i] / bufferTotal[i]) for i in range(node_amount)}
    fp.write(",".join([str(lossrate[el]) for el in range(node_amount)]) +"," + str(scale) + "\n")
    fp.close()

    filename3 = "throughput1000" + ".csv"
    #filename2 = "loss_scale" + ".csv"
    fp = open(filename3, "a")
    # fp.write(",".join([str(successReceivedPkt[el]/time/SPEED) for el in range(node_amount)]) +"," + str(scale)+ str(sum(bufferTotal[n] for n in range(node_amount))*2779/time/SPEED)+ "\n")
    fp.write(",".join([str(successSentPkt[el]*2779/time/SPEED) for el in range(node_amount)]) +"," + str(scale) +","+ str(sum(bufferTotal[n] for n in range(node_amount))*2779/time/SPEED) + "\n")
    #lossrate = {i:(bufferLoss[i] / bufferTotal[i]) for i in range(node_amount)}
    #fp.write(str(lossrate[0]) + "," +",".join([str(lossrate[el+1]) for el in range(node_amount-1)]) +"," + str(scale) + "\n")
    fp.close()




        

    
# when scale = 0.003, I get good queueing data in buffer
if __name__ == '__main__':
    filename1 = "collision1000" + ".csv"
    fp = open(filename1, "a")
    #fp.write("node0, node1, node2, node3, node4, node5,node6, node7, node8, node9, scale\n")
    fp.write("node0, node1, node2, node3, node4, node5,node6, node7, node8, node9, scale\n")
    fp.close()

    filename2 = "loss1000" + ".csv"
    fp = open(filename2, "a")
    #fp.write("node0, node1, node2, node3, node4, node5,node6, node7, node8, node9, scale\n")
    fp.write("node0, node1, node2, node3, node4, node5,node6, node7, node8, node9, scale\n")
    fp.close()

    filename3 = "throughput1000" + ".csv"
    fp = open(filename3, "a")
    #fp.write("node0, node1, node2, node3, node4, node5,node6, node7, node8, node9, scale\n")
    fp.write("node0, node1, node2, node3, node4, node5,node6, node7, node8, node9, scale,rho\n")
    fp.close()


    for i in range(1000):
        simu(3, 0.00034)



