from brownie import accounts, config, FederatedML, network
from scripts.helpful_scripts import get_account


def deploy_ML():
    account = get_account()
    # Deploy
    federatedML_contract = FederatedML.deploy(10, {"from": account})

    # Read the stored value
    # print(federatedML_contract.model(0))

    # Store a new value

    # Wait 1 block to complete, then read the stored value


def main():
    deploy_ML()
