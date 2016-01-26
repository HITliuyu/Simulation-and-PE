#! /usr/bin/python3
import math
import numpy
import heapq


#neighbour = {0: [5, 7, 9], 1: [6, 8], 2: [3, 4], 3: [2, 9], 4: [2], 5: [0, 7], 6: [1, 7], 7: [0, 5, 6], 8: [1], 9: [0, 3]}
neighbour = {0: [1], 1:[0]}
node_amount = 2

IDLE = 'idle'
TX = 'tx'
RX = 'rx'
BUFFERSIZE = 30
SPEED = 1024*1024

SENDER_DDLTASK = 'ddltask'
TASK = 'task'
RELEASED = -1

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
    lock = {x : RELEASED for x in range(node_amount)}
    bufferedPktSize = {x : [] for x in range(node_amount)}
    receiver = {x:[] for x in range(node_amount)}

    sched = EventScheduler()
    for i in range(node_amount):
        sched.schedule_event(numpy.random.rayleigh(scale), numpy.random.binomial(4150,0.662) + 32, i, TASK)
    sched.order()

    filename = "simudata" + str(scale) + ".csv"
    fp = open(filename, "w")
    fp.write("time,q0len,q1len\n")

    while sched.time < time:
        sched.order()
        print ("--------------")
        print (sched.queue)
        print ("state: ",state)
        print ("customer: ",customer)
        print ("bufferedPktSize: ", bufferedPktSize)
        print ("--------------")

        pktsize, qnum ,tasktype = sched.pop_event()
        
        if tasktype == TASK:
            sched.schedule_event(numpy.random.rayleigh(scale), numpy.random.binomial(4150,0.662) + 32, qnum, TASK)
            sched.order()

            if state[qnum] == IDLE:
                state[qnum] = TX
                ddl[qnum] = sched.time + pktsize/SPEED
                for q in neighbour[qnum]:
                    if state[q] == IDLE:
                        state[q] = RX
                        lock[q] = qnum
                        receiver[qnum].append(q)
                    elif state[q] == RX:
                        pass # collision
                    else:
                        pass #seems not possbile
                sched.schedule_event((ddl[qnum] - sched.time), 0, qnum, SENDER_DDLTASK)
                sched.order()

            elif state[qnum] == TX:
                if customer[qnum] < BUFFERSIZE:
                    bufferedPktSize[qnum].append(pktsize)
                    customer[qnum] += 1
                    

                else:
                    pass #loss

            else: # if node is RX state
                if customer[qnum] < BUFFERSIZE:
                    bufferedPktSize[qnum].append(pktsize)
                    customer[qnum] +=1
                else:
                    pass #loss

        else:
            if customer[qnum] > 0:
                ddl[qnum] = sched.time + bufferedPktSize[qnum].pop(0)/SPEED
                customer[qnum] -= 1
                sched.schedule_event((ddl[qnum] - sched.time), 0, qnum, SENDER_DDLTASK)
                sched.order()

            else:
                state[qnum] = IDLE
                for q in receiver[qnum]:
                    state[q] = IDLE
                    lock[q] = RELEASED
                    if customer[q] > 0:
                        state[q] = TX
                        ddl[q] = sched.time + bufferedPktSize[q].pop(0)/SPEED
                        customer[q] -=1

                        for i in neighbour[q]:
                            if state[i] == IDLE:
                                state[i] = RX
                                lock[i] = q
                                receiver[q].append(i)
                            elif state[i] == RX:
                                pass # collision
                            else:
                                pass #seems not possbile
                        sched.schedule_event((ddl[q] - sched.time), 0, q, SENDER_DDLTASK)
                        sched.order()

                receiver[qnum] = []
                bufferedPktSize[qnum] = []

        fp.write(str(sched.time) + "," + ",".join([str(el) for el in customer.values()]) + "\n")
    fp.close()
        
        

    
# when scale = 0.003, I get good queueing data in buffer
if __name__ == '__main__':
    simu(1000) 



