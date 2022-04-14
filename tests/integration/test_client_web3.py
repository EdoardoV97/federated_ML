from brownie import accounts
from web3 import Web3
from decimal import Decimal
from scripts.deploy import deploy_FederatedML

from scripts.helpful_scripts import get_account, get_contract


OLD_DATA_POINTS = 0
NEW_LOCAL_DATA_POINTS = 1
NEW_MODEL = [1, 2, 3, 4, 5]


def test_contract_deploy():
    federated_ML = deploy_FederatedML(5)
    assert federated_ML.retrieveModel() == ([0, 0, 0, 0, 0], 0)


def test_push_model_and_retrieve():
    account = get_account()
    federated_ML = deploy_FederatedML(5)
    integer_rep_new_model = [Web3.toWei(x, "gwei") for x in NEW_MODEL]
    tx = federated_ML.updateModel(
        integer_rep_new_model, OLD_DATA_POINTS, NEW_LOCAL_DATA_POINTS, {"from": account}
    )
    tx.wait(1)
    (pulled_model, pulled_model_data_points) = federated_ML.retrieveModel()
    assert (pulled_model, pulled_model_data_points) == (
        [Web3.toWei(x, "gwei") for x in NEW_MODEL],
        1,
    )
    assert [Web3.fromWei(x, "gwei") for x in pulled_model] == NEW_MODEL
