import pandas as pd
import numpy as np
from scipy.stats import zscore

CONSIDERED_DATA_PONTS = 150


def gradientLS(w, X, y):
    return -(X.T).dot(y - X.dot(w))


def gradient_descent(gradient, W, X, y, learn_rate, n_iter):
    W_new = W
    for _ in range(n_iter):
        W_new = W_new - learn_rate * gradient(W, X, y)
    return W_new


def applyLocalTraining(weights):
    # NEW LOCAL TRAINING
    print(f"The number of local data points used is: {CONSIDERED_DATA_PONTS}")
    # Retrieve the dataset
    file = "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data"
    # file = 'iris.data'
    names = ["sepal-length", "sepal-width", "petal-length", "petal-width", "class"]
    dataset_complete = pd.read_csv(file, names=names)
    dataset = dataset_complete
    # dataset = dataset_complete.truncate(before=74)
    dataset = dataset.drop("sepal-length", axis="columns")
    dataset = dataset.drop("sepal-width", axis="columns")
    dataset = dataset.drop("class", axis="columns")

    X = zscore(dataset["petal-length"].values).reshape(-1, 1)
    y = zscore(dataset["petal-width"].values)

    X = np.c_[np.ones(CONSIDERED_DATA_PONTS), X]

    newModel = gradient_descent(gradientLS, weights, X, y, 1, 1)

    print("Model[LOCAL UPDATE]: {}".format(newModel))
    return newModel, CONSIDERED_DATA_PONTS
