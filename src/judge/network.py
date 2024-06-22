import socket
import json
import struct

from typing import Any

# won't use text based IO, because:
# "The socket must be in blocking mode; it can have a timeout, but the file
# object's internal buffer may end up in an inconsistent state if a timeout
# occurs."

Jsonable = Any  # anything JSON can dump

JUDGE_PORT = 10000

class NetworkError(Exception):
    pass

def send_msg(sock: socket.SocketType, msg: Jsonable) -> None:
    msg = json.dumps(msg, ensure_ascii=True).encode('ascii')
    msg_len = len(msg)
    msg_len = struct.pack('>i', msg_len)
    sock.sendall(msg_len + msg)

def recv_msg(sock: socket.SocketType) -> Jsonable:

    def read_until(size: int) -> bytes:
        try:
            read_count = 0
            bytes_read = []
            while read_count < size:
                b = sock.recv(min(size - read_count, 4096))
                if b == b'':
                    raise NetworkError('Socket is broken.')
                bytes_read.append(b)
                read_count += len(b)
            return b''.join(bytes_read)
        except ConnectionResetError as e:
            raise NetworkError(f'Connection reset: {e}') from e

    msg_len = read_until(4)
    msg_len, = struct.unpack('>i', msg_len)
    msg = read_until(msg_len)
    return json.loads(msg)

def send_data(sock: socket.SocketType, data: str) -> None:
    try:
        send_msg(sock, {'type': 'data', 'data': data})
    except (BrokenPipeError, OSError) as e:
        raise NetworkError('Failed to send data') from e

# May want to send control messages as well, such as request for shutdown/kill
