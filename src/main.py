from protocol import Protocol
from sensor import *
from search import choose_action
import numpy as np

def main():
    p = Protocol("localhost", 10000)
    p.Connect()
    sensor = Sensor(p.GetData())
    while True:
        i = p.GetData()
        print(i)
        if not sensor.Sense(str(i)):
            break
        action = choose_action(sensor.physics.x, sensor.physics.y,
                        sensor.physics.vx, sensor.physics.vy,
                        np.array(sensor.vision.grid))
        print(f'{action[0]} {action[1]}\n')
        p.SendData(f'{action[0]} {action[1]}\n')


if __name__ == "__main__":
    main()