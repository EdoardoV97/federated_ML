from brownie import accounts, config, FederatedML, FederatedML_ZK, network
from scripts.helpful_scripts import fund_with_link, get_account, get_contract


# NUM_OF_WORKERS = 6
# VOTE_MINUTES = 60
# REGISTRATION_MINUTES = 60
INITIAL_MODEL_HASH = "QmeGCXqw21Y7g1w53GtzAWz8bBzHN7ES1PMS54RH44X56i"


def deploy_FederatedML():
    vrf_coordinator = get_contract("vrf_coordinator").address
    link_token = get_contract("link_token").address
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

    return federatedML_contract


def deploy_FederatedML_ZK():
    vrf_coordinator = get_contract("vrf_coordinator").address
    link_token = get_contract("link_token").address
    oracle_fee = config["networks"][network.show_active()]["fee"]
    keyhash = config["networks"][network.show_active()]["keyhash"]
    api_oracle = config["networks"][network.show_active()]["api_oracle"]
    job_id = config["networks"][network.show_active()]["job_id"]

    account = get_account()

    # Deploy
    federatedML_ZK_contract = FederatedML_ZK.deploy(
        "QmNssyBLsb3nvVf8JxaG1rdbQot8agUwoTUaF6u58KQr4A",
        vrf_coordinator,
        link_token,
        oracle_fee,
        keyhash,
        api_oracle,
        job_id,
        {"from": account},
    )
    print(f"Contract deployed to: {federatedML_ZK_contract.address}")

    return federatedML_ZK_contract


def main():
    deploy_FederatedML()
