import argparse

import numpy as np
import yaml

from docker_container import *

one_step_cpu = 0.25
one_step_mem = 16
_trial_ = 1
error = 0.05

result = {}


def init_runtime_pq(DAG):
    # Define the element in the runtime pq to be {'function': xxx, 'type': xxx}
    for func in DAG.workflow:

        item_cpu = {'function': func, 'type': 'cpu'}
        item_mem = {'function': func, 'type': 'memory'}

        DAG.runtime_pq.push(item_cpu, math.inf)
        DAG.runtime_pq.push(item_mem, math.inf)

    for fun in DAG.workflow:
        fun._run_and_set_runtime()
        fun._set_cost()

    runtime = DAG.get_runtime()

    print('\nInfo: current runtime:%.2f.\n' %
          (runtime))


def max_config(DAG):
    runtime = DAG.get_runtime()

    while runtime > DAG.time_limit:
        # First get the function with the highest priority
        item = DAG.runtime_pq.pop()
        func = item['function']
        type = item['type']
        # Increase the resources until we meet the SLO
        # According to its type, choose different operation
        if type == 'cpu':

            print("Info: allocate cpu to function-%s by %.2f."
                  % (func.id, cpu_base))

            func.one_step_dealloc(-cpu_base, 0)

            # Push into the queue
            item = item = {'function': func, 'type': type}
            if func.curr_runtime < func.last_runtime:
                prioirty = func.last_runtime - func.curr_runtime
            else:
                prioirty = 0
            DAG.runtime_pq.push(item, prioirty)

        if type == 'memory':

            print("Info: allocate memory to function-%s by %d."
                  % (func.id, mem_base))

            func.one_step_dealloc(0, -mem_base)

            # Push into the queue
            item = item = {'function': func, 'type': type}
            if func.curr_runtime < func.last_runtime:
                prioirty = func.last_runtime - func.curr_runtime
            else:
                prioirty = 0
            DAG.runtime_pq.push(item, prioirty)

        runtime = DAG.get_runtime()
        print('Info: current runtime: %.2f.' % (runtime))
        update(DAG)

    print("\nInfo: after max_config, current configuration:\n")

    for func in DAG.workflow:
        print("function-%s of image-%s, with cpu:%.2f and memory:%d."
              % (func.id, func.image_id, func.cpu_alloc, func.mem_alloc))

    runtime = DAG.get_runtime()
    print("Info: current runtime: %.2f" % (runtime))


def init_cost_pq(DAG):
    # Define the element in the cost pq to be {'function': xxx, 'type': xxx}
    for func in DAG.workflow:
        item_cpu = {'function': func, 'type': 'cpu', 'trial': _trial_}
        item_mem = {'function': func, 'type': 'memory', 'trial': _trial_}

        DAG.cost_pq.push(item_cpu, math.inf)
        DAG.cost_pq.push(item_mem, math.inf)

    cost = DAG.get_cost()

    print('\nInfo: Cost_pq has been initialized. Current cost is %.2f.\n' % (cost))


