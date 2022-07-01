import unittest
from brownie import accounts, config, FederatedML, network
from scripts.helpful_scripts import fund_with_link, get_account

INITIAL_MODEL_HASH = None  # TODO generate an initial model

# @unittest.skip("Passed")
def test_register():
    vrf_coordinator = config["networks"][network.show_active()]["vrf_coordinator"]
    link_token = config["networks"][network.show_active()]["link_token"]
    oracle_fee = config["networks"][network.show_active()]["fee"]
    keyhash = config["networks"][network.show_active()]["keyhash"]
    api_oracle = config["networks"][network.show_active()]["api_oracle"]
    job_id = config["networks"][network.show_active()]["job_id"]

    account = get_account()

    # Deploy
    federatedML_contract = FederatedML.deploy(
        INITIAL_MODEL_HASH,
        vrf_coordinator,
        link_token,
        oracle_fee,
        keyhash,
        api_oracle,
        job_id,
        {"from": account},
    )
    print(f"Contract deployed to: {federatedML_contract.address}")

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
    fee = federatedML_contract.entranceFee()
    print(fee)
