from protocol import Protocol


def main():
    p = Protocol("localhost", 10000)
    p.Connect()
    print(p.GetData())
    print(p.GetData())
    p.SendData("1 1\n")
    print(p.GetData())
        

if __name__ == "__main__":
    main()