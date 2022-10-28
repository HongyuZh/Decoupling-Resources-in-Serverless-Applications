import argparse
import math

import numpy as np
import yaml
import os

from docker_container import *

_trial = 2
_failed = 2
error = 0.05
margin = 100

result = {}


def init_runtime_pq(DAG: Workflow):
    # Define the element in the runtime pq to be {'function': xxx, 'type': xxx}
    for func in DAG.workflow:

        item_cpu = {'function': func, 'type': 'cpu'}
        item_mem = {'function': func, 'type': 'memory'}

        DAG.runtime_pq.push(item_cpu, math.inf)
        DAG.runtime_pq.push(item_mem, math.inf)

    for func in DAG.workflow:
        func.update()
        print('Function-%s runtime: %.2fms.' % (func.id, func.curr_runtime))

    update(DAG)
    runtime = DAG.get_runtime()

    print('Runtime of the workflow: %.2fms.\n' %
          (runtime))


def max_config(DAG: Workflow):
    while DAG.get_runtime() > DAG.time_limit:
        # First get the function with the highest priority
        item = DAG.runtime_pq.pop()
        func = item['function']
        type = item['type']
        # Increase the resources until we meet the SLO
        # According to its type, choose different operation
        if type == 'cpu':
            print("\nAllocate cpu to function-%s by %.2f."
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
            print("\nAllocate memory to function-%s by %d."
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
        print('Current runtime of the workflow: %.2fms.' % (runtime))
        update(DAG)

    print("\nAfter max_config, current configuration:")

    for func in DAG.workflow:
        print("Function-%s of image-%s, with cpu:%.2f and memory:%d."
              % (func.id, func.image_id, func.cpu_alloc, func.mem_alloc))


def init_cost_pq(DAG: Workflow):
    # Define the element in the cost pq to be {'function': xxx, 'type': xxx}
    for func in DAG.workflow:
        item_cpu = {'function': func, 'type': 'cpu', 'trial': _trial}
        item_mem = {'function': func, 'type': 'memory', 'trial': _trial}

        DAG.cost_pq.push(item_cpu, math.inf)
        DAG.cost_pq.push(item_mem, math.inf)

    cost = DAG.get_cost()
    print('\nCost_pq has been initialized. Current cost is %.2f.\n' % (cost))


def min_cost(DAG: Workflow):
    print('Min_cost config starts\n')
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

            print("\nTry to deallocate cpu from function-%s by %.2f."
                  % (func.id, one_step_cpu))

            if func.cpu_alloc > one_step_cpu:
                func.one_step_dealloc(one_step_cpu, 0)
            else:
                continue

            update(DAG)
            cost = DAG.get_cost()
            runtime = DAG.get_runtime()

            # Set several trials if performance doesn't meet expectations
            if runtime > DAG.time_limit:
                print("Long runtime, retrive configuration. (runtime: %.2fms)" %
                      (runtime))

                cnt = _failed
                while runtime > DAG.time_limit and cnt > 0:
                    func.one_step_dealloc(-one_step_cpu, 0)
                    runtime = DAG.get_runtime()
                    print('Current runtime of the workflow: %.2f' % (runtime))
                    cnt -= 1
                    update(DAG)

                if trial > 0:
                    trial -= 1
                    item = {'function': func, 'type': type, 'trial': trial}
                    priority = 0
                    DAG.cost_pq.push(item, priority)
                else:
                    print("Put function-%d type-%s out of queue." %
                          (func.id, type))
                    continue
            elif cost > last_cost*(1+error):
                print("Heavy cost, retrive configuration. (cost: %.2f)" %
                      (cost))

                func.one_step_dealloc(-one_step_cpu, 0)
                cost = DAG.get_cost()
                print('Current cost: %.2f.' % (cost))
                update(DAG)

                if trial > 0:
                    trial -= 1
                    item = {'function': func, 'type': type, 'trial': trial}
                    priority = 0
                    DAG.cost_pq.push(item, priority)
                else:
                    print("Put function-%d type-%s out of queue." %
                          (func.id, type))
                    continue
            else:
                print('Complete. current cost: %.2f' % (cost))
                trial = _trial
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

        elif type == 'memory':

            print("\nTry to deallocate mem from function-%s by %.2f."
                  % (func.id, one_step_mem))

            if func.mem_alloc > one_step_mem:
                func.one_step_dealloc(0, one_step_mem)
            else:
                continue

            update(DAG)
            cost = DAG.get_cost()
            runtime = DAG.get_runtime()

            # Set two trials if performance doesn't meet expectations
            if runtime > DAG.time_limit:
                print("Long runtime, retrive configuration. (runtime: %.2fms)" %
                      (runtime))

                cnt = _failed
                while runtime > DAG.time_limit and cnt >= 0:
                    func.one_step_dealloc(0, -one_step_mem)
                    runtime = DAG.get_runtime()
                    print('Current runtime of the workflow: %.2f' % (runtime))
                    cnt -= 1
                    update(DAG)

                if trial > 0:
                    trial -= 1
                    item = {'function': func, 'type': type, 'trial': trial}
                    priority = 0
                    DAG.cost_pq.push(item, priority)
                else:
                    print("Put function-%d type-%s out of queue." %
                          (func.id, type))
                    continue

            elif cost > last_cost*(1+error):
                print("Heavy cost, retrive configuration. (cost: %.2f)" %
                      (cost))

                func.one_step_dealloc(0, -one_step_mem)
                cost = DAG.get_cost()
                print('Current cost: %.2f.' % (cost))
                update(DAG)
                last_cost = cost

                if trial > 0:
                    trial -= 1
                    item = {'function': func, 'type': type, 'trial': trial}
                    priority = 0
                    DAG.cost_pq.push(item, priority)
                else:
                    print("Put function-%d type-%s out of queue." %
                          (func.id, type))
                    continue
            else:
                print('Complete. current cost: %.2f' % (cost))
                trial = _trial
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

    print("\nAfter min_cost, current configuration:")
    for func in DAG.workflow:
        print("function-%s of image-%s, with cpu:%.2f and memory:%d."
              % (func.id, func.image_id, func.cpu_alloc, func.mem_alloc))

    print("\nCurrent cost is %.2f." % (last_cost))
    print("Current runtime: %.2f" % (last_runtime))


def update(DAG: Workflow):
    for i in range(0, len(DAG.workflow)):
        function = result['function'][i]
        item = DAG.workflow[i]
        function['cpu'].append(item.cpu_alloc)
        function['mem'].append(item.mem_alloc)

    result['runtime'].append(DAG.get_runtime())
    result['cost'].append(DAG.get_cost())


def upload():
    if not os.path.exists('results'):
        os.makedirs('results')

    function = result['function']
    for i in range(0, len(function)):
        cpu = np.array(function[i]['cpu'])
        mem = np.array(function[i]['mem'])
        np.savetxt(f'results/function-{i}-cpu.txt', cpu, fmt='%.2f')
        np.savetxt(f'results/function-{i}-mem.txt', mem, fmt='%d')

    runtime = np.array(result['runtime'])
    cost = np.array(result['cost'])
    np.savetxt(f'results/runtime.txt', runtime, fmt='%.2f')
    np.savetxt(f'results/cost.txt', cost, fmt='%.2f')


def PQ_optimization(images, slo):
    print("Initializing workflow...\n")
    DAG = Workflow(images, slo)
    update(DAG)

    init_runtime_pq(DAG)
    max_config(DAG)
    init_cost_pq(DAG)
    min_cost(DAG)

    print("\nConfiguration complete.")\

    for i in range(0, exe_times):
        for func in DAG.workflow:
            func.update()
        update(DAG)
        print(f'Execution {i} completed.')


if __name__ == '__main__':
    # Get configuration
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', help='config file', required=True)
    args = parser.parse_args()

    config_file = args.config
    with open(config_file, 'r', encoding='utf-8') as f:
        cfgs = yaml.safe_load(f)

    slo = cfgs['slo'] - margin
    image_names = []
    for ele in cfgs['images']:
        image_names.append(f'{ele["name"]}:{ele["tag"]}')
    global exe_times
    exe_times = cfgs['exe_times']

    result['function'] = []
    for i in range(0, len(image_names)):
        function = {}
        function['cpu'] = []
        function['mem'] = []
        result['function'].append(function)

    result['runtime'] = []
    result['cost'] = []

    PQ_optimization(image_names, slo)
    upload()
