class State:
    def __init__(self, prev_x, prev_y):
        self.prev_x = prev_x
        self.prev_y = prev_y
    def Update(self, x, vx, ax,y, vy, ay):
        self.prev_x = x + vx + ax
        self.prev_y = y + vy + ay