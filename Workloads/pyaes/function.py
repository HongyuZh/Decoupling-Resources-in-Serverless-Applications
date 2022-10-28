import logging
import time
import random
import string
import pyaes


logging.basicConfig(level=logging.INFO)


def generate(length):
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for i in range(length))

def func():
    length_of_message = 300
    num_of_iterations = 300

    message = generate(length_of_message)

    # 128-bit key (16 bytes)
    KEY = b'\xa1\xf6%\x8c\x87}_\xcd\x89dHE8\xbf\xc9,'

    for loops in range(num_of_iterations):
        aes = pyaes.AESModeOfOperationCTR(KEY)
        ciphertext = aes.encrypt(message)

        aes = pyaes.AESModeOfOperationCTR(KEY)
        plaintext = aes.decrypt(ciphertext)
        aes = None


if __name__ == '__main__':
    start_t = time.perf_counter()

    func()

    end_t = time.perf_counter()
    elapsed_time = int(1000 * (end_t - start_t))

    logging.info(elapsed_time)
