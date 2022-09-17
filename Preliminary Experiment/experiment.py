import os


def experiment(alloc, image_name, cnt, sudopassword):
    result = {}

    # repeat the experiment according to the given "cnt"

    for i in range(0, cnt):
        result['experiment_'+str(i)] = {}
        for j in range(0, len(alloc)):
            experiment_result = result['experiment_'+str(i)]

            # perform the commands below:
            # let runtime equals -1 if a failure is detected
            try:
                # here I run the image and get the container name stored in "container_name"
                cmd = "docker run -d -t " + image_name + \
                    " -m " + str(alloc[j][0]) + " --cpus=" + str(alloc[j][1])
                output = os.popen(cmd)
                container_name = output.readlines()[0]
                output.close()
            except:
                print("couldn't start container in this condition \n")
                result['experiment'+str(i)][str(alloc[j])] = str(-1)
                continue

            # then record the runtime
            # get the start time of the container

            # run the following sudo command to get the start time
            cmd = "sudo docker inspect --format='{{.State.StartedAt}}' " + \
                container_name

            # get the ouput as a file named "output"
            # then read this file to get a list named "start" which contains the start time of this container
            output = os.popen('echo %s|sudo -S %s' % (sudopassword, cmd))
            start = output.readlines()
            output.close()

            # convert the timing format into Unix timing
            cmd = "date -d '"+start[0]+"' +%s"
            output = os.popen(cmd)
            start = output.readlines()
            output.close()

            # follow the same pattern above
            # get the finish time

            cmd = "sudo docker inspect --format='{{.State.FinishedAt}}' " + \
                container_name

            output = os.popen('echo %s|sudo -S %s' % (sudopassword, cmd))
            end = output.readlines()
            output.close()

            cmd = "date -d '"+end[0]+"' +%s"
            output = os.popen(cmd)
            end = output.readlines()
            output.close()

            # compute the overall runtime
            runtime = int(end[0]) - int(start[0])

            # store the result in "experiment_result"

            experiment_result[str(alloc[j])] = str(runtime)

    return result


if __name__ == '__main__':
    # configure the function

    image_name = ""
    sudopassword = ""
    cnt = 1

    # first determine the allocation plan

    cpu_alloc = [0.25, 0.5, 0.75, 1, 1.25, 1.5, 1.75, 2]
    m_alloc = [128, 256, 512, 768, 1024, 2048]
    alloc = []

    for i in range(0, len(cpu_alloc)):
        for j in range(0, len(m_alloc)):
            alloc.append([cpu_alloc[i], m_alloc[j]])

    # print the outcome here
    print(experiment(alloc, image_name, cnt, sudopassword))
