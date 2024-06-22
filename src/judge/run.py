import itertools
import numpy as np
import grid_race_env
import judge
import replay

from typing import Optional, Callable

class GridRaceEnv(judge.EnvironmentBase):

    INVALID_ACTION_PENALTY = 5

    def __init__(self,
                 num_players: int,
                 visibility_radius: int,
                 circuit: grid_race_env.Circuit,
                 max_turns: int = 500):
        self._num_players = num_players
        self.max_turns = max_turns
        self.visibility_radius = visibility_radius
        self.circuit = circuit
        for _ in range(num_players):
            self.circuit.add_new_player()

    def reset(self) -> str:
        self.circuit.reset_players()
        # score for not finishing is max turns + 1
        self.scores = [self.max_turns + 1] * self.num_players
        self.turns = 0
        self.penalties = [None for _ in range(self.num_players)]
        # extra player signalling end of turn
        self.players_iterator = itertools.cycle(range(self.num_players + 1))
        to_int = np.vectorize(lambda c: c.value)
        track_int = to_int(self.circuit.track)
        self.replay = replay.Replay(
            env_info=replay.EnvInfo(
                track=track_int.tolist(), num_players=self.num_players),
            states=[],
            steps=[])
        self.replay.states.append(self._save_state())
        return (f'{self.circuit.shape[0]} {self.circuit.shape[1]} '
                f'{self.num_players} {self.visibility_radius}')

    def _save_step(self, step: replay.PlayerStep) -> None:
        """
        Saves a step, and immediately saves the resulting state as well.
        """
        self.replay.steps.append(step)
        self.replay.states.append(self._save_state())

    def _save_state(self) -> replay.State:
        players = [
            replay.PlayerState(*p.pos.tolist(), *p.vel.tolist())
            for p in self.circuit.players
        ]
        return replay.State(turn=self.turns, players=players)

    def next_player(self, current_player: Optional[int]) -> Optional[int]:
        """
        Calculate the index of the next player, return ``None`` if the game is
        over. ``current_player`` is ``None`` at the beginning.
        """
        if current_player is None:
            # Should start with player #0
            assert next(self.players_iterator) == 0
            return 0
        while True:  # repeat until player is not in penalty
            # look for the next player
            for _ in range(self.num_players + 1):
                next_player = next(self.players_iterator)
                if next_player == self.num_players:
                    self.turns += 1
                    if self.turns >= self.max_turns:
                        print(f'Reached max turn limit ({self.turns}).')
                        return None
                    # skip the sentinel player indicating turn's end
                    continue
                if self.circuit.player_won(next_player):
                    # skip players who have already won
                    continue
                break
            else:
                # should be that all players have won
                assert all(
                    self.circuit.player_won(i) for i in range(self.num_players))
            assert next_player != self.num_players
            if self.penalties[next_player] is not None:
                if self.penalties[next_player] == 0:
                    self.penalties[next_player] = None
                    return next_player
                else:
                    self.penalties[next_player] -= 1
                    self._save_step(
                        replay.PlayerStep(
                            player_ind=next_player,
                            success=False,
                            status='Player is in penalty, skipping their turn.')
                    )
                    continue
            elif self.circuit.player_won(next_player):
                # No more active players
                assert all(
                    self.circuit.player_won(i) for i in range(self.num_players))
                return None
            else:
                return next_player

    def observation(self, current_player: int) -> str:
        """
        Observation to be sent to the current player

        Can be a multiline string, in which case lines should be separarated by
        "\n"s. The final newline will be appended.
        """
        current_player_obj = self.circuit.players[current_player]
        local_map = np.zeros(
            (2 * self.visibility_radius + 1, 2 * self.visibility_radius + 1),
            dtype=int)
        for r in range(2 * self.visibility_radius + 1):
            for c in range(2 * self.visibility_radius + 1):
                x = current_player_obj.pos[0] + r - self.visibility_radius
                y = current_player_obj.pos[1] + c - self.visibility_radius
                if (np.linalg.norm(
                        np.array([x, y]) - current_player_obj.pos, ord=2)
                        > self.visibility_radius):
                    local_map[r, c] = grid_race_env.CellType.NOT_VISIBLE.value
                elif (not (0 <= x < self.circuit.shape[0])
                      or not (0 <= y < self.circuit.shape[1])):
                    local_map[r, c] = grid_race_env.CellType.WALL.value
                else:
                    local_map[r, c] = self.circuit.track[x, y].value
        # TODO check this
        local_map_str = '\n'.join(
            ' '.join(map(str, line)) for line in local_map)
        player_pos = [f'{p.pos[0]} {p.pos[1]}' for p in self.circuit.players]
        current_player_info = (
            f'{current_player_obj.pos[0]} {current_player_obj.pos[1]} '
            f'{current_player_obj.vel[0]} {current_player_obj.vel[1]}')
        return (current_player_info + '\n' + '\n'.join(player_pos) + '\n'
                + local_map_str)

    def read_player_input(
            self, read_line: Callable[[], str]) -> Optional[judge.PlayerInput]:
        """
        Read and optionally parse/validate player input.

        Should take minimal time: player reply timeout is based on the timing
        of this function.

        Returns ``None`` on invalid player input.

        ``read_line`` returns one line of player input (without the ending
        newline, but check ``client_bridge.py`` to be sure).
        """
        line = read_line()
        try:
            dx, dy = map(int, line.split())
            return dx, dy
        except ValueError:
            return None

    def invalid_player_input(self, current_player: int) -> None:
        """
        Handle invalid player input.

        Default is to do nothing.

        Note that timeout also counts as invalid input.
        """
        print(f'Yoohoo! Player {current_player} sent something naughty! '
              'I will pretend it didn\'t happen, but they may be disqualified '
              'in the future.')
        self._save_step(
            replay.PlayerStep(
                current_player,
                status='Invalid input or timeout.',
                success=False))

    def step(self, current_player: int,
             player_input: judge.PlayerInput) -> None:
        """
        Apply player action.
        """
        dx, dy = player_input
        assert not self.circuit.player_won(current_player)
        try:
            self.circuit.move_player(current_player, np.array([dx, dy]))
            player_step = replay.PlayerStep(
                current_player, success=True, dx=dx, dy=dy)
        except grid_race_env.InvalidMove:
            # Penalty and set velocity to 0
            self.penalties[current_player] = self.INVALID_ACTION_PENALTY
            self.circuit.stop_player(current_player)
            player_step = replay.PlayerStep(
                current_player,
                success=False,
                status=f'Invalid move: ({dx}, {dy}).')
        if self.circuit.player_won(current_player):
            self.scores[current_player] = self.turns
        self._save_step(player_step)

    def get_scores(self) -> list[int | float]:
        """
        Return the scores of the players. Called after the end of the game.
        """
        return self.scores

    @property
    def num_players(self):
        return self._num_players

def run_judge():
    app = judge.App('Grid Race Tier 2')
    options = app.options
    circuit = grid_race_env.load_track_from_file(options['track_file'])
    env = GridRaceEnv(options['num_players'], options['visibility_radius'],
                      circuit, options['max_turns'])
    scores = app.run_environment(env)
    print('Final scores:', scores)
    if app.create_replay:
        with app.replay_file() as f:
            replay.serialise(env.replay, f)
    app.write_output(scores)

if __name__ == "__main__":
    run_judge()
