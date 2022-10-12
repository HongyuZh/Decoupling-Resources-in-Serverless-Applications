import logging
import time

from numpy import linalg, matrix, random

logging.basicConfig(level=logging.INFO)


def linpack(n):
    # LINPACK benchmarks
    ops = (2.0 * n) * n * n / 3.0 + (2.0 * n) * n

    # Create AxA array of random numbers -0.5 to 0.5
    A = random.random_sample((n, n)) - 0.5
    B = A.sum(axis=1)

    # Convert to matrices
    A = matrix(A)
    B = matrix(B.reshape((n, 1)))

    # Ax = B
    x = linalg.solve(A, B)


def func():
    for i in range(1000):
        linpack(i)


if __name__ == '__main__':
    start_t = time.perf_counter()

    func()

    end_t = time.perf_counter()
    elapsed_time = int(1000 * (end_t - start_t))

    logging.info(elapsed_time)
