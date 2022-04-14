from brownie import accounts
from web3 import Web3
from decimal import Decimal

from scripts.helpful_scripts import get_account, get_contract


def pullModel():
    federated_ML = get_contract("FederatedML")
    (pulled_model, data_points_pulled_model) = federated_ML.retrieveModel()
    print(
        f"The number of data points of the current model is: {data_points_pulled_model}"
    )
    print(f"The pulled model is: {pulled_model}")
    float_rep_pulled_model = [Web3.fromWei(x, "gwei") for x in pulled_model]
    return float_rep_pulled_model, data_points_pulled_model


def pushModel(new_model, old_data_points, new_local_data_points):
    account = get_account()
    integer_rep_new_model = [Web3.toWei(x, "gwei") for x in new_model]
    federated_ML = get_contract("FederatedML")
    print(f"Federated_ML contract called to issue tokens: {federated_ML}")
    tx = federated_ML.updateModel(
        integer_rep_new_model, old_data_points, new_local_data_points, {"from": account}
    )
    tx.wait(1)
