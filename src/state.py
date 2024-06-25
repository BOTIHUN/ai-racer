from sensor import *

class State:
    def __init__(self, sensor: Sensor):
        self.player_global_visited = set()
        self.sensor = sensor
    def add_global(self, x, y):
        self.player_global_visited.add((x,y))
    def is_visited(self, x, y):
        return (x,y) in self.player_global_visited
    def to_global(self, x, y):
        gx = self.sensor.physics.x + (x - self.sensor.environment.vis_radius)
        gy = self.sensor.physics.y + (y - self.sensor.environment.vis_radius)
        return gx,gy