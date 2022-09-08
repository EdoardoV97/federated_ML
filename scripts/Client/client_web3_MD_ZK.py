import sys
import requests
from web3 import Web3
import json
import asyncio
import json


class LocalOutput:
    def __init__(self):
        self.model = None
        self.bestKWorkers = list()


class WorkerToEvaluate:
    def __init__(self, weightsFile):
        self.weightsFile = weightsFile
        self.loss = None
        self.accuracy = None


workersToEvaluate = list()
localOutput = LocalOutput()

CHOSEN_NETWORK = "goerli"
CHOSEN_NETWORK_ID = 5
# WORKER_INDEX =

with open("scripts/Client/client-config.json", "r") as file:
    worker_index = sys.argv[1]
    json_file = json.load(file)
    w3 = Web3(Web3.HTTPProvider(json_file[CHOSEN_NETWORK]["provider"]))
    chain_id = int(json_file[CHOSEN_NETWORK]["chain-id"])
    my_address = json_file[CHOSEN_NETWORK]["address" + str(worker_index)]
    private_key = json_file[CHOSEN_NETWORK]["private-key" + str(worker_index)]


def get_contract_address():
    with open("build/deployments/map.json", "r") as file:
        json_file = json.load(file)
        return json_file[str(CHOSEN_NETWORK_ID)]["FederatedML_ZK"][0]


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


def get_models():
    contract_address = get_contract_address()
    federated_ML = w3.eth.contract(contract_address, abi=get_ABI(contract_address))

    modelsHash = federated_ML.functions.getPreviousModels().call()

    download_from_IPFS(modelsHash)
    return modelsHash


def send_response():
    global localOutput
    myModelHash = save_to_IPFS()

    contract_address = get_contract_address()
    federated_ML = w3.eth.contract(contract_address, abi=get_ABI(contract_address))

    not_confirmed = True
    already_redone = False
    while not_confirmed:
        transaction = federated_ML.functions.commitWork(
            localOutput.bestKWorkers,
            myModelHash,
            "dummy_mtrUpdatedModel",
            "0xF6FE2AF6E4EC2F4247E9D536E0B79C2B64538D9DA58C7FC9F8417E8ECFDF58C9",  # Dummy already verified fact
        ).buildTransaction(
            {
                "chainId": chain_id,
                "gasPrice": w3.eth.gas_price,
                "from": my_address,
                "nonce": w3.eth.getTransactionCount(my_address),
            }
        )
        signed_transaction = w3.eth.account.sign_transaction(
            transaction, private_key=private_key
        )
        tx_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
        print(f"Pushing new model. Tx hash: {tx_hash}")
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        print(tx_receipt)
        print("DONE!")
        if not already_redone:
            redo = input("REDO? y/n")
            if redo == "n":
                not_confirmed = False
            else:
                already_redone = True
        else:
            not_confirmed = False


def save_to_IPFS():
    global localOutput
    response = requests.post(
        "http://127.0.0.1:5001/api/v0/add",
        files={localOutput.model: open(localOutput.model, "rb")},
    )
    p = response.json()
    hash = p["Hash"]
    print(hash)
    return hash


def download_from_IPFS(modelsHash):
    for hash in modelsHash:
        params = {"arg": hash}
        response = requests.post("http://127.0.0.1:5001/api/v0/get", params=params)
        print(response)
        with open("./scripts/Client/models/" + str(hash) + ".h5", "wb") as f:
            f.write(response.content)


