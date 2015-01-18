import threading

class AQueue(object):
    """Asynchronous Queue"""
    def __init__(self):
        self.lock           = threading.Lock()
        self.data_available = threading.Condition(self.lock)
        self.q              = []

    def __str__(self):
        with self.lock:
            return str(self.q)

    def push(self, x):
        with self.lock:
            self.q.append(x)
            self.data_available.notify()

    def pop(self):
        with self.lock:
            while len(self.q) <= 0:
                self.data_available.wait()
            return self.q.pop(0)

    def iter(self):
        while True:
            yield self.pop()
