import socket

class Net:
    def __init__(self, addr: str, port: int):
        self.addr = addr
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = True
        self.buffer_size = 1024
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
        
    def Recieve(self):
        try:
            self.response = self.socket.recv(self.buffer_size)
        except Exception as e:
            print(f'Exception during recieve {e}')
    def GetResponse(self):
        return self.response
    def __del__(self):
        self.socket.close()