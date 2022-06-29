from client_ml import WorkerToEvaluate, LocalOutput, run
from client_web3 import getModels, sendResponse
from scripts.Client.client_web3 import listen_to_selection_events, register


def main():
    # Register to the SC
    register()

    # Listen to the events of RoundWorkersSelection and LastRoundWorkersSelection
    listen_to_selection_events()


if __name__ == "__main__":
    main()
