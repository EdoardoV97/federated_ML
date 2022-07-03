from tabnanny import check
import unittest
from brownie import config, network
from scripts.helpful_scripts import fund_with_link, get_account, get_contract
from scripts.deploy import deploy_FederatedML


@unittest.skip("Passed")
def test_second_round_get_models():
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

    tx = federatedML_contract.fulfillRandomnessTesting(1)
    tx.wait(1)

    selected_workers = federatedML_contract.getWorkersInRound(1)
    selected_addresses_index = []
    for w in range(1, 7):
        if get_account(w) == selected_workers[0]:
            selected_addresses_index.append(w)
            assert w == 4
        if get_account(w) == selected_workers[1]:
            selected_addresses_index.append(w)
            assert w == 5

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

    assert federatedML_contract.getPreviousModels() == ["model_1", "model_2"]


@unittest.skip("Passed")
def test_second_round_commit_work():
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
    selected_workers_1 = federatedML_contract.getWorkersInRound(0)
    selected_addresses_index_1 = []
    for w in range(1, 7):
        if get_account(w) == selected_workers_1[0]:
            selected_addresses_index_1.append(w)
        if get_account(w) == selected_workers_1[1]:
            selected_addresses_index_1.append(w)

    tx = federatedML_contract.commitWork(
        [], "model_1", {"from": get_account(selected_addresses_index_1[0])}
    )
    tx.wait(1)
    print(f"Worker{selected_addresses_index_1[0]} committed the model update")
    tx = federatedML_contract.commitWork(
        [], "model_2", {"from": get_account(selected_addresses_index_1[1])}
    )
    tx.wait(1)
    print(f"Worker{selected_addresses_index_1[1]} committed the model update")

    tx = federatedML_contract.fulfillRandomnessTesting(1)
    tx.wait(1)

    selected_workers_2 = federatedML_contract.getWorkersInRound(1)
    selected_addresses_index_2 = []
    for w in range(1, 7):
        if get_account(w) == selected_workers_2[0]:
            selected_addresses_index_2.append(w)
            assert w == 4
        if get_account(w) == selected_workers_2[1]:
            selected_addresses_index_2.append(w)
            assert w == 5

    assert (
        federatedML_contract.addressToWorkerInfo(
            get_account(selected_addresses_index_2[0])
        )[4]
        == True
    )
    assert (
        federatedML_contract.addressToWorkerInfo(
            get_account(selected_addresses_index_2[1])
        )[4]
        == True
    )

    tx = federatedML_contract.commitWork(
        [0], "model_3", {"from": get_account(selected_addresses_index_2[0])}
    )
    tx.wait(1)
    print(f"Worker{selected_addresses_index_2[0]} committed the model update")
    tx = federatedML_contract.commitWork(
        [0], "model_4", {"from": get_account(selected_addresses_index_2[1])}
    )
    tx.wait(1)
    print(f"Worker{selected_addresses_index_2[1]} committed the model update")

    # Check model hashes saved and last round started
    assert (
        federatedML_contract.addressToWorkerInfo(
            get_account(selected_addresses_index_2[0])
        )[5]
        == "model_3"
    )
    assert (
        federatedML_contract.addressToWorkerInfo(
            get_account(selected_addresses_index_2[1])
        )[5]
        == "model_4"
    )
    assert federatedML_contract.state() == 6

    # Check votes correctly assigned
    assert (
        federatedML_contract.addressToWorkerInfo(
            get_account(selected_addresses_index_1[0])
        )[2]
        == 2
    )
    assert (
        federatedML_contract.addressToWorkerInfo(
            get_account(selected_addresses_index_1[1])
        )[2]
        == 0
    )