import channel
import math
import itertools
import matplotlib.pyplot as plt
import string
import sys
import threading

class Event(object):
    """
    In Lamport's paper, there are three events that can occur.

    1. A local event
    2. A message sending
    3. A message receiving

    All three of these events are implemented below and can be sent to the
    shower thread for showing.
    """
    pass

class Local(Event):
    def __init__(self, timestamp, owner):
        self.timestamp = timestamp
        self.owner     = owner

    def __str__(self):
        return " {} ".format(self.owner)

    def __repr__(self):
        return "Local({}, {})".format(self.timestamp, self.owner)

class Sent(Event):
    def __init__(self, timestamp, src, dst):
        self.timestamp = timestamp
        self.src       = src
        self.dst       = dst
        self.owner     = src

    def __str__(self):
        return "<{}>".format(self.dst)

    def __repr__(self):
        return "Sent({}, {}, {})".format(self.timestamp, self.src, self.dst)

class Received(Event):
    def __init__(self, timestamp, src, dst):
        self.timestamp = timestamp
        self.src       = src
        self.dst       = dst
        self.owner     = dst

    def __str__(self):
        return "({})".format(self.src)

    def __repr__(self):
        return "Received({}, {}, {})".format(self.timestamp, self.src, self.dst)

class Clock_i(object):
    def __init__(self, i, channels, shower_tx):
        """
        `Clock(i, channels, shower_tx)` instantiates a clock for thread i;
        every thread i in Lamport's paper is assigned a clock (C_i or Clock_i).
        `channels` is a dictionary from thread id's to bidirectional channels.
        `shower_tx` is the sending end of a channel to the showing thread.
        """
        self.i         = i
        self.channels  = channels
        self.shower_tx    = shower_tx
        self.timestamp = 0

    def local(self):
        self.shower_tx.send(Local(self.timestamp, self.i))
        self.timestamp += 1

    def send(self, dst):
        self.shower_tx.send(Sent(self.timestamp, self.i, dst))
        (tx, _) = self.channels[dst]
        tx.send(self.timestamp)
        self.timestamp += 1

    def recv(self, src):
        (_, rx) = self.channels[src]
        self.timestamp = max(self.timestamp, rx.recv() + 1)
        self.shower_tx.send(Received(self.timestamp, src, self.i))
        self.timestamp += 1

    def done_(self):
        self.shower_tx.send(None)

def wind(fs, plotname="clock.svg"):
    """
    `wind(fs)` winds the clock and spawns a thread for each function `f` in
    `fs` which is of type `Clock_i -> ()`. `wind` returns the showing function
    which you can call to plot the clock.
    """
    num_threads = len(fs)
    ids = range(num_threads)
    (shower_tx, shower_rx) = channel.channel()
    channels = {i: {} for i in ids}

    for (i, j) in itertools.combinations(ids, 2):
        (chan0, chan1) = channel.bichannel()
        channels[i][j] = chan0
        channels[j][i] = chan1

    for (i, f) in enumerate(fs):
        def ticktock(f, clock):
            f(clock)
            clock.done_()

        clock = Clock_i(i, channels[i], shower_tx.copy())
        threading.Thread(target=ticktock, args=(f, clock)).start()

    return lambda: plot(num_threads, shower_rx, plotname)

def get_events(num_threads, shower_rx):
    num_done = [0]

    def more(event):
        if event is None:
            num_done[0] += 1
        return num_threads != num_done[0]

    events = itertools.takewhile(more, shower_rx.iter())
    events = filter(lambda e: e is not None, events)
    return list(events)

def plot(num_threads, shower_rx, plotname):
    events = get_events(num_threads, shower_rx)

    if len(events) == 0:
        plt.axis("off")
        plt.savefig(plotname, bbox_inches="tight")
        return

    events = sorted(events, key=lambda e: e.timestamp)
    max_timestamp = events[-1].timestamp

    # horizontal lines
    for i in range(max_timestamp):
        plt.plot([0, num_threads - 1], [i + 0.5, i + 0.5], "k--")

    # vertical lines
    for i in range(num_threads):
        plt.plot([i, i], [-0.5, max_timestamp + 0.5], "k")

    # thread labels
    for i in range(num_threads):
        plt.text(i, max_timestamp + 2, "process ${}$".format(string.letters[i]), rotation="vertical", horizontalalignment="center")

    # event labels
    for i in range(num_threads):
        for (j, e) in enumerate(filter(lambda e: e.owner == i, events)):
            plt.text(e.owner - 0.1, e.timestamp, "${}_{}$".format(string.letters[i], j))

    # events
    while len(events) > 0:
        e = events.pop(0)

        if type(e) is Local:
            plt.scatter([e.owner], [e.timestamp], c="k")
        elif type(e) is Sent:
            s = e
            (x0, y0) = (s.owner, s.timestamp)
            r = next(e for e in events if type(e) is Received and e.src == s.src)
            (x1, y1)  = (r.owner, r.timestamp)
            plt.scatter([x0, x1], [y0, y1], c="k")
            plt.plot([x0, x1], [y0, y1])
            events.remove(r)
        else:
            pass

    plt.axis("off")
    plt.savefig(plotname, bbox_inches="tight")
