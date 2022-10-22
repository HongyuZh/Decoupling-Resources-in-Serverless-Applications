from cProfile import run
import math
import time

import docker

from priority_queue import *

cpu_base = 2
mem_base = 128
one_step_cpu = 0.25
one_step_mem = 16
alpha = 0.05

cost_model = {'cpu_para': 64, 'mem_para': 1}

_trial = 2

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
    def __init__(self, image_id, idx):
        # Initial configuration
        self.image_id = image_id
        self.cpu_alloc = cpu_base
        self.mem_alloc = mem_base
        self.idx = idx
        # Simply use the current allocation to create a container and get its id
        self.container_id = self._init_container()

        self.curr_runtime = 0
        self.last_runtime = 0
        self.curr_cost = 0
        self.last_cost = 0

        self.update()

    def _init_container(self):
        # Object: Pre-warming the container.
        # Create the container and return its id.
        container = client.containers.run(self.image_id,
                                          detach=True,
                                          mem_limit=f'{self.mem_alloc}M',
                                          cpu_period=100000,
                                          cpu_quota=(self.cpu_alloc * 100000),
                                          memswap_limit=-1)

        print("Info: container-%s of image-%s is created, with cpu:%.2f and memory:%d."
              % (self.idx, self.image_id, self.cpu_alloc, self.mem_alloc))

        return container.short_id

    def run_and_set_runtime(self):
        # Set both the current runtime and the last runtime
        # Restart the container and get its runtime
        runtime = 0
        for i in range(0, _trial):
            wait_complete()

            container = client.containers.get(self.container_id)
            container.restart()

            wait_complete()

            log = str(container.logs(), encoding='utf-8').strip()
            # print(logs)

            runtime += int(log.split(':')[-1])
        runtime /= _trial

        self.last_runtime = self.curr_runtime
        self.curr_runtime = runtime

    def _set_cost(self):
        # Using the cost model to calculate the cost
        self.last_cost = self.curr_cost
        self.curr_cost = (self.cpu_alloc * cost_model['cpu_para'] +
                          self.mem_alloc * cost_model['mem_para']) * self.curr_runtime / 1000

    def one_step_dealloc(self, cpu_alloc=one_step_cpu, mem_alloc=one_step_mem):
        # Deallocate containers' CPU and memory
        # And update runtime and cost
        if cpu_alloc > self.cpu_alloc or mem_alloc > self.mem_alloc:
            print("Warn: can't set cpu/memory a negative number.")
            return 'Warn'

        self.cpu_alloc -= cpu_alloc
        self.mem_alloc -= mem_alloc
        wait_complete()

        try:

            container = client.containers.run(self.image_id,
                                              detach=True,
                                              mem_limit=f'{self.mem_alloc}M',
                                              cpu_period=100000,
                                              cpu_quota=int(
                                                  self.cpu_alloc * 100000),
                                              memswap_limit=-1)
            self.container_id = container.short_id

        except:
            print('Error: update failed.')
            return 'Error'

        self.update()
        return 'Success'

    def update(self):
        # Update runtime and cost
        self.run_and_set_runtime()
        self._set_cost()


