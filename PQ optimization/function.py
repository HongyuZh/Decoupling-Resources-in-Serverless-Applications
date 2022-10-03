from typing import List
from priority_queue import *

class Function(object):
    """a monitoring of serverless functions"""

    def __init__(self, cpu_alloc, mem_alloc, runtime):
        self.cpu_alloc = cpu_alloc
        self.mem_alloc = mem_alloc
        self.runtime = runtime


class Workflow(Function):
    """a monitoring of serverless workflow"""

    def __init__(self, functions: List[function]):
        self.workflow = functions

        self.cpu_pq = PriorityQueue()
        self.mem_pq = PriorityQueue()

        self.runtime = 0

        for func in self.workflow:
            self.runtime += func.runtime
        



