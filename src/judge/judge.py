import socket
import argparse
import time
import json
import contextlib
import network

from typing import Any, Optional, Callable

PlayerInput = Any

class EnvironmentBase:
    """
    Concrete environments should subclass these, implementing ``reset``,
    ``next_player``, ``observation``, ``read_player_input`` and ``step``.

    A note on observations: there is a reserved string: "~~~END~~~" (in its own
    line), that is used to signal the end of the game. Environments must not
    use this in observations.
    """

    def __init__(self, num_players: int):
        self._num_players = num_players

    def reset(self) -> str:
        raise NotImplementedError()

    def next_player(self, current_player: Optional[int]) -> Optional[int]:
        """
        Calculate the index of the next player, return ``None`` if the game is
        over. ``current_player`` is ``None`` at the beginning, otherwise
        contains the current player index.
        """
        raise NotImplementedError()

    def observation(self, current_player: int) -> str:
        """
        Observation to be sent to the current player

        Can be a multiline string, in which case lines should be separarated by
        "\n"s. The final newline will be appended.
        """
        raise NotImplementedError()

    def read_player_input(
            self, read_line: Callable[[], str]) -> Optional[PlayerInput]:
        """
        Read and optionally parse/validate player input.

        Should take minimal time: player reply timeout is based on the timing
        of this function.

        Returns ``None`` on invalid player input.

        ``read_line`` returns one line of player input (without the ending
        newline, but check ``client_bridge.py`` to be sure).
        """
        raise NotImplementedError()

    def invalid_player_input(self, current_player: int) -> None:
        """
        Handle invalid player input.

        Default is to do nothing.

        Note that timeout also counts as invalid input.
        """

    def step(self, current_player: int, player_input: PlayerInput) -> None:
        """
        Apply player action.
        """
        raise NotImplementedError()

    def get_scores(self) -> list[int | float]:
        """
        Return the scores of the players. Called after the end of the game.
        """
        raise NotImplementedError()

    @property
    def num_players(self):
        return self._num_players

class EnvironmentRunner:

    def __init__(self,
                 environment: EnvironmentBase,
                 step_timeout: float,
                 connection_timeout: float,
                 client_addresses: Optional[list[str]] = None):
        self.env = environment
        self.step_timeout = step_timeout
        if client_addresses is not None:
            assert self.env.num_players == len(client_addresses), \
                    'Wrong number of clients for this environment.'
        # Wait for players to connect
        server_socket = socket.create_server(('', network.JUDGE_PORT))
        server_socket.settimeout(connection_timeout)
        server_socket.listen(self.env.num_players)
        clients = {}  # Is used when addresses are given
        client_sockets = []  # Is used when addresses are not given
        print('Waiting for players to connect...')
        for _ in range(self.env.num_players):
            try:
                (clientsocket, address) = server_socket.accept()
            except TimeoutError:
                print('Warning: connection timed out. May not have '
                      'enough players.')
                break
            clientsocket.settimeout(self.step_timeout)
            address, _port = address
            if client_addresses and address in clients:
                raise RuntimeError(
                    f'Multiple connections from the same address: {address}')
            clients[address] = clientsocket
            client_sockets.append(clientsocket)
            print('Player connected from', address)
        if client_addresses is not None:
            del client_sockets  # We will use `clients`
            if not set(clients.keys()).issubset(client_addresses):
                raise RuntimeError(
                    'Got invalid connections: '
                    f'{set(clients.keys()) - set(client_addresses)}')
            client_sockets = []
            for caddr in client_addresses:
                if caddr in clients:
                    client_sockets.append(clients[caddr])
                else:
                    print(f'No connections from {caddr}.')
                    client_sockets.append(None)
        else:
            # client_sockets = list(clients.values())
            client_sockets += [None] * (self.env.num_players - len(clients))
        self.clients = client_sockets
        server_socket.close()

    def run(self) -> list[int | float]:
        print('Started the run.')
        self._send_initial_observations()
        current_player: Optional[int] = None
        while True:
            current_player = self.env.next_player(current_player)
            if current_player is None:
                break
            assert 0 <= current_player < self.env.num_players
            observation = self.env.observation(current_player)
            if not observation or observation[-1] != '\n':
                observation += '\n'
            self._send_observation(current_player, observation)
            try:
                tick = time.perf_counter()
                player_input = self.env.read_player_input(
                    lambda: self._read_from_client(current_player))
                tock = time.perf_counter()
                if tock - tick > self.step_timeout:
                    player_input = None
            except TimeoutError:
                player_input = None
            except network.NetworkError:
                player_input = None
            if player_input is None:
                self.env.invalid_player_input(current_player)
            else:
                self.env.step(current_player, player_input)
        self._signal_the_end()
        return self.env.get_scores()

    def _send_initial_observations(self) -> None:
        initial_obs = self.env.reset()
        if not initial_obs or initial_obs[-1] != '\n':
            initial_obs += '\n'
        print('Sending initial observation to all players.')
        for p in range(self.env.num_players):
            self._send_observation(p, initial_obs)

    def _signal_the_end(self) -> None:
        print('Run ends, sending the end signal to everyone...')
        for p in range(self.env.num_players):
            self._send_observation(p, '~~~END~~~\n')

    def _send_observation(self, current_player: int, observation: str):
        if self.clients[current_player] is None:
            # Not connected
            return
        try:
            network.send_data(self.clients[current_player], observation)
        except (TimeoutError, network.NetworkError):
            print(f'Failed to send to player {current_player}.')

    def _read_from_client(self, player_ind: int) -> str:
        if self.clients[player_ind] is None:
            raise network.NetworkError('Player not connected.')
        msg = network.recv_msg(self.clients[player_ind])
        assert msg['type'] == 'data', 'Control messages aren\'t supported yet.'
        return msg['data']

