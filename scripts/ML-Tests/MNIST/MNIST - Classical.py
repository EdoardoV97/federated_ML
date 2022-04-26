import sys
import requests
import json
from matplotlib import pyplot
from sklearn.model_selection import KFold
from tensorflow.keras.datasets import mnist
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D
from tensorflow.keras.layers import MaxPooling2D
from tensorflow.keras.layers import Dense
from tensorflow.keras.layers import Flatten
from tensorflow.keras.optimizers import SGD

# import tensorflow as tf
# from tensorflow.python.client import device_lib

# device_name = tf.test.gpu_device_name()
# if device_name != "/device:GPU:0":
#     raise SystemError("GPU device not found")
# print("Found GPU at: {}".format(device_name))
# device_lib.list_local_devices()


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


# plot diagnostic learning curves
def summarize_diagnostics(history):
    # plot loss
    pyplot.subplot(211)
    pyplot.title("Cross Entropy Loss")
    pyplot.plot(history.history["loss"], color="blue", label="train")
    pyplot.plot(history.history["val_loss"], color="orange", label="test")
    # plot accuracy
    pyplot.subplot(212)
    pyplot.title("Classification Accuracy")
    pyplot.plot(history.history["accuracy"], color="blue", label="train")
    pyplot.plot(history.history["val_accuracy"], color="orange", label="test")
    # save plot to file
    filename = sys.argv[0].split("/")[-1]
    pyplot.savefig(filename + "_plot.png")
    pyplot.close()


def save_to_IPFS():
    filepath = "MNIST-model.h5"
    # model.save_weights(filepath, overwrite=True)

    response = requests.post(
        "http://127.0.0.1:5001/api/v0/add", files={filepath: open(filepath, "rb")}
    )
    p = response.json()
    hash = p["Hash"]
    print(hash)


def get_from_IPFS():
    params = (("arg", "QmYr27Zwr7MYDAv4dExNtXrpe56hcG5D6oEJEAoUsVYagk"),)
    response = requests.post("http://127.0.0.1:5001/api/v0/get", params=params)
    print(response)
    pass


# run the test harness for evaluating a model
def run_test_harness():
    # # load dataset
    # trainX, trainY, testX, testY = load_dataset()
    # # prepare pixel data
    # trainX, testX = prep_pixels(trainX, testX)
    # # define model
    # model = define_model()
    # # fit model
    # history = model.fit(
    #     trainX, trainY, epochs=5, batch_size=64, validation_data=(testX, testY)
    # )
    # # evaluate model
    # _, acc = model.evaluate(testX, testY, verbose=0)
    # print("> %.3f" % (acc * 100.0))

    # save_to_IPFS()
    get_from_IPFS()

    # learning curves
    # summarize_diagnostics(history)


# entry point, run the test harness
run_test_harness()
