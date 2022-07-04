import json
from web3 import Web3


CHOSEN_NETWORK = "kovan"
CHOSEN_NETWORK_ID = 42

with open("scripts/Client/client-config.json", "r") as file:
    json_file = json.load(file)
    w3 = Web3(Web3.HTTPProvider(json_file[CHOSEN_NETWORK]["provider"]))
    chain_id = int(json_file[CHOSEN_NETWORK]["chain-id"])
    my_address = json_file[CHOSEN_NETWORK]["address" + str(1)]
    private_key = json_file[CHOSEN_NETWORK]["private-key" + str(1)]


def get_contract_address():
    with open("build/deployments/map.json", "r") as file:
        json_file = json.load(file)
        return json_file[str(CHOSEN_NETWORK_ID)]["FederatedML"][0]


def get_ABI(contract_address):
    with open(
        "build/deployments/"
        + str(CHOSEN_NETWORK_ID)
        + "/"
        + contract_address
        + ".json",
        "r",
    ) as file:
        json_file = json.load(file)
        return json_file["abi"]


def main():
    contract_address = get_contract_address()
    federated_ML = w3.eth.contract(contract_address, abi=get_ABI(contract_address))
    print(f"State is: {federated_ML.functions.state().call()}")

    workers = federated_ML.functions.getWorkersInRound(1).call()
    print(workers)

    result = federated_ML.functions.addressToWorkerInfo(
        "0xfa3e19450b82dFc4300053B2cdB1Cdba88ba8aa6"
    ).call()
    print(result)
    pass


if __name__ == "__main__":
    main()
