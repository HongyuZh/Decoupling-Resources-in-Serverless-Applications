import math
import time

import docker

from priority_queue import *

cpu_base = 2
mem_base = 256

one_step_cpu = 0.25
one_step_mem = 64

cost_model = {'cpu_para': 128, 'mem_para': 1}

client = docker.from_env()


def wait_complete():
    # attentioon: before the execution of a container, we should guarantee that there is no
    # other containers are running. otherwise, the time accuracy will be affected
    while True:
        active_containers = client.containers.list()

        if len(active_containers) == 0:
            break
        else:
            # sleep for 2 seconds
            time.sleep(2)


class DockerContainer(object):
    # A self-defined docker api
    def __init__(self, image_name):
        # Initial configuration
        self.image_name = image_name
        self.cpu_alloc = cpu_base
        self.mem_alloc = mem_base
        # Simply use the current allocation to create a container and get its id
        self.container_id = self._init_container()

        self.curr_runtime = 0
        self.last_runtime = 0
        self.curr_cost = 0
        self.last_cost = 0

    def _init_container(self):
        # Object: Pre-warming the container.
        # Create the container and return its id.
        container = client.containers.run(self.image_name,
                                          detach=True,
                                          mem_limit=f'{self.mem_alloc}M',
                                          cpu_period=100000,
                                          cpu_quota=(self.cpu_alloc * 100000),
                                          memswap_limit=-1)

        print("Info: container:%s of image:%s is created, with cpu:%.2f and memory:%d."
              % (container.short_id, self.image_name, self.cpu_alloc, self.mem_alloc))

        return container.short_id

    def run_and_set_runtime(self):
        # Set both the current runtime and the last runtime
        # Restart the container and get its runtime
        wait_complete()

        container = client.containers.get(self.container_id)
        container.restart()

        wait_complete()

        log = str(container.logs(), encoding='utf-8').strip()
        # print(logs)

        try:
            runtime = int(log.split(':')[-1])
        except:
            print("Error: couldn't get runtime.")
            return

        self.last_runtime = self.curr_runtime
        self.curr_runtime = runtime

    def _set_cost(self):
        # Using the cost model to calculate the cost
        self.last_cost = self.curr_cost
        self.curr_cost = (self.cpu_alloc * cost_model['cpu_para'] +
                          self.mem_alloc*cost_model['mem_para']) * self.curr_runtime

    def one_step_dealloc(self, cpu_alloc=one_step_cpu, mem_alloc=one_step_mem):
        # Deallocate containers' CPU and memory
        # And update runtime and cost
        if (cpu_alloc > self.cpu_alloc & mem_alloc > self.mem_alloc):
            print("Error: can't set cpu/memory a negative number.")
            return

        self.cpu_alloc -= cpu_alloc
        self.mem_alloc -= mem_alloc
        container = client.containers.get(self.container_id)
        container.update(cpu_quota=(self.cpu_alloc*100000),
                         mem_limit=f'{self.mem_alloc}M')

        self.run_and_set_runtime()
        self._set_cost()

    def update(self):
        # Update runtime and cost
        self.run_and_set_runtime()
        self._set_cost()


class Workflow(object):
    # Monitoring docker workflow
    def __init__(self, images, slo):

        self.time_limit = slo

        self.workflow = []
        for image in images:
            container = DockerContainer(image)
            self.workflow.append(container)
        # This class has two priority queue
        self.runtime_pq = PriorityQueue()
        self.cost_pq = PriorityQueue()

        self._init_runtime_pq()
        self._max_config()
        self._init_cost_pq()

    def get_runtime(self):
        # Get the runtime of the workflow as the sum of each function's runtime
        runtime = 0
        for func in self.workflow:
            runtime += func.curr_runtime

        return runtime

    def get_cost(self):
        # Get the cost of the workflow as the sum of each function's cost
        cost = 0
        for func in self.workflow:
            cost += func.curr_cost

        return cost

    def _init_runtime_pq(self):
        # Define the element in the runtime pq to be {'function': xxx, 'type': xxx}
        for func in self.workflow:
            func.update()

            item_cpu = {'function': func, 'type': 'cpu'}
            item_mem = {'function': func, 'type': 'memory'}

            self.runtime_pq.push(item_cpu, math.inf)
            self.runtime_pq.push(item_mem, math.inf)

    def _max_config(self):

        try:
            runtime = self.get_runtime()
            while runtime > self.time_limit:
                # First get the function with the highest priority
                item = self.runtime_pq.pop()
                func = item['function']
                type = item['type']
                # Increase the resources until we meet the SLO
                # According to its type, choose different operation
                if type == 'cpu':

                    func.one_step_dealloc(-cpu_base, 0)
                    # Push into the queue
                    item = item = {'function': func, 'type': type}
                    prioirty = func.curr_runtime - func.last_runtime
                    self.runtime_pq.push(item, prioirty)

                if type == 'memory':

                    func.one_step_dealloc(0, -mem_base)
                    # Push into the queue
                    item = item = {'function': func, 'type': type}
                    prioirty = func.curr_runtime - func.last_runtime
                    self.runtime_pq.push(item, prioirty)

                runtime += func.curr_runtime - func.last_runtime

        except:
            print("Error: can't meet the time limit.")
            return

        print("\nInfo: current configuration:\n")
        for func in self.workflow:
            print("function:%s of image:%s, with cpu:%.2f and memory:%d."
                  % (func.container_id, func.image_name, func.cpu_alloc, func.mem_alloc))

        runtime = self.get_runtime()
        print("\nInfo: current runtime: %.2f" % (runtime))

    def _init_cost_pq(self):
        # Define the element in the cost pq to be {'function': xxx, 'type': xxx}
        for func in self.workflow:
            item_cpu = {'function': func, 'type': 'cpu'}
            item_mem = {'function': func, 'type': 'memory'}

            self.cost_pq.push(item_cpu, math.inf)
            self.cost_pq.push(item_mem, math.inf)

        cost = self.get_cost()
        print('\nInfo: Cost_pq has been initialized. Current cost is %.2f.\n' % (cost))

    def min_cost(self, cpu_alloc=one_step_cpu, mem_alloc=one_step_mem):
        try:
            runtime = self.get_runtime()
            while runtime < self.time_limit & self.cost_pq.notEmpty():
                # First get the function with the highest priority
                item = self.cost_pq.pop()
                func = item['function']
                type = item['type']
                # According to its type, choose different operation
                # If slo isn't meet after the deallocation,
                # restore the configuration
                # and the function won't come back to the queue again
                if type == 'cpu':

                    print("Info: deallocate cpu of  function:%s by %.2f."
                          % (func.container_id, cpu_alloc))

                    func.one_step_dealloc(cpu_alloc, 0)
                    if self.get_runtime() > self.time_limit:
                        print("Runtime is too long! Retrive the deallocation.")
                        func.cpu_alloc += cpu_alloc
                    else:
                        item = {'function': func, 'type': type}
                        priority = func.last_cost - func.curr_cost
                        self.cost_pq.push(item, priority)

                if type == 'memory':

                    print("Info: deallocate memory of  function:%s by %d."
                          % (func.container_id, mem_alloc))

                    func.one_step_dealloc(0, mem_alloc)
                    if self.get_runtime() > self.time_limit:
                        print("Runtime is too long! Retrive the deallocation.")
                        func.mem_alloc += mem_alloc
                    else:
                        item = {'function': func, 'type': type}
                        priority = func.last_cost - func.curr_cost
                        self.cost_pq.push(item, priority)
        except:
            pass

        cost = self.get_cost()
        print("Info: current cost is %.2f." % (cost))