def register():
    contract_address = get_contract_address()

    federated_ML = w3.eth.contract(contract_address, abi=get_ABI(contract_address))
    fee = federated_ML.functions.entranceFee().call()
    print(f"Registration fee is: {fee}")
    transaction = federated_ML.functions.register(
        "dummy_mtrDataset" + str(worker_index)
    ).buildTransaction(
        {
            "chainId": chain_id,
            "gasPrice": w3.eth.gas_price,
            "from": my_address,
            "nonce": w3.eth.getTransactionCount(my_address),
            "value": fee,
        }
    )
    signed_transaction = w3.eth.account.sign_transaction(
        transaction, private_key=private_key
    )
    tx_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    print("Registering...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print("DONE!")


def check_if_in_round(workersInRound):
    for address in workersInRound:
        if str(address) == my_address:
            return True
    return False


# asynchronous defined function to loop
# this loop sets up an event filter and is looking for new entires for the events
# this loop runs on a poll interval
async def log_loop(event_filters, poll_interval):
    while True:
        i = 0
        for event_filter in event_filters:
            for event in event_filter.get_new_entries():
                if check_if_in_round(event.args.workers) == True:
                    if i == 0:  # case of RoundWorkersSelection
                        return True
                    else:
                        # case of LastRoundWorkersSelection
                        return False
            i = i + 1
        await asyncio.sleep(poll_interval)


def listen_to_selection_events():
    contract_address = get_contract_address()
    federated_ML = w3.eth.contract(contract_address, abi=get_ABI(contract_address))
    event_filters = []
    event_filters.append(
        federated_ML.events.RoundWorkersSelection.createFilter(fromBlock="latest")
    )
    event_filters.append(
        federated_ML.events.LastRoundWorkersSelection.createFilter(fromBlock="latest")
    )
    loop = asyncio.get_event_loop()
    try:
        ret_val = loop.run_until_complete(asyncio.gather(log_loop(event_filters, 4)))
        if ret_val[0] == True:
            print("\n[!] I have been selected for the current round")
            round(loop)
        else:
            print("\n[!] I have been selected for the current round(LAST)")
            last_round(loop)
    finally:
        # close loop to free up system resources
        loop.close()


def round(loop):
    # Get the models to evaluate
    models_path = get_models()
    for p in models_path:
        w = WorkerToEvaluate(p)
        workersToEvaluate.append(w)

    # Do local training
    global localOutput
    input(
        "Press any key after adding the weights file in the models' folder. The name must be the modelOfWorker"
        + worker_index
        + ".txt"
    )
    localOutput.model = (
        "scripts/Client/models/modelOfWorker" + str(worker_index) + ".txt"
    )
    localOutput.bestKWorkers = [
        int(vote) for vote in input("Copy and paste the votes array\n").split(",")
    ]

    # Send response to the SC
    send_response()
    listen_to_end_task_event(loop)


def last_round(loop):
    # Get the models to evaluate
    models_path = get_models()
    for p in models_path:
        w = WorkerToEvaluate(p)
        workersToEvaluate.append(w)

    # Do local training
    global localOutput
    localOutput.bestKWorkers = [
        int(vote) for vote in input("Copy and paste the votes array\n").split(",")
    ]

    commit_secret_vote()
    listen_to_disclosure_event(loop)
    listen_to_end_task_event(loop)


def commit_secret_vote():
    global localOutput
    contract_address = get_contract_address()
    federated_ML = w3.eth.contract(contract_address, abi=get_ABI(contract_address))

    keccakHash = w3.solidityKeccak(
        ["uint16[]", "string"], [localOutput.bestKWorkers, "ciao"]
    )

    transaction = federated_ML.functions.commitSecretVote(keccakHash).buildTransaction(
        {
            "chainId": chain_id,
            "gasPrice": w3.eth.gas_price,
            "from": my_address,
            "nonce": w3.eth.getTransactionCount(my_address),
        }
    )

    signed_transaction = w3.eth.account.sign_transaction(
        transaction, private_key=private_key
    )
    tx_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    print("Committing secret vote...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(
        tx_hash
    )  # May be useful to comment to avoid starting listening lately w.r.t. the disclosure event emit
    print("DONE!")


# asynchronous defined function to loop
# this loop sets up an event filter and is looking for new entires for the events
# this loop runs on a poll interval
async def log_loop_disclosure(event_filter, poll_interval):
    while True:
        for _ in event_filter.get_new_entries():
            disclose_secret_vote()
            return
        await asyncio.sleep(poll_interval)


def listen_to_disclosure_event(loop):
    contract_address = get_contract_address()
    federated_ML = w3.eth.contract(contract_address, abi=get_ABI(contract_address))
    event_filter = federated_ML.events.LastRoundDisclosurePhase.createFilter(
        fromBlock="latest"
    )
    # loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(asyncio.gather(log_loop_disclosure(event_filter, 2)))
    finally:
        # close loop to free up system resources
        # loop.close()
        pass


def disclose_secret_vote():
    global localOutput
    contract_address = get_contract_address()
    federated_ML = w3.eth.contract(contract_address, abi=get_ABI(contract_address))

    transaction = federated_ML.functions.discloseSecretVote(
        localOutput.bestKWorkers,
        "ciao",
        "0xF6FE2AF6E4EC2F4247E9D536E0B79C2B64538D9DA58C7FC9F8417E8ECFDF58C9",  # Dummy already verified fact
    ).buildTransaction(
        {
            "chainId": chain_id,
            "gasPrice": w3.eth.gas_price,
            "from": my_address,
            "nonce": w3.eth.getTransactionCount(my_address),
        }
    )

    signed_transaction = w3.eth.account.sign_transaction(
        transaction, private_key=private_key
    )
    tx_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    print("Disclosing vote...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print("DONE!")


# asynchronous defined function to loop
# this loop sets up an event filter and is looking for new entires for the events
# this loop runs on a poll interval
async def log_loop_task_ended(event_filter, poll_interval):
    while True:
        for _ in event_filter.get_new_entries():
            try_withdraw_reward()
            return
        await asyncio.sleep(poll_interval)


def listen_to_end_task_event(loop):
    contract_address = get_contract_address()
    federated_ML = w3.eth.contract(contract_address, abi=get_ABI(contract_address))
    event_filter = federated_ML.events.TaskEnded.createFilter(fromBlock="latest")
    # loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(asyncio.gather(log_loop_task_ended(event_filter, 2)))
    finally:
        # close loop to free up system resources
        # loop.close()
        pass


def try_withdraw_reward():
    balance_before = w3.eth.get_balance(my_address)
    print(f"Balance before: {balance_before}")

    contract_address = get_contract_address()
    federated_ML = w3.eth.contract(contract_address, abi=get_ABI(contract_address))

    transaction = federated_ML.functions.withdrawReward().buildTransaction(
        {
            "chainId": chain_id,
            "gasPrice": w3.eth.gas_price,
            "from": my_address,
            "nonce": w3.eth.getTransactionCount(my_address),
        }
    )

    signed_transaction = w3.eth.account.sign_transaction(
        transaction, private_key=private_key
    )
    tx_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    print("Reward asked...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    print("DONE!")

    balance_after = w3.eth.get_balance(my_address)
    print(f"Balance after: {balance_after}")


def main():
    # Register to the SC
    register()

    # Listen to the events of RoundWorkersSelection and LastRoundWorkersSelection
    print("Listening to worker selection events!")
    listen_to_selection_events()


if __name__ == "__main__":
    main()
