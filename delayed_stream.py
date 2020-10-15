import time

import multiprocessing as mp

def _producer(stream, q):
    for item in stream:
        q.put((time.time(), item))

def delayed_stream(iterable, delay_seconds=0):
    """Iterable wrapper that delayed consumption by delay_seconds."""
    q = mp.Queue()
    producer = mp.Process(target=_producer, args=(iterable, q))
    p = mp.Process(target=_producer, args=(iterable, q))
    p.start()
    while True:
        timestamp, item = q.get()
        age = time.time() - timestamp
        if age < delay_seconds:
            time.sleep(delay_seconds - age)
        yield item


if __name__ == '__main__':
    def slow_test_stream():
        for i in range(100):
            yield i
        for i in range(10):
            yield i + 100
            time.sleep(0.5)
        for i in range(10):
            yield i + 110


    slow_stream = slow_test_stream()
    delayed_stream = delayed_stream(slow_stream, delay_seconds=7)
    for item in delayed_stream:
        print(item)

