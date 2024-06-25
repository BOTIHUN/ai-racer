from protocol import Protocol
from sensor import *
from search import choose_action
import numpy as np
from state import State

def main():
    p = Protocol("localhost", 10000)
    p.Connect()
    sensor = Sensor(p.GetData())
    state = State(None, None)
    
    while True:
        i = p.GetData()
        print(i)
        if not sensor.Sense(str(i)):
            break
        print(vars(sensor.environment))
        action = choose_action(sensor.environment.vis_radius, sensor.environment.vis_radius,
                        sensor.physics.vx, sensor.physics.vy,
                        state.prev_x, state.prev_y,
                        np.array(sensor.vision.grid))
        state.Update(sensor.environment.vis_radius, sensor.physics.vx, action[0],
                     sensor.environment.vis_radius, sensor.physics.vy, action[1])
        print(f'{action[0]} {action[1]}\n')
        p.SendData(f'{action[0]} {action[1]}\n')


if __name__ == "__main__":
    main()