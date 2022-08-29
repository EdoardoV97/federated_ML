from tabnanny import check
import unittest
from brownie import config, network
from scripts.helpful_scripts import fund_with_link, get_account, get_contract
from scripts.deploy import deploy_FederatedML


# @unittest.skip("Passed")
def test_withdraw():
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
    print(f"Entrance fee is: {worker_fee} Wei = {worker_fee/(10**18)} ETH")
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

    # The winner of the round withdraw
    prev_balance = get_account(selected_addresses_index_1[0]).balance()
    tx = federatedML_contract.withdrawReward(
        {"from": get_account(selected_addresses_index_1[0])}
    )
    tx.wait(1)
    actual_balance = get_account(selected_addresses_index_1[0]).balance()
    print(
        f"Worker{selected_addresses_index_1[0]} correctly withdraw: {actual_balance - prev_balance} wei = {(actual_balance - prev_balance)/10**18} ETH"
    )
    # Check reward
    assert actual_balance - prev_balance == 1666666666666666666
    # The looser of the round withdraw (reward 0)
    prev_balance = get_account(selected_addresses_index_1[1]).balance()
    tx = federatedML_contract.withdrawReward(
        {"from": get_account(selected_addresses_index_1[1])}
    )
    tx.wait(1)
    actual_balance = get_account(selected_addresses_index_1[1]).balance()
    print(
        f"Worker{selected_addresses_index_1[1]} correctly withdraw: {actual_balance - prev_balance} Wei = {(actual_balance - prev_balance)/10**18} ETH"
    )
    # Check no reward
    assert actual_balance - prev_balance == 0

    ranking = federatedML_contract.getRankingInRound(0)
    ranking_addresses_index = []
    for w in ranking:
        for i in range(1, 7):
            if get_account(i) == w:
                ranking_addresses_index.append(i)
    # Check the ranking computed (triggered by the first withdraw)
    assert ranking_addresses_index[0] == 2
    assert ranking_addresses_index[1] == 3
