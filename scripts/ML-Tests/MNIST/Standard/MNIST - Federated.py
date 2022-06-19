# baseline cnn model for mnist
from sklearn.utils import shuffle
from matplotlib import pyplot
import numpy as np
import sys
from tensorflow.keras.datasets import mnist
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D
from tensorflow.keras.layers import MaxPooling2D
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import Flatten
from tensorflow.keras.optimizers import SGD

# device_name = tf.test.gpu_device_name()
# if device_name != "/device:GPU:0":
#     raise SystemError("GPU device not found")
# print("Found GPU at: {}".format(device_name))
# device_lib.list_local_devices()


# Constants
TOTAL_WORKERS = 100
ROUNDS = 10
WORKERS_IN_ROUND = TOTAL_WORKERS // ROUNDS  # This is K'
BEST_K = 3

LOCAL_EPOCHS = 5
LOCAL_BATCH_SIZE = 64

# CLASSES
class LocalOutput:
    def __init__(self):
        self.model = None
        self.bestKWorkers = []


class Worker:
    def __init__(self, train_data_X, train_data_Y):
        self.loss = None
        self.accuracy = None
        self.localOutput = LocalOutput()
        self.train_data_X = train_data_X
        self.train_data_Y = train_data_Y


def get_loss(worker):
    return worker.loss


class Round:
    def __init__(self):
        self.workers = []


# Global var
Rounds = []


def summarize_diagnostics(history, save):
    pyplot.title("Accuracy on BEST_K = " + str(BEST_K * 10) + "%")
    pyplot.plot(history, color="blue", label="test")

    # save plot to file
    if save:
        filename = sys.argv[0].split("/")[-1]
        pyplot.savefig(filename + str(BEST_K) + "_plot.png")

    # pyplot.show()
    pyplot.close()


# load train and test dataset
def load_dataset():
    # load dataset
    (trainX, trainY), (testX, testY) = mnist.load_data()
    # reshape dataset to have a single channel
    trainX = trainX.reshape((trainX.shape[0], 28, 28, 1))
    testX = testX.reshape((testX.shape[0], 28, 28, 1))
    # one hot encode target values
    trainY = to_categorical(trainY)
    testY = to_categorical(testY)
    return trainX, trainY, testX, testY


# scale pixels
def prep_pixels(train, test):
    # convert from integers to floats
    train_norm = train.astype("float32")
    test_norm = test.astype("float32")
    # normalize to range 0-1
    train_norm = train_norm / 255.0
    test_norm = test_norm / 255.0
    # return normalized images
    return train_norm, test_norm


# define cnn model
def define_model():
    model = Sequential()
    model.add(
        Conv2D(
            32,
            (3, 3),
            activation="relu",
            kernel_initializer="he_uniform",
            input_shape=(28, 28, 1),
        )
    )
    model.add(MaxPooling2D((2, 2)))
    model.add(Conv2D(64, (3, 3), activation="relu", kernel_initializer="he_uniform"))
    model.add(Conv2D(64, (3, 3), activation="relu", kernel_initializer="he_uniform"))
    model.add(MaxPooling2D((2, 2)))
    model.add(Flatten())
    model.add(Dense(100, activation="relu", kernel_initializer="he_uniform"))
    model.add(Dense(10, activation="softmax"))
    # compile model
    opt = SGD(learning_rate=0.01, momentum=0.9)
    model.compile(optimizer=opt, loss="categorical_crossentropy", metrics=["accuracy"])
    return model


def initialize():
    # load dataset
    trainX, trainY, testX, testY = load_dataset()
    # prepare pixel data
    trainX, testX = prep_pixels(trainX, testX)
    trainX, trainY = shuffle(trainX, trainY)
    step_size = int((60000 / ROUNDS) / WORKERS_IN_ROUND)
    print(f"Number of data for every worker: {step_size}")

    # define model
    model = define_model()

    # Evaluate Starting model
    _, acc = model.evaluate(testX, testY, verbose=0)
    print("\nInitial accuracy: %.3f" % (acc * 100.0))
    w = Worker(trainX, trainY)
    w.localOutput.model = model
    Rounds[0].workers.append(w)

    # Split the dataset among the workers
    for i in range(TOTAL_WORKERS):
        splitX = trainX[
            step_size * (i) : step_size * (i + 1),
            :,
        ]
        splitY = trainY[
            step_size * (i) : step_size * (i + 1),
            :,
        ]
        Rounds[(i // WORKERS_IN_ROUND) + 1].workers.append(Worker(splitX, splitY))

    return acc * 100.0


def local_update(evaluator: Worker, workersToEvaluate: list[Worker]):
    # 1) EVALUATE PULLED MODELS AND SELECT BEST K' WORKERS
    k = 1
    for w in workersToEvaluate:
        model = w.localOutput.model
        loss, acc = model.evaluate(
            evaluator.train_data_X, evaluator.train_data_Y, verbose=0
        )
        # print("Local evaluation accuracy on worker %i > %.3f" % (k, acc * 100.0))
        w.loss = loss
        w.accuracy = acc
        k = k + 1

    workersToEvaluate.sort(key=get_loss)
    evaluator.localOutput.bestKWorkers = workersToEvaluate[
        : min(max(BEST_K, 1), len(workersToEvaluate))
    ]  # 1st OUTPUT

    # 2) AVERAGE BEST K' models
    weights = [
        w.localOutput.model.get_weights() for w in evaluator.localOutput.bestKWorkers
    ]
    new_weights = list()
    for weights_list_tuple in zip(*weights):
        new_weights.append(
            np.array([np.array(w).mean(axis=0) for w in zip(*weights_list_tuple)])
        )

    # Set the average as starting new model
    new_model = define_model()
    new_model.set_weights(new_weights)

    # 3) LOCAL TRAINING
    new_model.fit(
        evaluator.train_data_X,
        evaluator.train_data_Y,
        epochs=LOCAL_EPOCHS,
        batch_size=64,
        verbose=0,
    )
    _, _, testX, testY = load_dataset()
    _, acc = model.evaluate(testX, testY, verbose=0)
    # print("Accuracy after local training > %.3f" % (acc * 100.0))
    evaluator.localOutput.model = new_model  # 2nd OUTPUT

    text_file = open("accuracies" + str(BEST_K) + ".txt", "a")
    text_file.write("\n" + str(acc * 100))
    text_file.close()
    return acc * 100.0


def do_Round(i):
    k = 1
    bestRoundAccuracy = 0.0
    for w in Rounds[i].workers:
        print(f"\nWorker[{k}] starting...")
        acc = local_update(w, Rounds[i - 1].workers)
        if acc > bestRoundAccuracy:
            bestRoundAccuracy = acc
        k = k + 1
    return bestRoundAccuracy


# run the test harness for evaluating a model
def main():
    acc = initialize()

    history = [acc]
    for r in range(ROUNDS):
        # input("Press to start new round...")
        print(f"\n\nStarting round: [{r+1}]")
        text_file = open("accuracies" + str(BEST_K) + ".txt", "a")
        text_file.write("\nStarting round " + str(r + 1))
        text_file.close()

        acc = do_Round(r + 1)
        history.append(acc)
        summarize_diagnostics(history, False)
    summarize_diagnostics(history, True)


# entry point
for _ in range(ROUNDS + 1):
    Rounds.append(Round())
for i in range(5, 10):
    # Create 1 additional round to simulate the presence of the ROUND 0 where only 1 model is present
    for k in range(len(Rounds)):
        Rounds[k].workers = []
    BEST_K = i + 1
    main()
