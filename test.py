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
SPEED = 1024*1024

DDLTASK = 'ddltask'
TASK = 'task'

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

    sched = EventScheduler()
    for i in range(node_amount):
        sched.schedule_event(numpy.random.rayleigh(scale), numpy.random.binomial(4150,0.662) + 32, i, TASK)
    sched.order()

    filename = "simudata" + str(scale) + ".csv"
    fp = open(filename, "w")
    fp.write("time,q0len,q1len\n")

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
                        pass # collision
                    else:
                        pass #seems not possbile
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
            for qn in receiver[qnum]:
                totalReceivedPkt[qn] += 1
            for node in receiver[qnum]:
                print(qnum)
                print(lock[node])
                print(state[node])
                if len(lock[node]) == 1 and qnum in lock[node] and state[node] == RX:
                    successReceivedPkt[node] += 1
            #collisionPkt[qnum] = totalReceivedPkt[qnum] - successReceivedPkt[qnum]

            if customer[qnum] > 0:
                ddl[qnum] = sched.time + bufferedPktSize[qnum].pop(0)/SPEED
                customer[qnum] -= 1
                sched.schedule_event((ddl[qnum] - sched.time), 0, qnum, DDLTASK)
                sched.order()

            else:
                state[qnum] = IDLE
                for q in receiver[qnum]:
                    lock[q].remove(qnum)
                    if not lock[q]:
                        state[q] = IDLE
                    
                    if customer[q] > 0 and not lock[q]:
                        state[q] = TX
                        ddl[q] = sched.time + bufferedPktSize[q].pop(0)/SPEED
                        customer[q] -=1

                        for i in neighbour[q]:
                            if i in neighbour[qnum]:
                                if qnum in lock[i]:
                                    pass
                                else:
                                    if state[i] == TX:
                                        print ('-----yes-----')
                                    print ('pass')
                                    pass #collision
                            elif state[i] == IDLE:
                                state[i] = RX
                                lock[i].append(q)
                                receiver[q].append(i)
                            elif state[i] == RX:
                                if q not in lock[i]:
                                    lock[i].append(q)
                                receiver[q].append(i)
                                pass # collision
                            else:
                                pass #seems not possbile
                        sched.schedule_event((ddl[q] - sched.time), 0, q, DDLTASK)
                        sched.order()

                receiver[qnum] = []
                bufferedPktSize[qnum] = []

        fp.write(str(sched.time) + "," + ",".join([str(el) for el in customer.values()]) + "\n")
    fp.close()
    print("bufferLoss :",bufferLoss)    
    print("totally generated pkt :",bufferTotal)
    print("buffer loss rate:", {i:(bufferLoss[i] / bufferTotal[i]) for i in range(node_amount)})

    for i in range(len(totalReceivedPkt)):
        collisionPkt[i] = totalReceivedPkt[i] - successReceivedPkt[i]
    print("totally sent pkt:",totalReceivedPkt)
    print("successfully sent pkt:",successReceivedPkt)
    print("collision pkt:",collisionPkt)
    print("collision rate:" ,{i:(collisionPkt[i] / totalReceivedPkt[i]) for i in range(node_amount)})

        

    
# when scale = 0.003, I get good queueing data in buffer
if __name__ == '__main__':
    simu(10, 0.003) 



