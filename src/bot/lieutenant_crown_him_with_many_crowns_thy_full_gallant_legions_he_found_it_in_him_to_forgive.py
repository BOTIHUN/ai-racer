import sys
import enum
import numpy as np

from typing import Optional, NamedTuple

class CellType(enum.Enum):
    NOT_VISIBLE = 3
    WALL = -1

class Player(NamedTuple):
    x: int
    y: int
    vel_x: int
    vel_y: int

    @property
    def pos(self) -> np.ndarray:
        return np.array([self.x, self.y])

    @property
    def vel(self) -> np.ndarray:
        return np.array([self.vel_x, self.vel_y])

class Circuit(NamedTuple):
    track_shape: tuple[int, int]
    num_players: int
    visibility_radius: int

class State(NamedTuple):
    circuit: Circuit
    visible_track: np.ndarray
    players: list[Player]
    agent: Player

def read_initial_observation() -> Circuit:
    H, W, num_players, visibility_radius = map(int, input().split())
    return Circuit((H, W), num_players, visibility_radius)

def read_observation(old_state: State) -> Optional[State]:
    line = input()
    if line == '~~~END~~~':
        return None
    posx, posy, velx, vely = map(int, line.split())
    agent = Player(posx, posy, velx, vely)
    players = []
    # this won't change
    circuit_data = old_state.circuit
    for _ in range(circuit_data.num_players):
        pposx, pposy = map(int, input().split())
        # Calculating the velocity from the old state is left as an exercise to
        # the reader.
        players.append(Player(pposx, pposy, 0, 0))
    visible_track = np.full(circuit_data.track_shape, CellType.WALL.value)
    for i in range(2 * circuit_data.visibility_radius + 1):
        line = [int(a) for a in input().split()]
        x = posx - circuit_data.visibility_radius + i
        if x < 0 or x >= circuit_data.track_shape[0]:
            continue
        y_start = posy - circuit_data.visibility_radius
        y_end = y_start + 2 * circuit_data.visibility_radius + 1
        if y_start < 0:
            line = line[-y_start:]
            y_start = 0
        if y_end > circuit_data.track_shape[1]:
            line = line[:-(y_end - circuit_data.track_shape[1])]
            y_end = circuit_data.track_shape[1]
        visible_track[x, y_start:y_end] = line
    # We can't risk it. Put walls everywhere we can't see. Just to be safe.
    visible_track[visible_track == CellType.NOT_VISIBLE.value] = (
        CellType.WALL.value)
    return old_state._replace(
        visible_track=visible_track, players=players, agent=agent)

def traversable(cell_value: int) -> bool:
    return cell_value >= 0

def valid_line(state: State, pos1: np.ndarray, pos2: np.ndarray) -> bool:
    track = state.visible_track
    if (np.any(pos1 < 0) or np.any(pos2 < 0) or np.any(pos1 >= track.shape)
            or np.any(pos2 >= track.shape)):
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
            if (not traversable(track[x, y_ceil])
                    and not traversable(track[x, y_floor])):
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
            if (not traversable(track[x_ceil, y])
                    and not traversable(track[x_floor, y])):
                return False
    return True

def calculate_move(rng: np.random.Generator, state: State) -> tuple[int, int]:
    self_pos = state.agent.pos

    def valid_move(next_move):
        return (valid_line(state, self_pos, next_move) and
                (np.all(next_move == self_pos)
                 or not any(np.all(next_move == p.pos) for p in state.players)))

    # thats how the center of the next movement can be computed
    new_center = self_pos + state.agent.vel
    next_move = new_center
    # the variable ``next_move`` is initialized as the center point if it
    # is valid, we stay there with a high probability
    if (np.any(next_move != self_pos) and valid_move(next_move)
            and rng.random() > 0.1):
        return (0, 0)
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
                        # the next movement is to stay still (maybe)
                        valid_stay = (i, j)
                    else:
                        # we store the movement as a valid movement
                        valid_moves.append((i, j))
        if valid_moves:
            # if there is a valid movement, try to step there
            return tuple(rng.choice(valid_moves))
        elif valid_stay is not None:
            # if the only one movement is equal to my actual position, we'd
            # rather stay there
            return valid_stay
        else:
            # if there is no valid movement, then close our eyes....
            print(
                'Not blind, just being brave! (No valid action found.)',
                file=sys.stderr)
            return (0, 0)

def main():
    circuit = read_initial_observation()
    state: Optional[State] = State(circuit, None, [], None)  # type: ignore
    rng = np.random.default_rng(seed=1)
    while True:
        assert state is not None
        state = read_observation(state)
        if state is None:
            return
        delta = calculate_move(rng, state)
        print(f'{delta[0]} {delta[1]}')

if __name__ == "__main__":
    main()
