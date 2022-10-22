import os 
import docker
import time

client = docker.from_env()
image_name = "pyaes"

slo = 33000
trail = 5
cpu = 5
memory = 256
# define input

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

def Bs_cpu(cpu,trail,slo):
    cpu_l = 0
    cpu_r = cpu
    cpu_m = 0
    execution_time = slo + 1
    execution_cnt = 0
    while execution_time > slo or execution_cnt < trail:
        if execution_time > slo:
            cpu_l = cpu_m
        else:
            cpu_r = cpu_m
        cpu_m = (cpu_l + cpu_r) / 2
        # define the setup
        
        container = client.containers.run(image_name, detach=True, cpu_period=100000, cpu_quota=int(100000*cpu_m), memswap_limit=-1)
                                          
        container_name = container.short_id 

        if container_name == "null":
            execution_time = slo + 1

        for i in range(1):
            container = client.containers.get(container_name)
            container.restart()
        wait_complete()

        container = client.containers.get(container_name)
        logs = str(container.logs(), encoding='utf-8').strip().split('\n')
        print(logs)
        if container_name != 'null':
            execution_time = int(logs[0].split(':')[-1])
        execution_cnt += 1
    return cpu_m

def Bs_memory(trail,slo,memory):
    memory_l = 6
    memory_r = memory
    memory_m = 6
    execution_time = slo + 1
    execution_cnt = 0
    while execution_time > slo or execution_cnt < trail:
        if execution_time > slo:
            memory_l = memory_m
        else:
            memory_r = memory_m
        memory_m = (memory_l + memory_r) / 2
       
        # define the setup

        container = client.containers.run(image_name, detach=True, mem_limit=f'{memory_m}M', memswap_limit=-1)
                                          
        container_name = container.short_id 

        if container_name == "null":
            execution_time = slo + 1

        for i in range(1):
            container = client.containers.get(container_name)
            container.restart()
        wait_complete()

        container = client.containers.get(container_name)
        logs = str(container.logs(), encoding='utf-8').strip().split('\n')
        print(logs)
        if container_name != 'null':
            execution_time = int(logs[0].split(':')[-1])
        execution_cnt += 1
    return memory_m

if __name__ == '__main__':
    CPU = Bs_cpu(cpu,trail,slo)
    print(CPU)
    MEM = Bs_memory(trail,slo,memory)
    print(MEM)
