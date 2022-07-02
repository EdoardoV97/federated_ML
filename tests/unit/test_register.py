import unittest
from brownie import config, network
from scripts.helpful_scripts import fund_with_link, get_account
from scripts.deploy import deploy_FederatedML


@unittest.skip("Passed")
def test_register():
    federatedML_contract = deploy_FederatedML()
    account = get_account()
    oracle_fee = config["networks"][network.show_active()]["fee"]

    link_amount = oracle_fee * 10  # 0.1 * 10 = 1 LINK

    # Fund with link
    tx = fund_with_link(
        federatedML_contract.address, get_account(key=True), amount=link_amount
    )  # attenzione
    tx.wait(1)

    # Fund the bounty
    fund_quantity = 1 * 10 ** 18  # 1 Wei
    tx = federatedML_contract.fund({"from": account, "value": fund_quantity})  # 1 ETH
    tx.wait(1)
    assert fund_quantity == federatedML_contract.balance()

    # Stop funding phase
    tx = federatedML_contract.stopFunding({"from": account})
    tx.wait(1)

    # Get the entranceFee
    worker_fee = federatedML_contract.entranceFee()
    print(f"Entrance fee is: {worker_fee} Wei")

    # Register the workers
    for w in range(1, 7):
        tx = federatedML_contract.register(
            {"from": get_account(w), "value": worker_fee}
        )
        print(f"Worker{w} registered!")
        tx.wait(1)

    # Check in the map if all registered workers are present
    for w in range(1, 7):
        info = federatedML_contract.addressToWorkerInfo(get_account(w).address)
        assert info[0] == True

    # TODO check if a round has been created and the worker selected
    state = federatedML_contract.state()
    print(state)


@unittest.skip("Passed")
def test_unregister():
    federatedML_contract = deploy_FederatedML()
    account = get_account()
    oracle_fee = config["networks"][network.show_active()]["fee"]

    link_amount = oracle_fee * 10  # 0.1 * 10 = 1 LINK

    # Fund with link
    tx = fund_with_link(
        federatedML_contract.address, get_account(key=True), amount=link_amount
    )  # attenzione
    tx.wait(1)

    # Fund the bounty
    fund_quantity = 1 * 10 ** 18  # 1 Wei
    tx = federatedML_contract.fund({"from": account, "value": fund_quantity})  # 1 ETH
    tx.wait(1)
    assert fund_quantity == federatedML_contract.balance()

    # Stop funding phase
    tx = federatedML_contract.stopFunding({"from": account})
    tx.wait(1)

    # Get the entranceFee
    worker_fee = federatedML_contract.entranceFee()
    print(f"Entrance fee is: {worker_fee} Wei")

    # Register the worker
    tx = federatedML_contract.register({"from": account, "value": worker_fee})
    print("Worker registered!")
    info = federatedML_contract.addressToWorkerInfo(get_account(0).address)
    assert info[0] == True
    tx.wait(1)

    # Deregister the worker
    tx = federatedML_contract.unregister()
    print("Worker Deregistered!")
    info = federatedML_contract.addressToWorkerInfo(get_account(0).address)
    assert info[0] == False
    tx.wait(1)
