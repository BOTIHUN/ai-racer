class Environment:
    def __init__(self, input: list[str]):
        self.height = int(input[0])
        self.width = int(input[1])
        self.num_of_players = int(input[2])
        self.vis_radius = int(input[3])

class Physics:
    def __init__(self, input: list[str]):
        self.x = int(input[0])
        self.y = int(input[1])
        self.vx = int(input[2])
        self.vy = int(input[3])

class Vision:
    def __init__(self, players: list[str], grid: list[str]):
        self.players = []
        self.grid = []
        for line in players:
            components = line.split()
            number_list = [int(x) for x in components]
            self.players.append(number_list)
        for line in grid:
            components = line.split()
            number_list = [int(x) for x in components]
            self.grid.append(number_list)
        
class Sensor:
    def __init__(self, input: str):
        temp = input.split()
        self.environment = Environment(temp)
        
    def Sense(self, input: str):
        if str == "~~~END~~~":
            return False
        lines = input.splitlines()
        self.physics = Physics(lines[0].split())
        lines = lines[1:]
        players = lines[:self.environment.num_of_players]
        lines = lines[self.environment.num_of_players:]
        grid = lines[:2 * self.environment.vis_radius + 1]
        self.vision = Vision(players, grid)
        return True
        
