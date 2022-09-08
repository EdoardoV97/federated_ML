from tabnanny import check
import unittest
from brownie import config, network
from scripts.helpful_scripts import fund_with_link, get_account, get_contract
from scripts.deploy import deploy_FederatedML


@unittest.skip("Passed")
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
    for w in range(1, 31):
        tx = federatedML_contract.register(
            {"from": get_account(w), "value": worker_fee}
        )
        print(f"Worker{w} registered!")
        tx.wait(1)
    print(f"SC balance: {federatedML_contract.getBalance()}")
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

    # Check rewards
    prev_balance = get_account(selected_addresses_index_1[0]).balance()
    tx = federatedML_contract.withdrawReward(
        {"from": get_account(selected_addresses_index_1[0])}
    )
    tx.wait(1)
    actual_balance = get_account(selected_addresses_index_1[0]).balance()
    print(
        f"Worker{selected_addresses_index_1[0]} correctly withdraw: {actual_balance - prev_balance} wei = {(actual_balance - prev_balance)/10**18} ETH"
    )
    assert actual_balance - prev_balance == 42857142857142857

    prev_balance = get_account(selected_addresses_index_1[1]).balance()
    tx = federatedML_contract.withdrawReward(
        {"from": get_account(selected_addresses_index_1[1])}
    )
    tx.wait(1)
    actual_balance = get_account(selected_addresses_index_1[1]).balance()
    print(
        f"Worker{selected_addresses_index_1[1]} correctly withdraw: {actual_balance - prev_balance} wei = {(actual_balance - prev_balance)/10**18} ETH"
    )
    assert actual_balance - prev_balance == 14285714285714285

    prev_balance = get_account(selected_addresses_index_1[2]).balance()
    tx = federatedML_contract.withdrawReward(
        {"from": get_account(selected_addresses_index_1[2])}
    )
    tx.wait(1)
    actual_balance = get_account(selected_addresses_index_1[2]).balance()
    print(
        f"Worker{selected_addresses_index_1[2]} correctly withdraw: {actual_balance - prev_balance} wei = {(actual_balance - prev_balance)/10**18} ETH"
    )
    assert actual_balance - prev_balance == 71428571428571428

    prev_balance = get_account(selected_addresses_index_1[3]).balance()
    tx = federatedML_contract.withdrawReward(
        {"from": get_account(selected_addresses_index_1[3])}
    )
    tx.wait(1)
    actual_balance = get_account(selected_addresses_index_1[3]).balance()
    print(
        f"Worker{selected_addresses_index_1[3]} correctly withdraw: {actual_balance - prev_balance} wei = {(actual_balance - prev_balance)/10**18} ETH"
    )
    assert actual_balance - prev_balance == 128571428571428571

    prev_balance = get_account(selected_addresses_index_1[4]).balance()
    tx = federatedML_contract.withdrawReward(
        {"from": get_account(selected_addresses_index_1[4])}
    )
    tx.wait(1)
    actual_balance = get_account(selected_addresses_index_1[4]).balance()
    print(
        f"Worker{selected_addresses_index_1[4]} correctly withdraw: {actual_balance - prev_balance} wei = {(actual_balance - prev_balance)/10**18} ETH"
    )
    assert actual_balance - prev_balance == 99999999999999999

    for i in range(5, 10):
        # The loosers of the round withdraw (reward 0)
        prev_balance = get_account(selected_addresses_index_1[i]).balance()
        tx = federatedML_contract.withdrawReward(
            {"from": get_account(selected_addresses_index_1[i])}
        )
        tx.wait(1)
        actual_balance = get_account(selected_addresses_index_1[i]).balance()
        print(
            f"Worker{selected_addresses_index_1[i]} correctly withdraw: {actual_balance - prev_balance} Wei = {(actual_balance - prev_balance)/10**18} ETH"
        )
        # Check no reward
        assert actual_balance - prev_balance == 0
    print(f"SC balance: {federatedML_contract.getBalance()}")
    ranking = federatedML_contract.getRankingInRound(0)
    ranking_addresses_index = []
    for w in ranking:
        for i in range(1, 31):
            if get_account(i) == w:
                ranking_addresses_index.append(i)
    # Check the ranking computed (triggered by the first withdraw)
    assert ranking_addresses_index == [5, 6, 4, 2, 3, 10, 11, 9, 7, 8]

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
        print(f"Worker{selected_addresses_index_3[i]} disclosed secret vote")

    # Check rewards 2nd round
    prev_balance = get_account(selected_addresses_index_2[0]).balance()
    tx = federatedML_contract.withdrawReward(
        {"from": get_account(selected_addresses_index_2[0])}
    )
    tx.wait(1)
    actual_balance = get_account(selected_addresses_index_2[0]).balance()
    print(
        f"Worker{selected_addresses_index_2[0]} correctly withdraw: {actual_balance - prev_balance} wei = {(actual_balance - prev_balance)/10**18} ETH"
    )
    assert actual_balance - prev_balance == 42857142857142857

    prev_balance = get_account(selected_addresses_index_2[1]).balance()
    tx = federatedML_contract.withdrawReward(
        {"from": get_account(selected_addresses_index_2[1])}
    )
    tx.wait(1)
    actual_balance = get_account(selected_addresses_index_2[1]).balance()
    print(
        f"Worker{selected_addresses_index_2[1]} correctly withdraw: {actual_balance - prev_balance} wei = {(actual_balance - prev_balance)/10**18} ETH"
    )
    assert actual_balance - prev_balance == 14285714285714285

    prev_balance = get_account(selected_addresses_index_2[2]).balance()
    tx = federatedML_contract.withdrawReward(
        {"from": get_account(selected_addresses_index_2[2])}
    )
    tx.wait(1)
    actual_balance = get_account(selected_addresses_index_2[2]).balance()
    print(
        f"Worker{selected_addresses_index_2[2]} correctly withdraw: {actual_balance - prev_balance} wei = {(actual_balance - prev_balance)/10**18} ETH"
    )
    assert actual_balance - prev_balance == 71428571428571428

    prev_balance = get_account(selected_addresses_index_2[3]).balance()
    tx = federatedML_contract.withdrawReward(
        {"from": get_account(selected_addresses_index_2[3])}
    )
    tx.wait(1)
    actual_balance = get_account(selected_addresses_index_2[3]).balance()
    print(
        f"Worker{selected_addresses_index_2[3]} correctly withdraw: {actual_balance - prev_balance} wei = {(actual_balance - prev_balance)/10**18} ETH"
    )
    assert actual_balance - prev_balance == 128571428571428571

    prev_balance = get_account(selected_addresses_index_2[4]).balance()
    tx = federatedML_contract.withdrawReward(
        {"from": get_account(selected_addresses_index_2[4])}
    )
    tx.wait(1)
    actual_balance = get_account(selected_addresses_index_2[4]).balance()
    print(
        f"Worker{selected_addresses_index_2[4]} correctly withdraw: {actual_balance - prev_balance} wei = {(actual_balance - prev_balance)/10**18} ETH"
    )
    assert actual_balance - prev_balance == 99999999999999999

    for i in range(5, 10):
        # The loosers of the round withdraw (reward 0)
        prev_balance = get_account(selected_addresses_index_2[i]).balance()
        tx = federatedML_contract.withdrawReward(
            {"from": get_account(selected_addresses_index_2[i])}
        )
        tx.wait(1)
        actual_balance = get_account(selected_addresses_index_2[i]).balance()
        print(
            f"Worker{selected_addresses_index_2[i]} correctly withdraw: {actual_balance - prev_balance} Wei = {(actual_balance - prev_balance)/10**18} ETH"
        )
        # Check no reward
        assert actual_balance - prev_balance == 0
    print(f"SC balance: {federatedML_contract.getBalance()}")
    # Check rewards last round
    prev_balance = get_account(selected_addresses_index_3[5]).balance()
    tx = federatedML_contract.withdrawReward(
        {"from": get_account(selected_addresses_index_3[5])}
    )
    tx.wait(1)
    actual_balance = get_account(selected_addresses_index_3[5]).balance()
    print(
        f"Worker{selected_addresses_index_3[5]} correctly withdraw: {actual_balance - prev_balance} wei = {(actual_balance - prev_balance)/10**18} ETH"
    )
    assert actual_balance - prev_balance == 99999999999999999

    prev_balance = get_account(selected_addresses_index_3[6]).balance()
    tx = federatedML_contract.withdrawReward(
        {"from": get_account(selected_addresses_index_3[6])}
    )
    tx.wait(1)
    actual_balance = get_account(selected_addresses_index_3[6]).balance()
    print(
        f"Worker{selected_addresses_index_3[6]} correctly withdraw: {actual_balance - prev_balance} wei = {(actual_balance - prev_balance)/10**18} ETH"
    )
    assert actual_balance - prev_balance == 128571428571428571

    prev_balance = get_account(selected_addresses_index_3[7]).balance()
    tx = federatedML_contract.withdrawReward(
        {"from": get_account(selected_addresses_index_3[7])}
    )
    tx.wait(1)
    actual_balance = get_account(selected_addresses_index_3[7]).balance()
    print(
        f"Worker{selected_addresses_index_3[7]} correctly withdraw: {actual_balance - prev_balance} wei = {(actual_balance - prev_balance)/10**18} ETH"
    )
    assert actual_balance - prev_balance == 71428571428571428

    prev_balance = get_account(selected_addresses_index_3[8]).balance()
    tx = federatedML_contract.withdrawReward(
        {"from": get_account(selected_addresses_index_3[8])}
    )
    tx.wait(1)
    actual_balance = get_account(selected_addresses_index_3[8]).balance()
    print(
        f"Worker{selected_addresses_index_3[8]} correctly withdraw: {actual_balance - prev_balance} wei = {(actual_balance - prev_balance)/10**18} ETH"
    )
    assert actual_balance - prev_balance == 14285714285714285

    prev_balance = get_account(selected_addresses_index_3[9]).balance()
    tx = federatedML_contract.withdrawReward(
        {"from": get_account(selected_addresses_index_3[9])}
    )
    tx.wait(1)
    actual_balance = get_account(selected_addresses_index_3[9]).balance()
    print(
        f"Worker{selected_addresses_index_3[9]} correctly withdraw: {actual_balance - prev_balance} wei = {(actual_balance - prev_balance)/10**18} ETH"
    )
    assert actual_balance - prev_balance == 42857142857142837
    print(federatedML_contract.getBalance())

    for i in range(0, 5):
        # The loosers of the round withdraw (reward 0)
        prev_balance = get_account(selected_addresses_index_3[i]).balance()
        tx = federatedML_contract.withdrawReward(
            {"from": get_account(selected_addresses_index_3[i])}
        )
        tx.wait(1)
        actual_balance = get_account(selected_addresses_index_3[i]).balance()
        print(
            f"Worker{selected_addresses_index_3[i]} correctly withdraw: {actual_balance - prev_balance} Wei = {(actual_balance - prev_balance)/10**18} ETH"
        )
        # Check no reward
        assert actual_balance - prev_balance == 0
