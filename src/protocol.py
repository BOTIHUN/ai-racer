from judge.network import *
import socket

class Protocol:
    def __init__(self, addr: str, port: int):
        self.addr = addr
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False

    def __del__(self):
        self.socket.close()

    def Connect(self):
        self.running = True
        print(f'Trying to connect to {self.addr}:{self.port}')
        while self.running:
            try:
                self.socket.connect((self.addr, self.port))
                print(f'Connected to {self.addr}:{self.port}')
                self.running = False
            except Exception as e:
                continue
    def InitialParameters(self) -> Jsonable:
        print('Waiting to recieve the initial message ...')
        return recv_msg(self.socket)["data"]
    