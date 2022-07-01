import unittest
from brownie import config, network
from scripts.helpful_scripts import fund_with_link, get_account
from scripts.deploy import deploy_FederatedML

INITIAL_MODEL_HASH = None  # TODO generate an initial model


# def deploy():
#     vrf_coordinator = config["networks"][network.show_active()]["vrf_coordinator"]
#     link_token = config["networks"][network.show_active()]["link_token"]
#     oracle_fee = config["networks"][network.show_active()]["fee"]
#     keyhash = config["networks"][network.show_active()]["keyhash"]
#     api_oracle = config["networks"][network.show_active()]["api_oracle"]
#     job_id = config["networks"][network.show_active()]["job_id"]

#     account = get_account()

#     # Deploy
#     federatedML_contract = FederatedML.deploy(
#         INITIAL_MODEL_HASH,
#         vrf_coordinator,
#         link_token,
#         oracle_fee,
#         keyhash,
#         api_oracle,
#         job_id,
#         {"from": account},
#     )
#     print(f"Contract deployed to: {federatedML_contract.address}")

#     return federatedML_contract


# @unittest.skip("Passed")
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
    print(worker_fee)

    # Register the workers
    for w in range(1, 7):
        tx = federatedML_contract.register(
            {"from": get_account(w), "value": worker_fee}
        )
        print(f"Worker{w} registered!")
        tx.wait(1)

    # info = federatedML_contract.addressToWorkerInfo(1)
    # print(info)


# def test_unregister():
