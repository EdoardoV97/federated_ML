import asyncio
import json
from web3 import Web3

CHOSEN_NETWORK = "kovan"
CHOSEN_NETWORK_ID = 42

with open("scripts/Client/client-config.json", "r") as file:
    json_file = json.load(file)
    w3 = Web3(Web3.HTTPProvider(json_file[CHOSEN_NETWORK]["provider"]))
    chain_id = int(json_file[CHOSEN_NETWORK]["chain-id"])
    my_address = json_file[CHOSEN_NETWORK]["address"]
    private_key = json_file[CHOSEN_NETWORK]["private-key"]


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


async def log_loop(event_filter, poll_interval):
    print("\n[!] Searching for events...")
    while True:
        for event in event_filter.get_new_entries():
            print("\nEvent Received!")
            print("Selected workers address are:")
            print(str(event.args.workers[0]))
            print(str(event.args.workers[1]))
            return
        # print("[!] No event found, starting the loop again in a while...")
        await asyncio.sleep(poll_interval)


def main():
    contract_address = get_contract_address()
    federated_ML = w3.eth.contract(contract_address, abi=get_ABI(contract_address))
    print(f"[!] Correctly retrieved the SC: {contract_address}")
    event_filter = federated_ML.events.RoundWorkersSelection.createFilter(
        fromBlock="latest",
    )
    print(event_filter)
    loop = asyncio.get_event_loop()
    try:
        print("[!] Starting the loop")
        loop.run_until_complete(asyncio.gather(log_loop(event_filter, 2)))
    finally:
        # close loop to free up system resources
        loop.close()


if __name__ == "__main__":
    main()
