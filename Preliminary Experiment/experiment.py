import numpy as np
import matplotlib.pyplot as plt
import os
import time

import matplotlib
matplotlib.use('Agg')

matplotlib.use('TKAgg')


def configure(alloc):
    container_name = []

    # create a number of containers according to the allocation plan

    for i in range(0, len(alloc)):
        try:
            cmd = "docker run -d -t " + " --cpus=" + \
                str(alloc[j][0]) + " -m " + \
                str(alloc[j][1])+"M" + " " + image_name
            print(cmd)
            output = os.popen(cmd)
            name = output.readlines()
            container_name.append(name[0])

        # if the execution fails, input "null" as the container's name

        except:
            print("couldn't start container in this condition \n")
            container_name.append('null')
            continue

    return container_name


def experiment(container_name, cnt, alloc):
    result = {}

    # repeat the experiment according to the given "cnt"

    for i in range(0, cnt):
        result['experiment_'+str(i)] = {}
        for j in range(0, len(alloc)):
            experiment_result = result['experiment_'+str(i)]

            # let runtime equals -1 if a "null" is detected

            if container_name[j] == "null":
                experiment_result[str(alloc[j])] = -1
                continue

            cmd = "docker restart " + container_name[j]

            # then perform the commands below:
            # at the same time, record the execution time

            start = time.perf_counter()
            os.system(cmd)
            end = time.perf_counter()

            # compute the overall runtime

            runtime = int(1000*(end-start))

            # store the result in "experiment_result"

            experiment_result[str(alloc[j])] = runtime

    data = [0]*len(alloc)

    # compute the average runtime

    for ele in result:
        for i in range(0, len(alloc)):
            data[i] += result[ele][str(alloc[i])]

    for i in range(0, len(data)):
        data[i] /= cnt

    return data


def heatplot(Xs, Ys, Zs):
    # copied from https://matplotlib.org/stable/gallery/images_contours_and_fields/image_annotated_heatmap.html
    # using this code to draw a heatplot

    Z = []
    for i in range(0, len(Ys)):
        Z.append(Zs[i*len(Xs): (i+1)*len(Xs)])

    data = np.array(Z)

    fig, ax = plt.subplots()
    im = ax.imshow(data)

    # Show all ticks and label them with the respective list entries

    ax.set_xticks(np.arange(len(Xs)))
    ax.set_yticks(np.arange(len(Ys)))
    plt.xlabel('cpu_alloc')
    plt.ylabel('m_alloc')

    # Rotate the tick labels and set their alignment
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right",
             rotation_mode="anchor")

    # Loop over data dimensions and create text annotations

    for i in range(len(Ys)):
        for j in range(len(Xs)):
            text = ax.text(j, i, data[i, j],
                           ha="center", va="center", color="w")

    ax.set_title("the Runtime of containers")
    fig.tight_layout()
    plt.savefig('EX2_plot.png', bbox_inches='tight')


if __name__ == '__main__':
    # configure the function

    image_name = "ex2"
    cnt = 1

    # determine the allocation plan

    cpu_alloc = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2, 3, 4]
    m_alloc = [2048, 1024, 768, 512, 256, 128]
    alloc = []

    for i in range(0, len(cpu_alloc)):
        for j in range(0, len(m_alloc)):
            alloc.append([cpu_alloc[i], m_alloc[j]])

    # create the containers and get their names

    container_name = configure(alloc)

    # run the containers to get the execution time

    data = experiment(container_name, cnt, alloc)

    # draw the heatplot using the data above

    heatplot(cpu_alloc, m_alloc, data)
