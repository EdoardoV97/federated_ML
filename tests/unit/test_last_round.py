from tabnanny import check
import unittest
from brownie import config, network
from scripts.helpful_scripts import fund_with_link, get_account, get_contract
from scripts.deploy import deploy_FederatedML


@unittest.skip("Passed")
def test_last_round_commit_secret_vote():
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
    print(f"{selected_workers_1[0]} committed the model update")
    tx = federatedML_contract.commitWork(
        [], "model_2", {"from": get_account(selected_addresses_index_1[1])}
    )
    tx.wait(1)
    print(f"{selected_workers_1[1]} committed the model update")

    tx = federatedML_contract.fulfillRandomnessTesting(1)
    tx.wait(1)

    selected_workers_2 = federatedML_contract.getWorkersInRound(1)
    selected_addresses_index_2 = []
    for w in range(1, 7):
        if get_account(w) == selected_workers_2[0]:
            selected_addresses_index_2.append(w)
        if get_account(w) == selected_workers_2[1]:
            selected_addresses_index_2.append(w)

    tx = federatedML_contract.commitWork(
        [0], "model_3", {"from": get_account(selected_addresses_index_2[0])}
    )
    tx.wait(1)
    print(f"{selected_workers_2[0]} committed the model update")
    tx = federatedML_contract.commitWork(
        [0], "model_4", {"from": get_account(selected_addresses_index_2[1])}
    )
    tx.wait(1)
    print(f"{selected_workers_2[1]} committed the model update")

    assert federatedML_contract.getPreviousModels() == ["model_3", "model_4"]
    selected_workers_3 = federatedML_contract.getWorkersInRound(2)
    selected_addresses_index_3 = []
    for w in range(1, 7):
        if get_account(w) == selected_workers_3[0]:
            selected_addresses_index_3.append(w)
        if get_account(w) == selected_workers_3[1]:
            selected_addresses_index_3.append(w)

    # Commit secret votes ([1] with salt "salt", calculated with web3)
    secret_vote_0 = 0xAC62CD60050F3120719979941745DE573FF96854BA8CFC458676E7944A50A563
    secret_vote_1 = 0xAC62CD60050F3120719979941745DE573FF96854BA8CFC458676E7944A50A563
    tx = federatedML_contract.commitSecretVote(
        secret_vote_0, {"from": get_account(selected_addresses_index_3[0])}
    )
    tx.wait(1)
    tx = federatedML_contract.commitSecretVote(
        secret_vote_1, {"from": get_account(selected_addresses_index_3[1])}
    )
    tx.wait(1)

    # Check secret votes correctly saved
    assert federatedML_contract.addressToWorkerInfo(
        get_account(selected_addresses_index_3[0])
    )[3] == hex(secret_vote_0)
    assert federatedML_contract.addressToWorkerInfo(
        get_account(selected_addresses_index_3[1])
    )[3] == hex(secret_vote_1)

    # Check disclosure phase
    assert federatedML_contract.state() == 7


@unittest.skip("Passed")
def test_last_round_disclosure_secret_vote():
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
    print(f"{selected_workers_1[0]} committed the model update")
    tx = federatedML_contract.commitWork(
        [], "model_2", {"from": get_account(selected_addresses_index_1[1])}
    )
    tx.wait(1)
    print(f"{selected_workers_1[1]} committed the model update")

    tx = federatedML_contract.fulfillRandomnessTesting(1)
    tx.wait(1)

    selected_workers_2 = federatedML_contract.getWorkersInRound(1)
    selected_addresses_index_2 = []
    for w in range(1, 7):
        if get_account(w) == selected_workers_2[0]:
            selected_addresses_index_2.append(w)
        if get_account(w) == selected_workers_2[1]:
            selected_addresses_index_2.append(w)

    tx = federatedML_contract.commitWork(
        [0], "model_3", {"from": get_account(selected_addresses_index_2[0])}
    )
    tx.wait(1)
    print(f"{selected_workers_2[0]} committed the model update")
    tx = federatedML_contract.commitWork(
        [0], "model_4", {"from": get_account(selected_addresses_index_2[1])}
    )
    tx.wait(1)
    print(f"{selected_workers_2[1]} committed the model update")

    selected_workers_3 = federatedML_contract.getWorkersInRound(2)
    selected_addresses_index_3 = []
    for w in range(1, 7):
        if get_account(w) == selected_workers_3[0]:
            selected_addresses_index_3.append(w)
        if get_account(w) == selected_workers_3[1]:
            selected_addresses_index_3.append(w)

    # Commit secret votes ([1] with salt "salt", calculated with web3)
    secret_vote_0 = 0xAC62CD60050F3120719979941745DE573FF96854BA8CFC458676E7944A50A563
    secret_vote_1 = 0xAC62CD60050F3120719979941745DE573FF96854BA8CFC458676E7944A50A563
    tx = federatedML_contract.commitSecretVote(
        secret_vote_0, {"from": get_account(selected_addresses_index_3[0])}
    )
    tx.wait(1)
    tx = federatedML_contract.commitSecretVote(
        secret_vote_1, {"from": get_account(selected_addresses_index_3[1])}
    )
    tx.wait(1)

    # Disclose secret votes
    tx = federatedML_contract.discloseSecretVote(
        [1], "salt", {"from": get_account(selected_addresses_index_3[0])}
    )
    tx.wait(1)
    tx = federatedML_contract.discloseSecretVote(
        [1], "salt", {"from": get_account(selected_addresses_index_3[1])}
    )
    tx.wait(1)

    # Check votes disclosed correctly assigned
    assert (
        federatedML_contract.addressToWorkerInfo(
            get_account(selected_addresses_index_2[0])
        )[2]
        == 0
    )
    assert (
        federatedML_contract.addressToWorkerInfo(
            get_account(selected_addresses_index_2[1])
        )[2]
        == 2
    )
    # Check task ended state
    assert federatedML_contract.state() == 2
