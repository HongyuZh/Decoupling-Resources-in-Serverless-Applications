import math
from time import time


def float_operations(n):
    start = time()
    for i in range(0, n):
        sin_i = math.sin(i)
        cos_i = math.cos(i)
        sqrt_i = math.sqrt(i)
    latency = time() - start
    return latency


def func(n):
    result = float_operations(n)
    return result


if __name__ == '__main__':
    latency = 0

    for i in range(0, 10000):
        latency += func(i)

    print("Done! The latency is: {}".format(latency))