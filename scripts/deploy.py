from brownie import accounts, config, FederatedML, network


def deploy_ML():
    account = get_account()
    # Deploy
    federatedML_contract = FederatedML.deploy(10, {"from": account})

    # Read the stored value
    # print(federatedML_contract.model(0))



    # Store a new value


    # Wait 1 block to complete, then read the stored value


def get_account():
    if network.show_active() == "development":
        return accounts[0]
    else:
        return accounts.add(config["wallets"]["from_key"])


def main():
    deploy_ML()