class App:
    """
    Class mainly for parsing arguments and writing results where it is expected
    """

    def __init__(self, environment_name: str):
        arguments = self._parse_args(environment_name)
        print(environment_name)
        self._replay_file_path = arguments.replay_file
        self._player_timeout = arguments.timeout
        self._connection_timeout = arguments.connection_timeout
        config_file_path = arguments.config_file
        self._output_file_path = arguments.output_file
        with open(config_file_path, 'r') as f:
            self._options = json.load(f)
        if 'num_players' in self._options:
            print('Warning: number of players specified in configuration file, '
                  'replacing it with command line argument value '
                  f'({self._options["num_players"]}->{arguments.num_players}).')
        self._options['num_players'] = arguments.num_players
        if arguments.client_addresses:
            self._client_addresses = arguments.client_addresses.split(';')
            assert (len(self._client_addresses)
                    == self._options['num_players']), \
                    'Number of client addresses must equal the number of ' \
                    'players.'
        else:
            self._client_addresses = None

    @staticmethod
    def _parse_args(environment_name: str) -> argparse.Namespace:
        parser = argparse.ArgumentParser(
            description=f'Judge program of the {environment_name} environment.')
        parser.add_argument(
            'config_file',
            type=str,
            default=None,
            help='Path to the environment config file.')
        parser.add_argument(
            'num_players',
            type=int,
            help='Number of players. Note that there is a maximum number for '
            'the different maps.')
        parser.add_argument(
            '--replay_file',
            type=str,
            default=None,
            help='Path to save replay file to. Optional, if omitted, no replay '
            'file is created.')
        parser.add_argument(
            '--output_file',
            type=str,
            help='Path to save the output file to. Optional.')
        parser.add_argument(
            '--timeout',
            type=float,
            default=1.,
            help='Timeout (in seconds) for the player responses. '
            'Default is 1.0 second.')
        parser.add_argument(
            '--connection_timeout',
            type=float,
            default=10,
            help='Timeout (in seconds) for player connections. '
            'Default is 10 second.')
        parser.add_argument(
            '--client_addresses',
            type=str,
            help='List of client addresses, separated by ";"s. The number '
            'of addresses must equal the number of players.')
        return parser.parse_args()

    @contextlib.contextmanager
    def replay_file(self):
        assert self._replay_file_path, 'No replay file path specified.'
        print(f'Saving replays to {self._replay_file_path}.')
        with open(self._replay_file_path, 'w') as f:
            yield f

    @property
    def create_replay(self):
        return bool(self._replay_file_path)

    def write_output(self, output):
        if self._output_file_path:
            print(f'Saving final scores to {self._output_file_path}.')
            with open(self._output_file_path, 'w') as f:
                json.dump(output, f)

    def run_environment(self, env: EnvironmentBase):
        runner = EnvironmentRunner(env, self._player_timeout,
                                   self._connection_timeout,
                                   self._client_addresses)
        return runner.run()

    @property
    def options(self):
        return self._options

    @property
    def player_timeout(self):
        return self._player_timeout
