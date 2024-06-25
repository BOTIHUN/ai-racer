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
        self.idle_count: int = 0
    def add_global(self, x, y):
        self.player_global_visited.add((x,y))
    def is_visited(self, x, y):
        return (x,y) in self.player_global_visited
    def to_global(self, local_dx, local_dy):
        return (self.sensor.physics.x + local_dx, self.sensor.physics.y + local_dy)

class BFS_State:
    def __init__(self, px = 0, py = 0, vx = 0, vy = 0, R = 0):
        self.px = px
        self.py = py
        self.vx = vx
        self.vy = vy
        self.R = R
        self.visited = set()
        self.global_grid = {}

    def update_position(self, x, y):
        self.px = x
        self.py = y

    def update_velocity(self, vx, vy):
        self.vx = vx
        self.vy = vy

    def add_to_visited(self, x, y):
        self.visited.add((x, y))

    def is_visited(self, x, y):
        return (x, y) in self.visited

    def to_global(self, dx, dy):
        return self.px + dx, self.py + dy

    def update_global_grid(self, vision_grid):
        for dx in range(-self.R, self.R + 1):
            for dy in range(-self.R, self.R + 1):
                gx, gy = self.to_global(dx, dy)
                if vision_grid[dx + self.R, dy + self.R] != NOT_VISIBLE:
                    self.global_grid[(gx, gy)] = vision_grid[dx + self.R, dy + self.R]
    def is_wall(self, x, y):
        cell_value = self.global_grid.get((x, y), EMPTY)
        return cell_value == WALL

    def is_goal(self, x, y):
        cell_value = self.global_grid.get((x, y), EMPTY)
        return cell_value == GOAL