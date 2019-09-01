import time
import math

from scoop import futures

data = range(12)

def func(num):
    time.sleep(0.1)
    return num ** 2

if __name__ == "__main__":
    begin_time = time.time()

    res = list(futures.map(func, data))
    spent_time = math.ceil((time.time() - begin_time) * 1000)

    print(res)
    print("End at {} msec".format(spent_time))
