import aqueue
import itertools

class Sender(object):
    def __init__(self, aq):
        self.aq = aq

    def send(self, x):
        self.aq.push(x)

    def copy(self):
        return Sender(self.aq)

class Receiver(object):
    def __init__(self, aq):
        self.aq = aq

    def recv(self):
        return self.aq.pop()

    def iter(self):
        return self.aq.iter()

def channel():
    """Creates a new asynchronous channel, returning the sender/receiver halves."""
    aq = aqueue.AQueue()
    return (Sender(aq), Receiver(aq))

def bichannel():
    """
    Creates a new bidirectional asynchronous channel, returning a pair of
    sender/receiver halves.
    """
    (tx0, rx0) = channel()
    (tx1, rx1) = channel()
    return ((tx0, rx1), (tx1, rx0))
