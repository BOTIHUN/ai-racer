from sensor import *

# Constants
EMPTY = 0
WALL = -1
START = 1
NOT_VISIBLE = 3
GOAL = 100

class State:
    def __init__(self, sensor: Sensor):
        self.player_global_visited = set()
        self.sensor = sensor
        self.player_last_acc = (0,0)
        self.f_maps = list()
    def add_global(self, x, y):
        self.player_global_visited.add((x,y))
    def is_visited(self, x, y):
        return (x,y) in self.player_global_visited
    def to_global(self, local_dx, local_dy):
        return (self.sensor.physics.x + local_dx, self.sensor.physics.y + local_dy)