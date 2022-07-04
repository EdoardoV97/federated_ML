import asyncio
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

    # workers = federated_ML.functions.getWorkersInRound(2).call()
    # print(workers)

    # result = federated_ML.functions.addressToWorkerInfo(
    #     "0xD302BDD84E9EC8569E5fC6C398aAC9536d9fB38C"
    # ).call()
    # print(result)


#     event_filter = federated_ML.events.LastRoundDisclosurePhase.createFilter(
#         fromBlock="latest"
#     )
#     loop = asyncio.get_event_loop()
#     try:
#         loop.run_until_complete(asyncio.gather(log_loop_disclosure(event_filter, 2)))
#     finally:
#         # close loop to free up system resources
#         loop.close()


# async def log_loop_disclosure(event_filter, poll_interval):
#     while True:
#         for e in event_filter.get_new_entries():
#             print(f"Received!!! {e}")
#             return
#         await asyncio.sleep(poll_interval)


if __name__ == "__main__":
    main()
