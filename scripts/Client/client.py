from client_web3 import register, listen_to_selection_events


def main():
    # Register to the SC
    register()

    # Listen to the events of RoundWorkersSelection and LastRoundWorkersSelection
    print("LIstening to worker selection events!")
    listen_to_selection_events()


if __name__ == "__main__":
    main()