def min_cost(DAG, cpu_alloc=one_step_cpu, mem_alloc=one_step_mem):
    print('Info: Min_cost config starts\n')
    last_cost = DAG.get_cost()
    last_runtime = DAG.get_runtime()

    while DAG.cost_pq.notEmpty():

        # First get the function with the highest priority
        item = DAG.cost_pq.pop()
        func = item['function']
        type = item['type']
        trial = item['trial']

        # According to its type, choose different operation
        # If slo isn't meet after the deallocation,
        # restore the configuration
        # and the function won't come back to the queue again
        if type == 'cpu':

            print("Info: try to deallocate cpu from function-%s by %.2f."
                  % (func.id, cpu_alloc))

            if func.cpu_alloc > cpu_alloc:
                func.one_step_dealloc(cpu_alloc, 0)
            else:
                continue

            cost = DAG.get_cost()
            runtime = DAG.get_runtime()

            # Set two trials if performance doesn't meet expectations
            if runtime > DAG.time_limit:
                print("Warn: long runtime. (runtime: %.2f)" %
                      (runtime))
                update(DAG)
                cnt = _trial_
                while runtime > DAG.time_limit and cnt >= 0:
                    func.one_step_dealloc(-cpu_alloc, 0)
                    runtime = DAG.get_runtime()
                    update(DAG)
                    cnt -= 1
                if trial > 0:
                    trial -= 1
                    item = {'function': func, 'type': type, 'trial': trial}
                    priority = 0
                    DAG.cost_pq.push(item, priority)
                else:
                    print("Info: function-%d type-%s out of queue." %
                          (func.id, type))
                    continue

            elif cost > last_cost*(1+error):
                print("Warn: heavy cost. (cost: %.2f)" %
                      (cost))
                update(DAG)

                func.one_step_dealloc(-cpu_alloc, 0)
                cost = DAG.get_cost()
                update(DAG)

                print('Info: current cost: %.2f.' % (cost))

                if trial > 0:
                    trial -= 1
                    item = {'function': func, 'type': type, 'trial': trial}
                    priority = 0
                    DAG.cost_pq.push(item, priority)
                else:
                    print("Info: function-%d type-%s out of queue." %
                          (func.id, type))
                    continue
            else:
                print('Info: complete. current cost: %.2f' % (cost))
                trial = _trial_
                # Put in queue
                item = {'function': func, 'type': type, 'trial': trial}
                if cost < last_cost:
                    priority = last_cost - cost
                else:
                    priority = 0
                DAG.cost_pq.push(item, priority)
                last_cost = cost
                last_runtime = runtime
                update(DAG)

        if type == 'memory':

            print("Info: try to deallocate mem from function-%s by %.2f."
                  % (func.id, mem_alloc))

            if func.mem_alloc > mem_alloc:
                func.one_step_dealloc(0, mem_alloc)
            else:
                continue

            cost = DAG.get_cost()
            runtime = DAG.get_runtime()

            # Set two trials if performance doesn't meet expectations
            if runtime > DAG.time_limit:
                print("Warn: long runtime. (runtime: %.2f)" %
                      (runtime))
                update(DAG)
                cnt = _trial_
                while runtime > DAG.time_limit and cnt >= 0:
                    func.one_step_dealloc(0, -mem_alloc)
                    runtime = DAG.get_runtime()
                    update(DAG)
                    cnt -= 1

                if trial > 0:
                    trial -= 1
                    item = {'function': func, 'type': type, 'trial': trial}
                    priority = 0
                    DAG.cost_pq.push(item, priority)
                else:
                    print("Info: function-%d type-%s out of queue." %
                          (func.id, type))
                    continue

            elif cost > last_cost*(1+error):
                print("Warn: heavy cost. (cost: %.2f)" %
                      (cost))
                update(DAG)

                func.one_step_dealloc(0, -mem_alloc)
                cost = DAG.get_cost()
                update(DAG)
                print('Info: current cost: %.2f.' % (cost))

                if trial > 0:
                    trial -= 1
                    item = {'function': func, 'type': type, 'trial': trial}
                    priority = 0
                    DAG.cost_pq.push(item, priority)
                else:
                    print("Info: function-%d type-%s out of queue." %
                          (func.id, type))
                    continue
            else:
                print('Info: complete. current cost: %.2f' % (cost))
                trial = _trial_
                # Put in queue
                item = {'function': func, 'type': type, 'trial': trial}
                if cost < last_cost:
                    priority = last_cost - cost
                else:
                    priority = 0
                DAG.cost_pq.push(item, priority)
                last_cost = cost
                last_runtime = runtime
                update(DAG)

    print("\nInfo: after min_cost, current configuration:\n")
    for func in DAG.workflow:
        print("function-%s of image-%s, with cpu:%.2f and memory:%d."
              % (func.id, func.image_id, func.cpu_alloc, func.mem_alloc))

    print("\nInfo: current cost is %.2f." % (last_cost))
    print("Info: current runtime: %.2f" % (last_runtime))
    return 'success'


def update(DAG):
    for i in range(0, len(DAG.workflow)):
        function = result['function'][i]
        container = DAG.workflow[i]
        function['cpu'].append(container.cpu_alloc)
        function['mem'].append(container.mem_alloc)

    result['runtime'].append(DAG.get_runtime())
    result['cost'].append(DAG.get_cost())


def upload():
    function = result['function']
    for i in range(0, len(function)):
        cpu = np.array(function[i]['cpu'])
        mem = np.array(function[i]['mem'])
        np.savetxt(f'results/function-{i}-cpu.yaml', cpu, fmt='%.2f')
        np.savetxt(f'results/function-{i}-mem.yaml', mem, fmt='%d')

    runtime = np.array(result['runtime'])
    cost = np.array(result['cost'])
    np.savetxt(f'results/runtime.yaml', runtime, fmt='%.2f')
    np.savetxt(f'results/cost.yaml', cost, fmt='%.2f')


def PQ_optimization(images, slo):

    print("Initializing workflow...\n")
    DAG = Workflow(images, slo)
    update(DAG)

    init_runtime_pq(DAG)
    max_config(DAG)
    init_cost_pq(DAG)
    res = min_cost(DAG)

    if res == 'Error':
        print("\nConfiguration failed!")
    else:
        print("\nConfiguration completed!")


if __name__ == '__main__':
    # Get configuration
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='config file', required=True)

    args = parser.parse_args()

    config_file = args.config
    with open(config_file, 'r', encoding='utf-8') as f:
        cfgs = yaml.safe_load(f)

    slo = cfgs['slo']
    image_names = []
    for ele in cfgs['images']:
        image_names.append(f'{ele["name"]}:{ele["tag"]}')

    result['function'] = []
    for i in range(0, len(image_names)):
        function = {}
        function['cpu'] = []
        function['mem'] = []
        function['runtime'] = []
        result['function'].append(function)

    result['runtime'] = []
    result['cost'] = []

    PQ_optimization(image_names, slo)

    upload()
