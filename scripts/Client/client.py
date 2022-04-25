from client_ml import WorkerToEvaluate, LocalOutput, run
from client_web3 import getModels, sendResponse

workersToEvaluate: list(WorkerToEvaluate) = None
localOutput: list(LocalOutput) = None


def main():
    # Get the models to evaluate
    models_path = getModels()
    for p in models_path:
        w = WorkerToEvaluate(p)
        workersToEvaluate.append(w)

    # Do local training
    localOutput = run(workersToEvaluate)

    # Send back the response
    sendResponse(localOutput)


if __name__ == "__main__":
    main()
