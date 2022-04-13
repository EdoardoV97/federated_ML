import pandas as pd
import numpy as np
from scipy.stats import zscore
from sklearn import linear_model

# Retrieve the dataset
#url = "https://archive.ics.uci.edu/ml/machine-learning-databases/iris/iris.data"
file = 'iris.data'
names = ['sepal-length', 'sepal-width', 'petal-length', 'petal-width', 'class']
dataset = pd.read_csv(file, names=names)

# Print the first 5 line of the dataset
print(dataset.head())
print('\n')

# Remove features
# Leave only petal-lenght and petal-width
dataset = dataset.drop('sepal-length', axis='columns')
dataset = dataset.drop('sepal-width', axis='columns')
dataset = dataset.drop('class', axis='columns')

# Define the input dataset(X) and the output dataset(Y)
x = zscore(dataset['petal-length'].values).reshape(-1, 1) 
y = zscore(dataset['petal-width'].values)


# Build the model
lin_model = linear_model.LinearRegression()
lin_model.fit(x, y)

w1 = lin_model.coef_ # weights of the model are stored here
w0 = lin_model.intercept_ # and here it is the intercept

weights = np.concatenate( (w1, [w0] ) )

print('Coefficients : {}'.format(weights))


# Convert the weights to integers, because the EVM (Solidity) cannot handle floating point numbers
# Invoke the smart contract and send the weights