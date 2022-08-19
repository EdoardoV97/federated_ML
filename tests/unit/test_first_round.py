import unittest
from brownie import config, network
from scripts.helpful_scripts import fund_with_link, get_account, get_contract
from scripts.deploy import deploy_FederatedML


@unittest.skip("Passed")
def test_get_initial_model():
    federatedML_contract = deploy_FederatedML()
    account = get_account()
    oracle_fee = config["networks"][network.show_active()]["fee"]
    link_amount = oracle_fee * 10  # 0.1 * 10 = 1 LINK
    # Fund with link
    tx = fund_with_link(federatedML_contract.address, amount=link_amount)
    tx.wait(1)
    # Fund the bounty
    fund_quantity = 1 * 10 ** 18  # 1 Wei
    tx = federatedML_contract.fund({"from": account, "value": fund_quantity})  # 1 ETH
    tx.wait(1)
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

    tx = federatedML_contract.fulfillRandomnessTesting(1)
    tx.wait(1)
    selected_workers = federatedML_contract.getWorkersInRound(0)
    selected_addresses_index = []
    for w in range(1, 7):
        if get_account(w) == selected_workers[0]:
            selected_addresses_index.append(w)
            assert (
                w == 2
            )  # Because account registered from 1, and randomness=1, thus 1+1=2
        if get_account(w) == selected_workers[1]:
            selected_addresses_index.append(w)
            assert (
                w == 3
            )  # Because account registered from 1, and randomness=1, thus 2+1=3

    assert (
        federatedML_contract.addressToWorkerInfo(
            get_account(selected_addresses_index[0])
        )[4]
        == True
    )
    assert (
        federatedML_contract.addressToWorkerInfo(
            get_account(selected_addresses_index[1])
        )[4]
        == True
    )

    res = federatedML_contract.getPreviousModels()
    assert "test_hash" == res[0]
    res = federatedML_contract.getPreviousModels()
    assert "test_hash" == res[0]


@unittest.skip("Passed")
def test_commit_updates():
    federatedML_contract = deploy_FederatedML()
    account = get_account()
    oracle_fee = config["networks"][network.show_active()]["fee"]
    link_amount = oracle_fee * 10  # 0.1 * 10 = 1 LINK
    # Fund with link
    tx = fund_with_link(federatedML_contract.address, amount=link_amount)
    tx.wait(1)
    # Fund the bounty
    fund_quantity = 1 * 10 ** 18  # 1 Wei
    tx = federatedML_contract.fund({"from": account, "value": fund_quantity})  # 1 ETH
    tx.wait(1)
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

    tx = federatedML_contract.fulfillRandomnessTesting(1)
    tx.wait(1)
    selected_workers = federatedML_contract.getWorkersInRound(0)
    selected_addresses_index = []
    for w in range(1, 7):
        if get_account(w) == selected_workers[0]:
            selected_addresses_index.append(w)
        if get_account(w) == selected_workers[1]:
            selected_addresses_index.append(w)

    tx = federatedML_contract.commitWork(
        [], "model_1", {"from": get_account(selected_addresses_index[0])}
    )
    tx.wait(1)
    print(f"Worker{selected_addresses_index[0]} committed the model update")
    tx = federatedML_contract.commitWork(
        [], "model_2", {"from": get_account(selected_addresses_index[1])}
    )
    tx.wait(1)
    print(f"Worker{selected_addresses_index[1]} committed the model update")

    # Check model hashes saved and new round started
    assert (
        federatedML_contract.addressToWorkerInfo(
            get_account(selected_addresses_index[0])
        )[5]
        == "model_1"
    )
    assert (
        federatedML_contract.addressToWorkerInfo(
            get_account(selected_addresses_index[1])
        )[5]
        == "model_2"
    )
    assert federatedML_contract.state() == 4
