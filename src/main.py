from protocol import Protocol
from sensor import *
from bfs_search import choose_action
import numpy as np
from state import *
from pprint import pprint


def main():
    p = Protocol("localhost", 10000)
    p.Connect()
    sensor = Sensor(p.GetData())
    state = State(sensor)
    bfs_state =  BFS_State()
    
    while True:
        if not sensor.Sense(str(p.GetData())):
            break
        bfs_state.update_position(sensor.physics.x, sensor.physics.y)
        bfs_state.update_velocity(sensor.physics.vx, sensor.physics.vy)
        bfs_state.update_global_grid(np.array(sensor.vision.grid))
        #bfs_state.add_to_visited(sensor.physics.x, sensor.physics.y)
        bfs_state.R = sensor.environment.vis_radius
        
        action = choose_action(sensor.physics.x, sensor.physics.y,
                               sensor.physics.vx, sensor.physics.vy,
                               np.array(sensor.vision.grid), bfs_state)
        
        p.SendData(f'{action[0]} {action[1]}\n')
        print(action)

    pprint(bfs_state.global_grid)
if __name__ == "__main__":
    main()