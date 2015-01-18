import matplotlib.pyplot as plt
import channel
import itertools
import threading
import sys

class Local(object):
    def __init__(self, timestamp, src):
        self.timestamp = timestamp
        self.src = src

    def __str__(self):
        return " {} ".format(self.src)

    def __repr__(self):
        return "Local({}, {})".format(self.timestamp, self.src)

class Sent(object):
    def __init__(self, timestamp, src, dst):
        self.timestamp = timestamp
        self.src = src
        self.dst = dst

    def __str__(self):
        return "<{}>".format(self.dst)

    def __repr__(self):
        return "Sent({}, {}, {})".format(self.timestamp, self.src, self.dst)

class Received(object):
    def __init__(self, timestamp, src, dst):
        self.timestamp = timestamp
        self.src = src
        self.dst = dst

    def __str__(self):
        return "({})".format(self.src)

    def __repr__(self):
        return "Received({}, {}, {})".format(self.timestamp, self.src, self.dst)

class Arm(object):
    def __init__(self, name, channels, printer_tx):
        self.name = name
        self.channels = channels
        self.printer_tx = printer_tx
        self.timestamp = 0

    def local(self):
        self.printer_tx.send(Local(self.timestamp, self.name))
        self.timestamp += 1

    def send(self, dst):
        self.printer_tx.send(Sent(self.timestamp, self.name, dst))
        (tx, _) = self.channels[dst]
        tx.send(self.timestamp)
        self.timestamp += 1

    def recv(self, src):
        (_, rx) = self.channels[src]
        self.timestamp = max(self.timestamp, rx.recv() + 1)
        self.printer_tx.send(Received(self.timestamp, src, self.name))
        self.timestamp += 1

    def done(self):
        self.printer_tx.send(None)

def spawn(fs):
    num_threads = len(fs)
    ids = range(num_threads)
    (printer_tx, printer_rx) = channel.channel()
    channels = {i: {} for i in ids}

    for (i, j) in itertools.combinations(ids, 2):
        (chan0, chan1) = channel.bichannel()
        channels[i][j] = chan0
        channels[j][i] = chan1

    for (i, f) in enumerate(fs):
        arm = Arm(i, channels[i], printer_tx.copy())
        def wrapper(arm):
            f(arm)
            arm.done()
        threading.Thread(target=wrapper, args=(arm,)).start()

    return lambda: plotter(len(fs), printer_rx)

def get_events(num_threads, printer_rx):
    events = []
    num_done = 0

    for event in printer_rx.iter():
        if event is None:
            num_done += 1
            if num_threads == num_done:
                break
        else:
            events.append(event)

    return events

def plotter(num_threads, printer_rx):
    events = get_events(num_threads, printer_rx)
    m = max(events, key=lambda e: e.timestamp).timestamp


    events = sorted(events, key=lambda e: e.timestamp)
    while len(events) > 0:
        e = events.pop(0)
        if type(e) is Local:
            plt.scatter([e.src], [e.timestamp])
        elif type(e) is Sent:
            (x0, y0) = (e.src, e.timestamp)
            x = next(x for x in events if type(x) is Received and x.dst == e.dst)
            (x1, y1)  = (x.dst, x.timestamp)
            plt.scatter([x0, x1], [y0, y1])
            plt.plot([x0, x1], [y0, y1])
            events.remove(x)
        else:
            pass

    for i in range(m + 1):
        plt.plot([0, num_threads - 1], [i, i], "k--")

    for i in range(num_threads):
        plt.plot([i, i], [0, m], "k")

    plt.savefig("plot.svg")


def printer(num_threads, printer_rx):
    events = get_events(num_threads, printer_rx)
    m = max(events, key=lambda e: e.timestamp).timestamp
    print "   " + "".join(" {} ".format(i) for i in range(num_threads))

    for t in range(m + 1):
        print "{}: ".format(t),
        for i in range(num_threads):
            def matches(e, t, i):
                if type(e) is Local:
                    return e.timestamp == t and e.src == i
                elif type(e) is Sent:
                    return e.timestamp == t and e.src == i
                else:
                    return e.timestamp == t and e.dst == i

            x = next((e for e in events if matches(e, t, i)), None)
            if x is None:
                sys.stdout.write("   ")
            else:
                sys.stdout.write(str(x))

        print ""

