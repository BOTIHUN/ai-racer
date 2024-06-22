#!/usr/bin/env python
import os
import subprocess
import asyncio
import datetime
import threading
import socket
import argparse
import sys
import network

LOGGING = True

class Logger:

    def __init__(self, fname: str):
        self.f = open(fname, 'w')  # pylint: disable=consider-using-with
        self.lock = threading.Lock()

    def write_stdout(self, msg: str):
        with self.lock:
            self.f.write(
                f'{datetime.datetime.now().time().isoformat()} - stdout :: '
                f'{msg}\n')
            self.f.flush()

    def write_stderr(self, msg: str):
        with self.lock:
            self.f.write(
                f'{datetime.datetime.now().time().isoformat()} - stderr :: '
                f'{msg}\n')
            self.f.flush()

    def write_stdin(self, msg: str):
        with self.lock:
            self.f.write(
                f'{datetime.datetime.now().time().isoformat()} - stdin  :: '
                f'{msg}\n')
            self.f.flush()

    def close(self):
        with self.lock:
            self.f.close()

class SubmissionManager():

    def __init__(self, judge_address: str, exe_cmd: list[str]) -> None:
        if LOGGING:
            self.logger = Logger(
                'communication.'
                f'{datetime.datetime.now().strftime("%Y%m%d_%H%M%S.%f")[:-3]}'
                '.log')
        else:
            self.logger = None
        # Connect to judge
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((judge_address, network.JUDGE_PORT))
        # Start submitted program
        self.submission_process = subprocess.Popen(  # pylint: disable=R1732
            exe_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True)

    async def start(self):
        if LOGGING:
            task = asyncio.gather(
                asyncio.to_thread(self.read_stderr),
                asyncio.to_thread(self.read_stdout),
                asyncio.to_thread(self.listen_to_server))
        else:
            task = asyncio.gather(
                asyncio.to_thread(self.read_stdout),
                asyncio.to_thread(self.listen_to_server))
        await task

    def read_stdout(self):
        while True:
            # ``readline`` will return the ending newline, this is good when
            # the line is empty (i.e., it will return a string with the newline
            # character, and it will not quit the loop). At EOF, however, it
            # will return an empty string.
            line = self.submission_process.stdout.readline()
            if not line:
                break
            if LOGGING:
                self.logger.write_stdout(line[:-1])
            network.send_data(self.socket, line[:-1])

    def read_stderr(self):
        # stderr goes only to logging, this thread shouldn't have been
        # started otherwise
        assert LOGGING
        while True:
            line = self.submission_process.stderr.readline()
            if not line:
                break
            self.logger.write_stderr(line[:-1])

    def listen_to_server(self):
        try:
            while True:
                msg = network.recv_msg(self.socket)
                assert msg['type'] == 'data', \
                        f'{msg["type"]} messages aren\'t supported yet.'
                if LOGGING:
                    self.logger.write_stdin(msg['data'][:-1])
                self.submission_process.stdin.write(msg['data'])
                self.submission_process.stdin.flush()
        except network.NetworkError:
            pass  # Server terminated. Farewell.
        except BrokenPipeError:
            print('Error: can\'t write to client. Maybe it terminated?')

    def close(self) -> None:
        self.submission_process.terminate()
        if LOGGING:
            self.logger.close()

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=
        'A script that forwards bot standard input/output to the judge via '
        'the network.')
    parser.add_argument(
        'bot_exe',
        help='Path to the bot executable (must have executable or read '
        'permissions).')
    parser.add_argument(
        '--judge_address',
        type=str,
        default='localhost',
        help='Address of the judge system. Default is localhost.')
    return parser.parse_args()

def get_execute_command(fname: str) -> list[str]:
    """
    Return the command to execute the bot
    """
    if fname.endswith('.py'):
        return ['python', '-u', fname]
    if fname.endswith('.mjs'):
        return ['node', fname]
    if os.path.splitext(fname)[1] == '':
        return [fname]
    print('Error: unknown filetype. Exiting.', file=sys.stderr)
    return []

def main():
    args = parse_args()
    cmd = get_execute_command(args.bot_exe)
    if not cmd:
        return
    manager = SubmissionManager(args.judge_address, cmd)
    try:
        asyncio.run(manager.start())
    except KeyboardInterrupt:
        manager.close()
        print('Received keyboard interrupt. Bye.')

if __name__ == "__main__":
    main()
