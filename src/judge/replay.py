import json
import dataclasses
import numpy as np
import typing

from typing import Optional, Any

@dataclasses.dataclass(frozen=True, slots=True)
class EnvInfo:
    track: list[list[int]]
    num_players: int

@dataclasses.dataclass(frozen=True, slots=True)
class PlayerState:
    x: int
    y: int
    vel_x: int
    vel_y: int

@dataclasses.dataclass(frozen=True, slots=True)
class State:
    turn: int
    players: list[PlayerState]

@dataclasses.dataclass(frozen=True, slots=True)
class PlayerStep:
    player_ind: int
    success: bool
    status: str = ''
    dx: Optional[int] = None
    dy: Optional[int] = None

    def __post_init__(self):
        if self.success:
            assert self.dx is not None, \
                    'dx should be defined for a successful step'
            assert self.dy is not None, \
                    'dy should be defined for a successful step'
        else:
            assert self.status, 'Failure message should be specified'

@dataclasses.dataclass(frozen=True, slots=True)
class Replay:
    """
    ``states`` contain the states before and after each step, ``steps`` contain
    the plys or steps the players made. So ``len(states) = len(steps) + 1``.
    """
    env_info: EnvInfo
    states: list[State] = dataclasses.field(default_factory=list)
    steps: list[PlayerStep] = dataclasses.field(default_factory=list)
    version: int = 1

class Encoder(json.JSONEncoder):

    def default(self, o):
        if isinstance(o, (EnvInfo, PlayerState, State, PlayerStep, Replay)):
            return {
                field.name: getattr(o, field.name)
                for field in dataclasses.fields(o)
            }
        elif isinstance(o, np.integer):
            return int(o)
        else:
            return json.JSONEncoder.default(self, o)

def serialise(replay: Replay, output) -> None:
    if isinstance(output, str):
        with open(output, 'w') as f:
            json.dump(replay, f, cls=Encoder)
    else:
        json.dump(replay, output, cls=Encoder)

def _construct_dataclass(target_cls: type, obj: dict[str] | Any):
    # Note: this (whole function) only works if the dataclasses are not
    # subclassed
    # Also not supported: tuples and dicts (use dataclasses)
    generic_cls = typing.get_origin(target_cls)
    assert generic_cls not in [dict, tuple], f'{generic_cls} is not supported'
    if generic_cls == list:
        return target_cls(
            _construct_dataclass(typing.get_args(target_cls)[0], elem)
            for elem in obj)
    if generic_cls == Optional or generic_cls == typing.Union:
        concrete_clss = typing.get_args(target_cls)
        assert (not dataclasses.is_dataclass(concrete_clss[0])
                and concrete_clss[0] not in [
                    list, tuple
                ]), 'Only elementary types are supported with Optional.'
        assert (not dataclasses.is_dataclass(concrete_clss[1])
                and concrete_clss[1] not in [
                    list, tuple
                ]), 'Only elementary types are supported with Optional.'
        assert not isinstance(obj, (list, tuple, dict))
        return obj
    if not dataclasses.is_dataclass(target_cls):
        # Leaf node
        return target_cls(obj)
    assert typing.get_origin(target_cls) != tuple, \
        'Tuples are not supported for deserialisation'
    fields = typing.get_type_hints(target_cls)
    typed_obj = {k: _construct_dataclass(fields[k], v) for k, v in obj.items()}
    return target_cls(**typed_obj)

def deserialise(fname: str) -> Replay:
    with open(fname, 'r') as f:
        obj_dict = json.load(f)
    return _construct_dataclass(Replay, obj_dict)
