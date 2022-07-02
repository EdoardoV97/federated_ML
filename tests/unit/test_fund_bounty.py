import unittest
from brownie import config, network
from scripts.deploy import deploy_FederatedML
from scripts.helpful_scripts import fund_with_link, get_account


@unittest.skip("Passed")
def test_fund_FederatedML():
    account = get_account()
    federatedML_contract = deploy_FederatedML()
    oracle_fee = config["networks"][network.show_active()]["fee"]

    link_amount = oracle_fee * 10  # 0.1 * 10 = 1 LINK

    # Fund with link
    tx = fund_with_link(
        federatedML_contract.address, get_account(key=True), amount=link_amount
    )  # attenzione
    tx.wait(1)

    # Fund the bounty
    fund_quantity = 1 * 10 ** 18  # 1 ETH
    tx = federatedML_contract.fund({"from": account, "value": fund_quantity})
    tx.wait(1)
    assert fund_quantity == federatedML_contract.balance()

    # Stop funding phase
    tx = federatedML_contract.stopFunding({"from": account})
    tx.wait(1)


@unittest.skip("Passed")
def test_unfund():
    account = get_account()
    federatedML_contract = deploy_FederatedML()

    # Fund the bounty
    fund_quantity = 1 * 10 ** 18  # 1 ETH
    tx = federatedML_contract.fund({"from": account, "value": fund_quantity})
    tx.wait(1)
    assert fund_quantity == federatedML_contract.balance()

    # Unfund
    tx = federatedML_contract.unfund()
    tx.wait(1)
    assert federatedML_contract.balance() == 0
