import heapq

class PriorityQueue(object):
    '''
        The heap queue is organised from the greatest to the least
        So I add '-' to the priority in function heappush
        Such that the one with hightest priority would appear at the tail of the queue
        And heappop would pop it out
    '''
    def __init__(self):
        self._queue = []
        self._index = 0

    def push(self, item, priority):

        # This queue's elements are like (priority, index, priority)

        heapq.heappush(self._queue,(-priority, self._index, item))
        self._index += 1

    def pop(self):

        # Pop the one with the greatest priority

        return heapq.heappop(self._queue)[-1]

    def notEmpty(self):
        return len(self._queue) > 0

