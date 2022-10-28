import time

import docker

from priority_queue import *

cpu_base = 2
mem_base = 128
one_step_cpu = 0.25
one_step_mem = 16

cost_model = {'cpu_para': 64, 'mem_para': 1}
run_times = 3

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
    def __init__(self, image_id, id):
        # Initial configuration
        self.image_id = image_id
        self.id = id
        self.cpu_alloc = cpu_base
        self.mem_alloc = mem_base
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
                                          cpu_quota=int(
                                              self.cpu_alloc * 100000),
                                          memswap_limit=-1)

        print('Function-%s of image-%s is created, with cpu: %.2f and memory: %d.'
              % (self.id, self.image_id, self.cpu_alloc, self.mem_alloc))

        return container.short_id

    def update(self):
        # Restart the container and get its runtime
        runtime = 0

        # Repeat the execution to get more stable runtime
        for i in range(0, run_times):
            wait_complete()
            container = client.containers.get(self.container_id)
            container.restart()
            wait_complete()

            log = str(container.logs(), encoding='utf-8').strip()
            runtime += int(log.split(':')[-1])
        runtime /= run_times

        self.last_runtime = self.curr_runtime
        self.curr_runtime = runtime

        # Using the cost model to calculate the cost
        self.last_cost = self.curr_cost
        self.curr_cost = (self.cpu_alloc * cost_model['cpu_para'] +
                          self.mem_alloc * cost_model['mem_para']) * self.curr_runtime / 1000

    def one_step_dealloc(self, cpu_alloc=one_step_cpu, mem_alloc=one_step_mem):
        # Deallocate containers' CPU and memory
        # And update runtime and cost
        self.cpu_alloc -= cpu_alloc
        self.mem_alloc -= mem_alloc

        container = client.containers.run(self.image_id,
                                          detach=True,
                                          mem_limit=f'{self.mem_alloc}M',
                                          cpu_period=100000,
                                          cpu_quota=int(
                                              self.cpu_alloc * 100000),
                                          memswap_limit=-1)
        self.container_id = container.short_id

        self.update()


class Workflow(object):
    def __init__(self, images, slo):
        self.time_limit = slo

        self.workflow = []
        for i in range(0, len(images)):
            container = DockerContainer(images[i], i+1)
            self.workflow.append(container)

        # This class has two priority queue
        self.runtime_pq = PriorityQueue()
        self.cost_pq = PriorityQueue()

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
