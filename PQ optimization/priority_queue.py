import heapq

class PriorityQueue(object):
    def __init__(self):
        self._queue = []
        self._index = 0

    def push(self, item, priority):
        """
        This queue's elements are like (priority, index, priority)
        """
        heapq.heappush(self._queue,(-priority, self._index, item))
        self._index += 1

    def pop(self):
        return heapq.heappop(self._queue)[-1]

    def qsize(self):
        return len(self._queue)

    def isempty(self):
        return True if not self._queue else False
        
