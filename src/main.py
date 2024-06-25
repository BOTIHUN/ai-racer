from protocol import Protocol
from sensor import *
from search import choose_action
import numpy as np
from state import State

def main():
    p = Protocol("localhost", 10000)
    p.Connect()
    sensor = Sensor(p.GetData())
    state = State(sensor)
    
    while True:
        i = p.GetData()
        if not sensor.Sense(str(i)):
            break
        state.add_global(sensor.physics.x, sensor.physics.y)
        action = choose_action(sensor.environment.vis_radius, sensor.environment.vis_radius,
                        sensor.physics.vx, sensor.physics.vy,
                        np.array(sensor.vision.grid), state)
        p.SendData(f'{action[0]} {action[1]}\n')
        print(action)

    print(state.player_global_visited)
    
if __name__ == "__main__":
    main()