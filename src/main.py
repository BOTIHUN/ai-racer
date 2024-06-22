from Net import Net

def main():
    net = Net('localhost', 10000)
    net.Connect()
    net.Recieve()
    print(net.GetResponse().decode("utf8"))
        

if __name__ == "__main__":
    main()