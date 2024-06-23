from protocol import Protocol


def main():
    p = Protocol("localhost", 10000)
    p.Connect()
    print(p.InitialParameters())
        

if __name__ == "__main__":
    main()