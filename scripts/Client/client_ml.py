from sklearn.utils import shuffle
from matplotlib import pyplot
import numpy as np
from tensorflow.keras.datasets import mnist
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D
from tensorflow.keras.layers import MaxPooling2D
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import Flatten
from tensorflow.keras.optimizers import SGD

# Constants
TOTAL_WORKERS = 100
ROUNDS = 10
WORKERS_IN_ROUND = TOTAL_WORKERS // ROUNDS  # This is K'
BEST_K = (WORKERS_IN_ROUND + 1) // 2

LOCAL_EPOCHS = 5
LOCAL_BATCH_SIZE = 64

# CLASSES
class LocalOutput:
    def __init__(self):
        self.model = None
        self.bestKWorkers = []


class LocalDataset:
    def __init__(self):
        self.X = None
        self.Y = None


class WorkerToEvaluate:
    def __init__(self, weightsFile):
        self.weightsFile = weightsFile
        self.loss = None
        self.accuracy = None


def get_loss(worker):
    return worker.loss


# GLOBAL VARIABLES
localDataset: LocalDataset = None
localOutput: LocalOutput = None

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


def get_localDataset():
    trainX, trainY, testX, testY = load_dataset()
    localDataset.X = trainX
    localDataset.Y = trainY


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


def local_update(workersToEvaluate: list[WorkerToEvaluate], isLastRound: bool):
    # 1) EVALUATE PULLED MODELS AND SELECT BEST K' WORKERS
    # k = 1
    for w in workersToEvaluate:
        model = define_model()
        model.load_weights(w.weightsFile)
        loss, acc = model.evaluate(localDataset.X, localDataset.Y, verbose=0)
        # print("Local evaluation accuracy on worker %i > %.3f" % (k, acc * 100.0))
        w.loss = loss
        w.accuracy = acc
        # k = k + 1

    bestVotedWorkers = workersToEvaluate
    bestVotedWorkers.sort(key=get_loss)
    bestVotedWorkers = bestVotedWorkers[: min(max(BEST_K, 1), len(workersToEvaluate))]
    for w in bestVotedWorkers:
        for w2 in workersToEvaluate:
            if w.weightsFile == w2.weightsFile:
                localOutput.bestKWorkers.append(
                    workersToEvaluate.index(w2)
                )  # 1st OUTPUT

    if not isLastRound:
        # 2) AVERAGE BEST K' models
        weights = [w.localOutput.model.get_weights() for w in localOutput.bestKWorkers]
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
            localDataset.X,
            localDataset.Y,
            epochs=LOCAL_EPOCHS,
            batch_size=64,
            verbose=0,
        )
        # trainX, trainY, testX, testY = load_dataset()
        # _, acc = model.evaluate(testX, testY, verbose=0)
        # print("Accuracy after local training > %.3f" % (acc * 100.0))
        model.save_weights("myModel")  # 2nd OUTPUT
        localOutput.model = "myModel"
        return acc * 100.0


def run_learning(workersToEvaluate: list[WorkerToEvaluate], isLastRound: bool):
    # Initialize the local dataset
    get_localDataset()

    # Do local training
    local_update(workersToEvaluate, isLastRound)

    # Return the output
    return localOutput
