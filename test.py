#! /usr/bin/python3
import math
import numpy
import heapq


neighbour = {0: [5, 7, 9], 1: [6, 8], 2: [3, 4], 3: [2, 9], 4: [2], 5: [0, 7], 6: [1, 7], 7: [0, 5, 6], 8: [1], 9: [0, 3]}
#neighbour = {0: [1,2], 1:[0,2,3], 2:[0,1], 3:[1]}
node_amount = 10

IDLE = 'idle'
TX = 'tx'
RX = 'rx'
BUFFERSIZE = 30
SPEED =8*1024*1024

DDLTASK = 'ddltask' #deadline task
TASK = 'task' #arrival task

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
    state = {x : IDLE for x in range(node_amount)}
    customer = {x : 0 for x in range(node_amount)}
    ddl = {x : 0 for x in range(node_amount)}
    lock = {x : [] for x in range(node_amount)}
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

    sched = EventScheduler()
    for i in range(node_amount):
        sched.schedule_event(numpy.random.rayleigh(scale), numpy.random.binomial(4150,0.662) + 32, i, TASK)
    sched.order()

    # filename = "simudata" + str(scale) + ".csv"
    # fp = open(filename, "w")
    # fp.write("time,q0len,q1len\n")

    while sched.time < time:
        sched.order()
        # print ("--------------")
        # print (sched.queue)
        # print ("state: ",state)
        # print ("customer: ",customer)
        # print ("lock: ",lock)
        # print ("bufferedPktSize: ", bufferedPktSize)
        # print ("--------------")

        pktsize, qnum ,tasktype = sched.pop_event()
        #if qnum == 4:
            # print ("state: ",state)
            # print ("customer: ",customer)
            # print ("lock: ",lock)
            # print ("--------------")
        
        if tasktype == TASK:
            sched.schedule_event(numpy.random.rayleigh(scale), numpy.random.binomial(4150,0.662) + 32, qnum, TASK)
            sched.order()

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

                        pass 
                sched.schedule_event((ddl[qnum] - sched.time), 0, qnum, DDLTASK)
                sched.order()

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

        else: #ddltask
            for node in receiver[qnum]:
                # print(qnum)
                # print(lock[node])
                # print(state[node])
                totalReceivedPkt[node] += 1 #pkt received by this node add one, no matter if it's collision
                if len(lock[node]) == 1 and qnum in lock[node] and state[node] == RX:
                    successReceivedPkt[node] += 1
            totalSentPkt[qnum] += 1
            for node in receiver[qnum]:
                if len(lock[node]) == 1 and qnum in lock[node] and state[node] == RX:
                    successSentPkt[qnum] += 1
                    break


            if customer[qnum] > 0: #if there still are some pkt in the buffer, set another deadline task for next pkt in the buffer
                ddl[qnum] = sched.time + bufferedPktSize[qnum].pop(0)/SPEED
                customer[qnum] -= 1
                sched.schedule_event((ddl[qnum] - sched.time), 0, qnum, DDLTASK)
                sched.order()
                for q in neighbour[qnum]: #make sure all neighbours entering idle state will be involved in qnum
                    if state[q] == IDLE:
                        state[q] = RX
                        lock[q].append(qnum)
                        receiver[qnum].append(q)


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
                            if i in neighbour[qnum]: #if this node is the shared neighbour of qnum and q, we have to do special handing
                                if state[i] == IDLE:
                                    if len(lock[i]) == 0 and customer[i] == 0:
                                        state[i] = RX
                                        lock[i].append(q)
                                        receiver[q].append(i)
                                elif state[i] == RX:
                                    lock[i].append(q)
                                    receiver[q].append(i)
                                else:
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
                                pass 
                        sched.schedule_event((ddl[q] - sched.time), 0, q, DDLTASK)
                        sched.order()

                receiver[qnum] = []
                bufferedPktSize[qnum] = []

    #     fp.write(str(sched.time) + "," + ",".join([str(el) for el in customer.values()]) + "\n")
    # fp.close()
    
    # print("bufferLoss :",bufferLoss)    
    # print("totally generated pkt :",bufferTotal)
    # print("buffer loss rate:", {i:(bufferLoss[i] / bufferTotal[i]) for i in range(node_amount)})

    for i in range(len(totalReceivedPkt)):
        collisionPkt[i] = totalReceivedPkt[i] - successReceivedPkt[i]
        collisionSentPkt[i] = totalSentPkt[i] - successSentPkt[i]
    # print("totally received pkt:",totalReceivedPkt)
    # print("successfully received pkt:",successReceivedPkt)
    # print("collision pkt:",collisionPkt)
    print("collision rate:" ,{i:(collisionPkt[i] / totalReceivedPkt[i]) for i in range(node_amount)})

    # print("totally sent pkt:",totalSentPkt)
    # print("successfully sent pkt:",successSentPkt)
    # print("Sent collision pkt:",collisionSentPkt)
    print("Sent collision rate:" ,{i:(collisionSentPkt[i] / totalSentPkt[i]) for i in range(node_amount)})
    filename1 = "collision1000" + ".csv"
    #filename1 = "collision_scale" + ".csv"
    fp = open(filename1, "a")
    #fp.write(str(successReceivedPkt[0]) + "," +",".join([str(successReceivedPkt[el+1]) for el in range(node_amount-1)]) +"," + str(scale)+ "\n")
    collisionrate = {i:(collisionPkt[i] / totalReceivedPkt[i]) for i in range(node_amount)}
    fp.write(",".join([str(collisionrate[el]) for el in range(node_amount)]) +"," + str(scale) + "\n")
    # fp.write(str(collisionrate[0]) + "," +",".join([str(collisionrate[el+1]) for el in range(node_amount-1)]) +"," + str(scale) + "\n")
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
    #fp.write(str(successReceivedPkt[0]/10) + "," +",".join([str(successReceivedPkt[el+1]/10) for el in range(node_amount-1)]) +"," + str(scale)+ "\n")
    fp.write(",".join([str(successSentPkt[el]/10) for el in range(node_amount)]) +"," + str(scale)+ "\n")
    #lossrate = {i:(bufferLoss[i] / bufferTotal[i]) for i in range(node_amount)}
    #fp.write(str(lossrate[0]) + "," +",".join([str(lossrate[el+1]) for el in range(node_amount-1)]) +"," + str(scale) + "\n")
    fp.close()




        

    
# when scale = 0.003, I get good queueing data in buffer
if __name__ == '__main__':
    # filename1 = "collision_scale" + ".csv"
    # fp = open(filename1, "a")
    # #fp.write("node0, node1, node2, node3, node4, node5,node6, node7, node8, node9, scale\n")
    # fp.write("node0, node1, node2, node3, node4, node5,node6, node7, node8, node9, scale\n")
    # fp.close()

    # filename2 = "loss_scale" + ".csv"
    # fp = open(filename2, "a")
    # #fp.write("node0, node1, node2, node3, node4, node5,node6, node7, node8, node9, scale\n")
    # fp.write("node0, node1, node2, node3, node4, node5,node6, node7, node8, node9, scale\n")
    # fp.close()

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
    fp.write("node0, node1, node2, node3, node4, node5,node6, node7, node8, node9, scale\n")
    fp.close()


    for i in range(2, 11):
        simu(10, i/100)
        #print("**************************\n")

    #simu(10,0.003)


