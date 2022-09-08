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
    for w in range(1, 31):
        tx = federatedML_contract.register(
            {"from": get_account(w), "value": worker_fee}
        )
        print(f"Worker{w} registered!")
        tx.wait(1)
    tx = federatedML_contract.fulfillRandomnessTesting(1)
    tx.wait(1)
    selected_workers_1 = federatedML_contract.getWorkersInRound(0)
    selected_addresses_index_1 = []
    for w in range(1, 31):
        for i in range(0, 10):
            if get_account(w) == selected_workers_1[i]:
                selected_addresses_index_1.append(w)

    for w in range(0, 10):
        tx = federatedML_contract.commitWork(
            [], "model_" + str(w), {"from": get_account(selected_addresses_index_1[w])}
        )
        tx.wait(1)
        print(f"Worker{selected_addresses_index_1[w]} committed the model update")

    tx = federatedML_contract.fulfillRandomnessTesting(1)
    tx.wait(1)

    selected_workers_2 = federatedML_contract.getWorkersInRound(1)
    selected_addresses_index_2 = []
    for w in range(1, 31):
        for i in range(0, 10):
            if get_account(w) == selected_workers_2[i]:
                selected_addresses_index_2.append(w)

    for w in range(0, 10):
        tx = federatedML_contract.commitWork(
            [0, 1, 2, 3, 4],
            "model_1" + str(w),
            {"from": get_account(selected_addresses_index_2[w])},
        )
        tx.wait(1)
        print(f"Worker{selected_addresses_index_2[w]} committed the model update")

    assert federatedML_contract.getPreviousModels() == [
        "model_10",
        "model_11",
        "model_12",
        "model_13",
        "model_14",
        "model_15",
        "model_16",
        "model_17",
        "model_18",
        "model_19",
    ]
    selected_workers_3 = federatedML_contract.getWorkersInRound(2)
    selected_addresses_index_3 = []
    for w in range(1, 31):
        for i in range(0, 10):
            if get_account(w) == selected_workers_3[i]:
                selected_addresses_index_3.append(w)

    # Commit secret votes ([1] with salt "salt", calculated with web3)
    secret_vote = 0x44314D48435679BC3ABA55E1C74CA86ADE9FD49A742D7239849A287468EE008C
    for i in range(0, 10):
        tx = federatedML_contract.commitSecretVote(
            secret_vote, {"from": get_account(selected_addresses_index_3[i])}
        )
        tx.wait(1)

    # Check secret votes correctly saved
    for i in range(0, 10):
        assert federatedML_contract.addressToWorkerInfo(
            get_account(selected_addresses_index_3[i])
        )[3] == hex(secret_vote)

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
    for w in range(1, 31):
        tx = federatedML_contract.register(
            {"from": get_account(w), "value": worker_fee}
        )
        print(f"Worker{w} registered!")
        tx.wait(1)

    tx = federatedML_contract.fulfillRandomnessTesting(1)
    tx.wait(1)
    selected_workers_1 = federatedML_contract.getWorkersInRound(0)
    selected_addresses_index_1 = []
    for w in range(1, 31):
        for i in range(0, 10):
            if get_account(w) == selected_workers_1[i]:
                selected_addresses_index_1.append(w)

    for w in range(0, 10):
        tx = federatedML_contract.commitWork(
            [0, 1, 2, 3, 4],
            "model_1" + str(w),
            {"from": get_account(selected_addresses_index_1[w])},
        )
        tx.wait(1)
        print(f"Worker{selected_addresses_index_1[w]} committed the model update")

    tx = federatedML_contract.fulfillRandomnessTesting(1)
    tx.wait(1)

    selected_workers_2 = federatedML_contract.getWorkersInRound(1)
    selected_addresses_index_2 = []
    for w in range(1, 31):
        for i in range(0, 10):
            if get_account(w) == selected_workers_2[i]:
                selected_addresses_index_2.append(w)

    for w in range(0, 10):
        tx = federatedML_contract.commitWork(
            [0, 1, 2, 3, 4],
            "model_1" + str(w),
            {"from": get_account(selected_addresses_index_2[w])},
        )
        tx.wait(1)
        print(f"Worker{selected_addresses_index_2[w]} committed the model update")

    selected_workers_3 = federatedML_contract.getWorkersInRound(2)
    selected_addresses_index_3 = []
    for w in range(1, 31):
        for i in range(0, 10):
            if get_account(w) == selected_workers_3[i]:
                selected_addresses_index_3.append(w)

    # Commit secret votes ([0,1,2,3,4] with salt "salt", calculated with web3)
    secret_vote = 0x44314D48435679BC3ABA55E1C74CA86ADE9FD49A742D7239849A287468EE008C
    for i in range(0, 10):
        tx = federatedML_contract.commitSecretVote(
            secret_vote, {"from": get_account(selected_addresses_index_3[i])}
        )
        tx.wait(1)

    # Disclose secret votes
    for i in range(0, 10):
        tx = federatedML_contract.discloseSecretVote(
            [0, 1, 2, 3, 4],
            "salt",
            {"from": get_account(selected_addresses_index_3[i])},
        )
        tx.wait(1)

    # Check votes disclosed correctly assigned
    for w in range(1, 5):
        assert (
            federatedML_contract.addressToWorkerInfo(
                get_account(selected_addresses_index_2[w])
            )[2]
            == 10
        )
    for w in range(5, 10):
        assert (
            federatedML_contract.addressToWorkerInfo(
                get_account(selected_addresses_index_2[w])
            )[2]
            == 0
        )
    # Check task ended state
    assert federatedML_contract.state() == 2
