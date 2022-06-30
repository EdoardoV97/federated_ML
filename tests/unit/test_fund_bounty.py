from brownie import accounts, config, FederatedML, network
from scripts.helpful_scripts import fund_with_link, get_account

INITIAL_MODEL_HASH = None  # TODO generate an initial model


def test_fund_FederatedML():
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

    # Fund with link
    tx = fund_with_link(
        federatedML_contract.address, get_account(key=True)
    )  # attenzione
    tx.wait(1)

    # Fund the bounty
    federatedML_contract.fund({"from": account, "value": 1})  # 1 ETH

    # Stop funding phase
    # federatedML_contract.stopFunding({"from": account})
