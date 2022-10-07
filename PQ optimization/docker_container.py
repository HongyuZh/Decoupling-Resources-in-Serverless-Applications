import os
import time
from typing import List
from priority_queue import *


cpu_base = 2
mem_base = 256
one_step_cpu = 0.25
one_step_mem = 64


class DockerContainer(object):

    # A self-defined docker api

    def __init__(self, image_name):

        self.cpu_alloc = cpu_base
        self.mem_alloc = mem_base

        out_of_mem = True

        while out_of_mem == True:
            try:
                cmd = "docker run -d -t " + image_name+" -m " + \
                    str(self.mem_alloc) + " --cpus=" + str(self.cpu_alloc)
                output = os.popen(cmd)
                out_of_mem = False

            # If the execution fails, double the memory

            except:
                self.mem_alloc *= 2

        self.container_name = output.readlines()[0]

        self.curr_runtime = 0
        self.last_runtime = 0

        self.init_container()

    def init_container(self):

        # Restart these containers to get the runtime

        cmd = "docker restart " + self.container_name

        start = time.perf_counter()
        os.system(cmd)
        end = time.perf_counter()

        self.curr_runtime = int(end - start)

    def set_runtime(self, runtime):

        # Set both the current runtime and the last runtime

        self.last_runtime = self.curr_runtime
        self.curr_runtime = runtime

    def one_step_cpu_dealloc(self, cpu_alloc=one_step_cpu):

        # Deallocate containers' CPU and get runtime

        self.cpu_alloc -= cpu_alloc

        cmd = "docker update --cpus " + \
            str(self.cpu_alloc) + self.container_name
        os.system(cmd)

        cmd = "docker restart " + self.container_name

        start = time.perf_counter()
        os.system(cmd)
        end = time.perf_counter()

        runtime = int(end - start)
        self.set_runtime(runtime)

    def one_step_mem_dealloc(self, mem_alloc=one_step_mem):

        # Deallocate containers' CPU and get runtime

        self.mem_alloc -= mem_alloc

        cmd = "docker update -m " + \
            str(self.mem_alloc) + self.container_name
        os.system(cmd)

        cmd = "docker restart " + self.container_name

        start = time.perf_counter()
        os.system(cmd)
        end = time.perf_counter()

        runtime = int(end - start)
        self.set_runtime(runtime)


class Workflow(object):

    # Monitoring docker workflow

    def __init__(self, images, slo):

        self.slo = slo

        self.workflow = []

        for image in images:
            container = DockerContainer(image)
            self.workflow.append(container)

        self.cpu_pq = PriorityQueue()
        self.mem_pq = PriorityQueue()

        self.runtime = 0
        for func in self.workflow:
            self.runtime += func.curr_runtime

            self.cpu_pq.push(func, 0)
            self.mem_pq.push(func, 0)

        self.max_config()

    def max_config(self):

        # Double the resources until we meet the SLO

        while self.runtime > self.slo:

            # Double the cpu

            func = self.cpu_pq.pop()
            cpu_alloc = func.cpu_alloc
            func.one_step_cpu_dealloc(-cpu_alloc)

            prioirty = (func.curr_runtime - func.last_runtime)/cpu_alloc
            self.cpu_pq.push(func, prioirty)

            self.runtime += func.curr_runtime - func.last_runtime

            # Double the mem

            func = self.mem_pq.pop()
            mem_alloc = func.mem_alloc
            func.one_step_mem_dealloc(-mem_alloc)

            prioirty = (func.curr_runtime - func.last_runtime)/mem_alloc
            self.mem_pq.push(func, prioirty)

            self.runtime += func.curr_runtime - func.last_runtime

    def one_step_cpu_dealloc(self, cpu_alloc=one_step_cpu):

        func = self.cpu_pq.pop()
        func.one_step_cpu_dealloc(cpu_alloc)

        prioirty = (func.last_runtime - func.curr_runtime)/cpu_alloc
        self.cpu_pq.push(func, prioirty)

        self.runtime += func.curr_runtime - func.last_runtime

    def mem_base_alloc(self, mem_alloc=one_step_mem):

        func = self.mem_pq.pop()
        func.one_step_mem_dealloc(mem_alloc)

        priority = (func.last_runtime - func.curr_runtime)/mem_alloc
        self.mem_pq.push(func, priority)

        self.runtime += func.curr_runtime - func.last_runtime
