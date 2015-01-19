import lamport

def f(clock):
    clock.send(1)
    clock.recv(1)
    clock.local()
    clock.recv(1)

def g(clock):
    clock.send(0)
    clock.send(2)
    clock.recv(0)
    clock.local()
    clock.send(2)
    clock.send(0)
    clock.local()
    clock.recv(2)

def h(clock):
    clock.local()
    clock.send(1)
    clock.recv(1)
    clock.recv(1)

def main():
    lamport.wind([f, g, h], "clock.png")()

if __name__ == "__main__":
    main()
