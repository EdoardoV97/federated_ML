from scripts.Client.client_ml import applyLocalTraining
from scripts.Client.client_web3 import pullModel, pushModel

# weights = [-6.034544563891951 * 10 ** -16, 0.9627571]


def main():
    pulled_model, pulled_model_data_points = pullModel()
    newModel, new_local_data_points = applyLocalTraining(weights=pulled_model)
    pushModel(newModel, pulled_model_data_points, new_local_data_points)
