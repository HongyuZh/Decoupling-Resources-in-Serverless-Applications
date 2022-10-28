import math
import time
import logging

logging.basicConfig(level=logging.INFO)


def func(n):
    for j in range(0,100):
        for i in range(0, 2*n):
            sin_i = math.sin(i)
            cos_i = math.cos(i)
            sqrt_i = math.sqrt(i)

if __name__ == '__main__':
    start_t = time.perf_counter()

    func(10000)

    end_t = time.perf_counter()
    elapsed_time = int(1000 * (end_t - start_t))

    logging.info(elapsed_time)
