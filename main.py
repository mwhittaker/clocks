import lamport

def f(arm):
    arm.send(1)
    arm.recv(1)
    arm.local()
    arm.recv(1)

def g(arm):
    arm.send(0)
    arm.send(2)
    arm.recv(0)
    arm.local()
    arm.send(2)
    arm.send(0)
    arm.local()
    arm.recv(2)

def h(arm):
    arm.local()
    arm.send(1)
    arm.recv(1)
    arm.recv(1)

def main():
    lamport.spawn([f, g, h])

if __name__ == "__main__":
    main()
