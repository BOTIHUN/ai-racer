from protocol import Protocol
from sensor import *

def main():
    p = Protocol("localhost", 10000)
    p.Connect()
    sensor = Sensor(p.GetData())
    sensor.Sense(p.GetData())
    print(vars(sensor.environment))
    print(len(sensor.vision.grid))
    print(vars(sensor.physics))

if __name__ == "__main__":
    main()