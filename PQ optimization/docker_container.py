import os
import time
from typing import List
from priority_queue import *


one_step_cpu = 0.25
one_step_mem = 64


class docker_container(object):
    def __init__(self, image_name):

        self.cpu_alloc = 0.25
        self.mem_alloc = 64

        flag = True

        while flag == True:
            try:
                cmd = "docker run -d -t " + image_name+" -m " + \
                    str(self.mem_alloc) + " --cpus=" + str(self.cpu_alloc)
                output = os.popen(cmd)
                flag = False

            # if the execution fails, give the function more memories

            except:
                self.mem_alloc += one_step_mem

        self.container_name = output.readlines()[0]

        self.curr_runtime = 0
        self.last_runtime = 0

    def init_container(self):
        cmd = "docker restart " + self.container_name

        start = time.perf_counter()
        os.system(cmd)
        end = time.perf_counter()

        self.curr_runtime = int(end - start)

    def set_runtime(self, runtime):
        self.last_runtime = self.curr_runtime
        self.curr_runtime = runtime

    def one_step_cpu_alloc(self):
        self.cpu_alloc += one_step_cpu

        cmd = "docker update --cpus " + \
            str(self.cpu_alloc) + self.container_name
        os.system(cmd)

        cmd = "docker restart " + self.container_name

        start = time.perf_counter()
        os.system(cmd)
        end = time.perf_counter()

        runtime = int(end - start)
        self.set_runtime(runtime)

    def one_step_mem_alloc(self):
        self.mem_alloc += one_step_mem

        cmd = "docker update --cpus " + \
            str(self.mem_alloc) + self.container_name
        os.system(cmd)

        cmd = "docker restart " + self.container_name

        start = time.perf_counter()
        os.system(cmd)
        end = time.perf_counter()

        runtime = int(end - start)
        self.set_runtime(runtime)

class Workflow(object):
    def __init__(self, containers: List[docker_container]):
        self.workflow = containers

        self.cpu_pq = PriorityQueue()
        self.mem_pq = PriorityQueue()

        self.runtime = 0
        for func in self.workflow:
            self.runtime += func.curr_runtime

        self.init_cpu_alloc
        self.init_mem_alloc

    def init_cpu_alloc(self):
        for func in self.workflow:
            func.one_step_cpu_alloc()
            self.runtime += func.curr_runtime - func.last_runtime

        self.init_cpu_queue()
        
    def init_mem_alloc(self):
        for func in self.workflow:
            func.one_step_mem_alloc()
            self.runtime += func.curr_runtime - func.last_runtime

        self.init_mem_queue()


    def init_cpu_queue(self):

        for func in self.workflow:
            prioirty = func.curr_runtime - func.last_runtime
            self.cpu_pq.push((func, prioirty))
            self.mem_pq.push((func, prioirty))

    def init_mem_queue(self):

        for func in self.workflow:
            prioirty = func.curr_runtime - func.last_runtime
            self.mem_pq.push((func, prioirty))

    def one_step_cpu_alloc(self):
        func = self.cpu_pq.pop()

        func.one_step_cpu_alloc()
        self.runtime += func.curr_runtime - func.last_runtime

    def one_step_mem_alloc(self):
        func = self.mem_pq.pop()

        func.one_step_mem_alloc()
        self.runtime += func.curr_runtime - func.last_runtime