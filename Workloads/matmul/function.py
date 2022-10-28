import logging
import time

import numpy as np

logging.basicConfig(level=logging.INFO)


def func():
    for n in range(0, 200):
        A = np.random.rand(n, n)
        B = np.random.rand(n, n)
        np.matmul(A, B)


if __name__ == '__main__':
    start_t = time.perf_counter()

    func()

    end_t = time.perf_counter()
    elapsed_time = int(1000 * (end_t - start_t))

    logging.info(elapsed_time)
