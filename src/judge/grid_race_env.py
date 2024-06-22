import enum
import itertools
import sys
import numpy as np
import PIL.Image as Image

from typing import Optional, NamedTuple

class CellType(enum.Enum):
    GOAL = 100
    START = 1
    WALL = -1
    UNKNOWN = 2
    EMPTY = 0
    NOT_VISIBLE = 3

    def traversable(self) -> bool:
        return self.value >= 0

CellTypeVec = np.vectorize(CellType)

class InvalidMove(Exception):
    pass

Position = np.ndarray  # shape: (2,)

# Player {{{1 #
class Player(NamedTuple):
    ind: int
    pos: Position  # (vertical, horizontal) (directly indexes the arrays)
    vel: Position

class Observation(NamedTuple):
    agent_pos: Position
    agent_vel: Position
    track: np.ndarray
    players: list[Position]

class AiPlayer:

    def calculate_move(self, observation: Observation) -> Position:
        raise NotImplementedError()

class RandomPlayer(AiPlayer):

    def __init__(self, *args, circuit: 'Circuit', ai_seed: int = 0, **kwargs):
        super().__init__(*args, **kwargs)
        self._rng = np.random.default_rng(ai_seed)
        # We use the Circuit object for some calculations, not cheating really
        self.circuit = circuit

    def calculate_move(self, observation: Observation) -> Position:
        self_pos = observation.agent_pos

        def valid_move(next_move):
            return (
                self.circuit.valid_line(self_pos, next_move)
                and (np.all(next_move == self_pos) or not any(
                    np.all(next_move == pos) for pos in observation.players)))

        # thats how the center of the next movement can be computed
        new_center = self_pos + observation.agent_vel
        next_move = new_center
        # the variable ``next_move`` is initialized as the center point if it
        # is valid, we stay there with a high probability
        if (np.any(next_move != self_pos) and valid_move(next_move)
                and self._rng.random() > 0.1):
            return np.array([0, 0])
        else:
            # the center point is not valid or we want to change with a small
            # probability
            valid_moves = []
            valid_stay = None
            for i in range(-1, 2):
                for j in range(-1, 2):
                    next_move = new_center + np.array([i, j])
                    # if the movement is valid (the whole line has to be valid)
                    if valid_move(next_move):
                        if np.all(self_pos == next_move):
                            # we store the movement as a valid movement
                            valid_stay = np.array([i, j])
                        else:
                            # the next movement is me
                            valid_moves.append(np.array([i, j]))
            if valid_moves:
                # if there is a valid movement, try to step there, if it not
                # equal with my actual position
                return self._rng.choice(valid_moves)
            elif valid_stay is not None:
                # if the only one movement is equal to my actual position, we
                # rather stay there
                return valid_stay
            else:
                # if there is no valid movement, then close our eyes....
                print(
                    'Not blind, just being brave! (No valid action found.)',
                    file=sys.stderr)
                return np.array([0, 0])

# 1}}} #

