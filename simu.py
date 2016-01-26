#! /usr/bin/python3
import math
import numpy
import heapq

receivers = {0: [5, 7, 9], 1: [6, 8], 2: [3, 4], 3: [2, 9], 4: [2], 5: [0, 7], 6: [1, 7], 7: [0, 5, 6], 8: [1], 9: [0, 3]}
IDLE = 0
TX = 1
RX = 2
BUFFERSIZE = 30
class EventScheduler:
    def __init__(self):
            self.queue = []
            self.time = 0
            self.last = 0
            self.bufferCount = 0

    def schedule_event(self, interval, pktsize, qnum):
            t = self.time + interval
            if t > self.last:
                self.last = t
            heapq.heappush(self.queue, (t, pktsize, qnum))

    def pop_event(self):
            e = heapq.heappop(self.queue)
            self.time = e[0]
            return e[1], e[2]

    def elapsed_time(self):
            return self.time

    def last_event_time(self):
            return self.last

    def sort(self):
            return sorted(self.queue, key = lambda event: event[0])


def simu(time, scale = 1):
	state = {x : 0 for x in range(10)}
	customer = {x : 0 for x in range(10)}
	sched = EventScheduler()

