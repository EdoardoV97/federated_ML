from brownie import accounts, config, FederatedML, network
from scripts.helpful_scripts import get_account

TASK_SCRIPT = ""
NUM_OF_WORKERS = 6
VOTE_MINUTES = 60
REGISTRATION_MINUTES = 60
INITIAL_MODEL_HASH = None  # TODO generate an initial model


def deploy_FederatedML():
    vrf_coordinator = config["networks"][network.show_active()]["vrf_coordinator"]
    link_token = config["networks"][network.show_active()]["link_token"]
    oracle_fee = config["networks"][network.show_active()]["oracle_fee"]
    keyhash = config["networks"][network.show_active()]["keyhash"]
    api_oracle = config["networks"][network.show_active()]["api_oracle"]
    job_id = config["networks"][network.show_active()]["job_id"]

    account = get_account()
    # Deploy
    federatedML_contract = FederatedML.deploy(
        TASK_SCRIPT,
        NUM_OF_WORKERS,
        VOTE_MINUTES,
        REGISTRATION_MINUTES,
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

    # Fund the bounty
    federatedML_contract.fund({"from": account, "value": 1})  # 1 ETH

    # Stop funding phase
    federatedML_contract.stopFunding({"from": account})


def main():
    deploy_FederatedML()
