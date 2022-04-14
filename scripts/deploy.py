from brownie import accounts, config, FederatedML, network
from scripts.helpful_scripts import get_account


def deploy_ML(number_of_weigths=10):
    account = get_account()
    # Deploy
    federatedML_contract = FederatedML.deploy(number_of_weigths, {"from": account})
    print(f"Contract deployed to: {federatedML_contract.address}")
    return federatedML_contract

    # Read the stored value
    # print(federatedML_contract.model(0))

    # Store a new value

    # Wait 1 block to complete, then read the stored value


def main():
    deploy_ML()
