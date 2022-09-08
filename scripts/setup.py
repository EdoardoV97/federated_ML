# This script is needed to deploy the SC to testnets or ganacheUI


import time
from brownie import config, network
from scripts.helpful_scripts import fund_with_link, get_account, get_contract
from scripts.deploy import deploy_FederatedML


def main():
    federatedML_contract = deploy_FederatedML()
    account = get_account()
    oracle_fee = config["networks"][network.show_active()]["fee"]

    link_amount = oracle_fee * 10  # 0.1 * 10 = 1 LINK

    # Fund with link
    tx = fund_with_link(federatedML_contract.address, amount=link_amount)
    tx.wait(1)

    # Fund the bounty
    fund_quantity = 10  # 10 Wei
    tx = federatedML_contract.fund({"from": account, "value": fund_quantity})
    tx.wait(1)

    print("Stopping funding!")
    # Stop funding phase
    tx = federatedML_contract.stopFunding({"from": account})
    tx.wait(1)


if __name__ == "__main__":
    main()
