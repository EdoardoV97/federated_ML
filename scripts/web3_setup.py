# This script is needed to deploy the SC with web3, so to be able to retrieve the SC in the deployments folder
# If we use brownie, we cannot get the SC in the development network


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
    tx = fund_with_link(federatedML_contract.address, amount=link_amount)  # attenzione
    tx.wait(1)

    # Fund the bounty
    assert federatedML_contract.state() == 0  # Funding state check
    fund_quantity = 1 * 10 ** 18  # 1 Wei
    tx = federatedML_contract.fund({"from": account, "value": fund_quantity})  # 1 ETH
    tx.wait(1)
    assert fund_quantity == federatedML_contract.balance()

    # Stop funding phase
    tx = federatedML_contract.stopFunding({"from": account})
    tx.wait(1)
    assert federatedML_contract.state() == 1  # Registering state check

    # Get the entranceFee
    worker_fee = federatedML_contract.entranceFee()
    print(f"Entrance fee is: {worker_fee} Wei")

    # Register the workers
    for w in range(1, 7):
        assert federatedML_contract.state() == 1  # Registering state check
        tx = federatedML_contract.register(
            {"from": get_account(w), "value": worker_fee}
        )
        print(f"Worker{w} registered!")
        tx.wait(1)

    # Start the round
    tx = federatedML_contract.fulfillRandomnessTesting(1)
    tx.wait(1)
    time.sleep(5)
    assert federatedML_contract.state() == 5  # Round in progress state check


if __name__ == "__main__":
    main()
