import argparse
import time

import docker
import numpy as np

client = docker.from_env()
image_name = ''


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


def configure(alloc):
    container_name = []

    # create a number of containers according to the allocation plan
    for i in range(len(alloc)):
        container = client.containers.run(image_name,
                                          detach=True,
                                          mem_limit=f'{alloc[i][1]}M',
                                          cpu_period=100000,
                                          cpu_quota=int(alloc[i][0] * 100000))

        container_name.append(container.short_id)

    wait_complete()
    return container_name


def experiment(container_name, cnt, alloc):
    result = np.zeros((cnt + 1, len(alloc)))

    # repeat the experiment according to the given "cnt"
    for i in range(cnt):
        for j in range(len(alloc)):
            # let runtime equal -1 if a "null" is detected
            if container_name[j] == "null":
                result[i][j] = -1
                continue

            wait_complete()

            # cmd = f"docker restart {container_name[j]}"
            # os.system(cmd)
            container = client.containers.get(container_name[j])
            container.restart()

    wait_complete()

    # get the results according to the `docker log`
    for j in range(len(alloc)):
        container = client.containers.get(container_name[j])
        # we get rid of the first log
        logs = str(container.logs(), encoding='utf-8').strip().split('\n')
        print(logs)

        if container_name[j] != 'null':
            for i in range(cnt + 1):
                result[i, j] = int(logs[i].split(':')[-1])

    np.savetxt(f'{image_name}.txt', result, fmt='%d')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', help='image name', required=True)
    parser.add_argument('-c', '--count', help='repeated times', required=True)

    args = parser.parse_args()

    # configure the function
    image_name = args.name
    cnt = int(args.count)

    # determine the allocation plan
    cpu_alloc = [1, 2, 4, 8, 16]
    m_alloc = [256, 128, 64, 32, 16]
    alloc = []

    for j in range(len(m_alloc)):
        for i in range(len(cpu_alloc)):
            alloc.append([cpu_alloc[i], m_alloc[j]])

    # avoid cold start
    # create the containers and get their names
    container_name = configure(alloc)

    # run the containers to get the execution time
    experiment(container_name, cnt, alloc)
