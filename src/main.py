from protocol import Protocol
from sensor import *
from search import choose_action
import numpy as np
from state import *
from pprint import pprint
from colored_map import generate_colored_map


def main():
    p = Protocol("localhost", 10000)
    p.Connect()
    sensor = Sensor(p.GetData())
    state = State(sensor)
    
    while True:
        if not sensor.Sense(str(p.GetData())):
            break
        
        action = choose_action(sensor.environment.vis_radius, sensor.environment.vis_radius,
                               sensor.physics.vx, sensor.physics.vy,
                               np.array(sensor.vision.grid), state)
        state.add_global(sensor.physics.x, sensor.physics.y)
        
        p.SendData(f'{action[0]} {action[1]}\n')
        print(f'{action[0]} {action[1]}')

    print(state.player_global_visited)
    generate_colored_map(state.f_maps[3], (2 * sensor.environment.vis_radius + 1, 2* sensor.environment.vis_radius + 1), "map4.png")
if __name__ == "__main__":
    main()