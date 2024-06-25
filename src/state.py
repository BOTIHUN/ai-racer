from sensor import *

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
    def wait(self):
        self.idle_count = self.idle_count + 1
        if self.waiting_long():
            self.idle_count = 0
    def waiting_long(self):
        return self.idle_count > 6