from typing import List
from priority_queue import *


class Function(object):
    """a monitoring of serverless functions"""

    def __init__(self, index, cpu_alloc, mem_alloc, curr_runtime):
        self.index = index
        self.cpu_alloc = cpu_alloc
        self.mem_alloc = mem_alloc
        self.curr_runtime = curr_runtime
        self.last_runtime = 0

    def set_runtime(self, runtime):
        self.last_runtime = self.curr_runtime
        self.curr_runtime = runtime


class Workflow(Function):
    """a monitoring of serverless workflow"""

    def __init__(self, functions: List[function]):
        self.workflow = functions

        self.cpu_pq = PriorityQueue()
        self.mem_pq = PriorityQueue()

        self.runtime = 0

        for func in self.workflow:
            self.runtime += func.curr_runtime

    def init_queue(self):
        for func in self.workflow:
            prioirty = func.curr_runtime - func.last_runtime
            self.cpu_pq.push((func, prioirty))
            self.mem_pq.push((func, prioirty))