# Circuit {{{1 #
class Circuit:

    def __init__(self) -> None:
        self.players: list[Player] = []
        self.track, self.start = self.initialise_track()
        self.track.flags.writeable = False
        # ``laps`` is not actually used anywhere
        # self.laps: int = params['laps']
        assert np.all(
            [self.track[s[0], s[1]] == CellType.START for s in self.start])

    def get_player(self, pos) -> Optional[Player]:
        for p in self.players:
            if np.all(p.pos == pos):
                return p
        return None

    def move_player(self, player: int, how: Position | AiPlayer) -> None:
        if isinstance(how, AiPlayer):
            player_obj = self.players[player]
            assert not self.track.flags.writeable
            obs = Observation(
                agent_pos=player_obj.pos.copy(),
                agent_vel=player_obj.vel.copy(),
                track=self.track,
                players=[p.pos.copy() for p in self.players])
            delta = how.calculate_move(obs)
        else:
            delta = how
        self._move_player_directly(player, delta)

    def _move_player_directly(self, player: int, delta: Position) -> None:
        assert delta.shape == (2,)
        if not np.all(np.isin(delta, [-1, 0, 1])):
            raise InvalidMove(f'{self}: Invalid direction value.')
        player = self.players[player]
        new_pos = player.pos + player.vel + delta
        new_vel = player.vel + delta
        if not self.valid_line(player.pos, new_pos):
            raise InvalidMove(f'Player {player.ind} left the track.')
        player_at_target = self.get_player(new_pos)
        if player_at_target is not None and player_at_target is not player:
            raise InvalidMove(
                f'Player {player.ind} collided with {player_at_target}')
        player.pos[()] = new_pos
        player.vel[()] = new_vel

    def stop_player(self, player: int) -> None:
        self.players[player].vel[()] = 0

    def player_won(self, player: int) -> bool:
        return self._player_won(self.players[player])

    def _player_won(self, player: Player) -> bool:
        p = player.pos
        return self.track[p[0], p[1]] == CellType.GOAL

    def add_new_player(self):
        assert self.max_num_players > len(self.players), \
            'Too many players added'
        ind = len(self.players)
        self.players.append(Player(ind, np.array([-1, -1]), np.array([0, 0])))

    def reset_players(self):
        for s, p in zip(self.start, self.players):
            p.pos[()] = s
            p.vel[()] = [0, 0]

    def valid_line(self, pos1, pos2) -> bool:
        if (np.any(pos1 < 0) or np.any(pos2 < 0)
                or np.any(pos1 >= self.track.shape)
                or np.any(pos2 >= self.track.shape)):
            return False
        diff = pos2 - pos1
        # Go through the straight line connecting ``pos1`` and ``pos2``
        # cell-by-cell. Wall is blocking if either it is straight in the way or
        # there are two wall cells above/below each other and the line would go
        # "through" them.
        if diff[0] != 0:
            slope = diff[1] / diff[0]
            d = np.sign(diff[0])  # direction: left or right
            for i in range(abs(diff[0]) + 1):
                x = pos1[0] + i*d
                y = pos1[1] + i*slope*d
                y_ceil = np.ceil(y).astype(int)
                y_floor = np.floor(y).astype(int)
                if (not self.track[x, y_ceil].traversable()
                        and not self.track[x, y_floor].traversable()):
                    return False
        # Do the same, but examine two-cell-wall configurations when they are
        # side-by-side (east-west).
        if diff[1] != 0:
            slope = diff[0] / diff[1]
            d = np.sign(diff[1])  # direction: up or down
            for i in range(abs(diff[1]) + 1):
                x = pos1[0] + i*slope*d
                y = pos1[1] + i*d
                x_ceil = np.ceil(x).astype(int)
                x_floor = np.floor(x).astype(int)
                if (not self.track[x_ceil, y].traversable()
                        and not self.track[x_floor, y].traversable()):
                    return False
        return True

    def iter_players(self):
        players = itertools.cycle(self.players)
        # after all of them has won, there is no need to iterate, and it may
        # fall into an endless loop
        end_countdown = len(self.players)
        while True:
            next_player = next(players)
            if self._player_won(next_player):
                end_countdown -= 1
                if end_countdown <= 0:
                    return
                continue
            else:
                end_countdown = len(self.players)
                yield next_player

    @classmethod
    def initialise_track(cls) -> tuple[np.ndarray, np.ndarray]:
        raise NotImplementedError()

    @property
    def shape(self):
        return self.track.shape

    @property
    def max_num_players(self):
        return len(self.start)

    @property
    def num_players(self):
        return len(self.players)

class MinimalTrack(Circuit):

    @classmethod
    def initialise_track(cls) -> tuple[np.ndarray, np.ndarray]:
        # yapf: disable
        track = np.array([[-1, -1, -1, -1, -1, -1,  -1, -1],
                          [-1,  1,  0,  0,  2, -1,  -1, -1],
                          [-1,  1, -1,  0,  2, -1,  -1, -1],
                          [-1,  1, -1,  0,  2,  0, 100, -1],
                          [-1, -1, -1, -1, -1, -1,  -1, -1]])
        # yapf: enable
        track = CellTypeVec(track)
        start = np.array([[1, 1], [2, 1], [3, 1]])
        return track, start

class PlayableMap(Circuit):

    @classmethod
    def initialise_track(cls) -> tuple[np.ndarray, np.ndarray]:
        # yapf: disable
        track = np.array([[-1, -1, -1, -1, -1,  -1,  -1, -1],
                          [-1,  1,  0,  0,  2, 100, 100, -1],
                          [-1,  1,  0,  0,  2, 100, 100, -1],
                          [-1,  1,  0,  0,  2, 100, 100, -1],
                          [-1, -1, -1, -1, -1,  -1,  -1, -1]])
        # yapf: enable
        track = CellTypeVec(track)
        start = np.array([[1, 1], [2, 1], [3, 1]])
        return track, start

def load_track_from_file(fname: str) -> Circuit:
    img = Image.open(fname)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    im = np.asarray(img)
    COLOURS = np.array([
        [255, 0, 0],
        [255, 255, 255],
        [0, 255, 0],
        [0, 0, 255],
    ])
    ENUM_VALUES = np.array([-1, 0, 1, 100])
    i = np.all(
        im.reshape(-1, 3)[:, np.newaxis, :] == COLOURS[np.newaxis, :, :],
        axis=-1).nonzero()
    if np.any(i[0] != np.arange(len(i[0]))):
        raise ValueError(f'Image {fname} contains colours I cannot decipher.')
    track = ENUM_VALUES[i[1]].reshape(im.shape[:2])
    track = CellTypeVec(track)
    start = np.stack((track == CellType.START).nonzero()).T

    class LoadedCircuit(Circuit):

        @classmethod
        def initialise_track(cls) -> tuple[np.ndarray, np.ndarray]:
            return track, start

    return LoadedCircuit()

# 1}}} #

# vim:set et sw=4 ts=4 fdm=marker:
