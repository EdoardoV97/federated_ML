from brownie import accounts, config, IPFS, network


def deploy_ipfs():
    account = get_account()
    # Deploy
    ipfs = IPFS.deploy({"from": account})

    # Read the stored value


    # Store a new value


    # Wait 1 block to complete, then read the stored value


def get_account():
    if network.show_active() == "development":
        return accounts[0]
    else:
        return accounts.add(config["wallets"]["from_key"])


def main():
    deploy_ipfs()