class Workflow(object):
    # Monitoring docker workflow
    def __init__(self, images, slo):

        self.time_limit = slo

        self.workflow = []
        for i in range(0, len(images)):
            container = DockerContainer(images[i], i)
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

            item_cpu = {'function': func, 'type': 'cpu'}
            item_mem = {'function': func, 'type': 'memory'}

            self.runtime_pq.push(item_cpu, math.inf)
            self.runtime_pq.push(item_mem, math.inf)

        runtime = self.get_runtime()

        print('\nInfo: current runtime:%.2f.\n' %
              (runtime))

    def _max_config(self):

        runtime = self.get_runtime()
        while runtime > self.time_limit:
            # First get the function with the highest priority
            item = self.runtime_pq.pop()
            func = item['function']
            type = item['type']
            # Increase the resources until we meet the SLO
            # According to its type, choose different operation
            if type == 'cpu':

                print("Info: allocate cpu to function-%s by %.2f."
                      % (func.idx, cpu_base))

                func.one_step_dealloc(-cpu_base, 0)
                # Push into the queue
                item = item = {'function': func, 'type': type}
                if func.curr_runtime < func.last_runtime:
                    prioirty = func.last_runtime - func.curr_runtime
                else:
                    prioirty = 0
                self.runtime_pq.push(item, prioirty)

            if type == 'memory':

                print("Info: allocate memory to function-%s by %d."
                      % (func.idx, mem_base))

                func.one_step_dealloc(0, -mem_base)
                # Push into the queue
                item = item = {'function': func, 'type': type}
                if func.curr_runtime < func.last_runtime:
                    prioirty = func.last_runtime - func.curr_runtime
                else:
                    prioirty = 0
                self.runtime_pq.push(item, prioirty)

            runtime += func.curr_runtime - func.last_runtime
            print('Info: current runtime: %.2f.' % (runtime))

        print("\nInfo: after max_config, current configuration:\n")
        for func in self.workflow:
            print("function-%s of image-%s, with cpu:%.2f and memory:%d."
                  % (func.idx, func.image_id, func.cpu_alloc, func.mem_alloc))

        runtime = self.get_runtime()
        print("Info: current runtime: %.2f" % (runtime))

    def _init_cost_pq(self):
        # Define the element in the cost pq to be {'function': xxx, 'type': xxx}
        for func in self.workflow:
            item_cpu = {'function': func, 'type': 'cpu', 'trial': _trial}
            item_mem = {'function': func, 'type': 'memory', 'trial': _trial}

            self.cost_pq.push(item_cpu, math.inf)
            self.cost_pq.push(item_mem, math.inf)

        cost = self.get_cost()
        print('\nInfo: Cost_pq has been initialized. Current cost is %.2f.\n' % (cost))

    def min_cost(self, cpu_alloc=one_step_cpu, mem_alloc=one_step_mem):
        print('Info: Min_cost config starts\n')
        last_cost = self.get_cost()

        while self.cost_pq.notEmpty():

            # First get the function with the highest priority
            item = self.cost_pq.pop()
            func = item['function']
            type = item['type']
            trial = item['trial']

            # According to its type, choose different operation
            # If slo isn't meet after the deallocation,
            # restore the configuration
            # and the function won't come back to the queue again
            if type == 'cpu':

                print("Info: try to deallocate cpu from function-%s by %.2f."
                      % (func.idx, cpu_alloc))

                res = func.one_step_dealloc(cpu_alloc, 0)
                cost = self.get_cost()
                runtime = self.get_runtime()
                # Error handler
                if res == 'Error':
                    return 'Error'
                elif res == 'Warn':
                    func.cpu_alloc += cpu_alloc
                    continue
                # Set two trials if performance doesn't meet expectations
                elif runtime > self.time_limit:
                    func.cpu_alloc += cpu_alloc
                    func.one_step_dealloc(0, 0)
                    print("Warn: long runtime. (runtime: %.2f)" %
                          (runtime))
                    if trial > 0:
                        trial -= 1
                        item = {'function': func, 'type': type, 'trial': trial}
                        priority = 0
                        self.cost_pq.push(item, priority)
                    else:
                        print("Info: function-%d type-%s out of queue." %
                              (func.idx, type))
                        continue

                elif cost > last_cost*(1+alpha):
                    func.cpu_alloc += cpu_alloc
                    func.one_step_dealloc(0, 0)
                    print("Warn: heavy cost. (cost: %.2f)" %
                          (cost))
                    if trial > 0:
                        trial -= 1
                        item = {'function': func, 'type': type, 'trial': trial}
                        priority = 0
                        self.cost_pq.push(item, priority)
                    else:
                        print("Info: function-%d type-%s out of queue." %
                              (func.idx, type))
                        continue
                else:
                    print('Info: complete. current cost: %.2f' % (cost))
                    trial = _trial
                    # Put in queue
                    item = {'function': func, 'type': type, 'trial': trial}
                    if cost < last_cost:
                        priority = last_cost - cost
                    else:
                        priority = 0
                    self.cost_pq.push(item, priority)
                    last_cost = cost

            if type == 'memory':

                print("Info: try to deallocate mem from function-%s by %.2f."
                      % (func.idx, mem_alloc))

                res = func.one_step_dealloc(0, mem_alloc)
                cost = self.get_cost()
                runtime = self.get_runtime()
                # Error handler
                if res == 'Error':
                    return 'Error'
                elif res == 'Warn':
                    func.mem_alloc += mem_alloc
                    continue
                # Set two trials if performance doesn't meet expectations
                elif runtime > self.time_limit:
                    func.mem_alloc += mem_alloc
                    func.one_step_dealloc(0, 0)
                    print("Warn: long runtime. (runtime: %.2f)" %
                          (runtime))
                    if trial > 0:
                        trial -= 1
                        item = {'function': func, 'type': type, 'trial': trial}
                        priority = 0
                        self.cost_pq.push(item, priority)
                    else:
                        print("Info: function-%d type-%s out of queue." %
                              (func.idx, type))
                        continue

                elif cost > last_cost*(1+alpha):
                    func.mem_alloc += mem_alloc
                    func.one_step_dealloc(0, 0)
                    print("Warn: heavy cost. (cost: %.2f)" %
                          (cost))
                    if trial > 0:
                        trial -= 1
                        item = {'function': func, 'type': type, 'trial': trial}
                        priority = 0
                        self.cost_pq.push(item, priority)
                    else:
                        print("Info: function-%d type-%s out of queue." %
                              (func.idx, type))
                        continue
                else:
                    print('Info: complete. current cost: %.2f' % (cost))
                    trial = _trial
                    # Put in queue
                    item = {'function': func, 'type': type, 'trial': trial}
                    if cost < last_cost:
                        priority = last_cost - cost
                    else:
                        priority = 0
                    self.cost_pq.push(item, priority)
                    last_cost = cost

        print("\nInfo: after min_cost, current configuration:\n")
        for func in self.workflow:
            print("function-%s of image-%s, with cpu:%.2f and memory:%d."
                  % (func.idx, func.image_id, func.cpu_alloc, func.mem_alloc))

        print("\nInfo: current cost is %.2f." % (last_cost))
        print("Info: current runtime: %.2f" % (runtime))
        return 'success'
