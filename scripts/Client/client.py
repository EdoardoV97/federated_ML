import pandas as pd
import numpy as np
from scipy.stats import zscore
# from sklearn import linear_model
from web3 import Web3
from decimal import Decimal

def gradientOLS (w, X, y):
    return -(X.T).dot(y - X.dot(w))


def gradient_descent(gradient, W, X, y, learn_rate, n_iter):
    W_new = W
    for _ in range(n_iter):
        W_new = W_new - learn_rate * gradient(W, X, y)
    return W_new 




weights = [-6.034544563891951 * 10** -16 ,0.9627571]
print('Coefficients [PULLED ONE] : {}'.format(weights))
# print('Features : {}'.format(X))





# NEW LOCAL TRAINING
# Retrieve the dataset
file = "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data"
# file = 'iris.data'
names = ['sepal-length', 'sepal-width', 'petal-length', 'petal-width', 'class']
dataset_complete = pd.read_csv(file, names=names)
dataset = dataset_complete
# dataset = dataset_complete.truncate(before=74)
dataset = dataset.drop('sepal-length', axis='columns')
dataset = dataset.drop('sepal-width', axis='columns')
dataset = dataset.drop('class', axis='columns')

X = zscore(dataset['petal-length'].values).reshape(-1, 1) 
y = zscore(dataset['petal-width'].values)

X = np.c_[ np.ones(150),  X ]



newModel = gradient_descent(gradientOLS, weights, X, y, 1, 1)

print('Coefficients [LOCAL UPDATE] : {}'.format(newModel))

# Convert the weights to integers, because the EVM (Solidity) cannot handle floating point numbers
# Invoke the smart contract and send the weights

# integerRepresentation = [Web3.toWei(x, 'lovelace') for x in newModel]
print(Web3.toWei(Decimal(3.123456789), 'gwei'))

print(Web3.fromWei(3123456789, 'gwei'))