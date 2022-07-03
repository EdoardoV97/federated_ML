import requests
from client_ml import LocalOutput, WorkerToEvaluate, run_learning
from web3 import Web3
import json
import asyncio

workersToEvaluate: list
localOutput: LocalOutput = None

CHOSEN_NETWORK = "kovan"
CHOSEN_NETWORK_ID = 42
WORKER_INDEX = 5

with open("scripts/Client/client-config.json", "r") as file:
    json_file = json.load(file)
    w3 = Web3(Web3.HTTPProvider(json_file[CHOSEN_NETWORK]["provider"]))
    chain_id = int(json_file[CHOSEN_NETWORK]["chain-id"])
    my_address = json_file[CHOSEN_NETWORK]["address" + str(WORKER_INDEX)]
    private_key = json_file[CHOSEN_NETWORK]["private-key" + str(WORKER_INDEX)]


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


def get_models():
    contract_address = get_contract_address()
    federated_ML = w3.eth.contract(contract_address, abi=get_ABI(contract_address))

    modelsHash = federated_ML.functions.getPreviousModels().call()

    download_from_IPFS(modelsHash)
    return modelsHash


def send_response():
    myModelHash = save_to_IPFS()

    contract_address = get_contract_address()
    federated_ML = w3.eth.contract(contract_address, abi=get_ABI(contract_address))

    transaction = federated_ML.functions.commitWork(
        localOutput.bestKWorkers, myModelHash
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
    print("Pushing new model...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print("DONE!")


def save_to_IPFS():
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
        with open(str(hash) + ".h5", "wb") as f:
            f.write(response.content)


def register():
    contract_address = get_contract_address()

    federated_ML = w3.eth.contract(contract_address, abi=get_ABI(contract_address))
    fee = federated_ML.functions.entranceFee().call()
    print(f"Registration fee is: {fee}")
    transaction = federated_ML.functions.register().buildTransaction(
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
                    else:  # case of LastRoundWorkersSelection
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
        ret_val = loop.run_until_complete(asyncio.gather(log_loop(event_filters, 2)))
        if ret_val == True:
            print("[!] I have been selected for the current round")
            round()
        else:
            print("[!] I have been selected for the current round(LAST)")
            last_round()
    finally:
        # close loop to free up system resources
        loop.close()


def round():
    # Get the models to evaluate
    models_path = get_models()
    for p in models_path:
        w = WorkerToEvaluate(p)
        workersToEvaluate.append(w)

    # Do local training
    localOutput = run_learning(workersToEvaluate, False)

    # Send response to the SC
    send_response()


def last_round():
    # Get the models to evaluate
    models_path = get_models()
    for p in models_path:
        w = WorkerToEvaluate(p)
        workersToEvaluate.append(w)

    # Do local training
    localOutput = run_learning(workersToEvaluate, True)

    commit_secret_vote()


def commit_secret_vote():
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
    print("Pushing new model...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print("DONE!")


# asynchronous defined function to loop
# this loop sets up an event filter and is looking for new entires for the events
# this loop runs on a poll interval
async def log_loop_disclosure(event_filter, poll_interval):
    while True:
        for _ in event_filter.get_new_entries():
            disclose_secret_vote()
        await asyncio.sleep(poll_interval)


def listen_to_disclosure_event():
    contract_address = get_contract_address()
    federated_ML = w3.eth.contract(contract_address, abi=get_ABI(contract_address))
    event_filter = federated_ML.events.LastRoundDisclosurePhase.createFilter(
        fromBlock="latest"
    )
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(asyncio.gather(log_loop(event_filter, 2)))
    finally:
        # close loop to free up system resources
        loop.close()


def disclose_secret_vote():
    contract_address = get_contract_address()
    federated_ML = w3.eth.contract(contract_address, abi=get_ABI(contract_address))

    transaction = federated_ML.functions.discloseSecretVote(
        localOutput.bestKWorkers, "ciao"
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
    pass


# asynchronous defined function to loop
# this loop sets up an event filter and is looking for new entires for the events
# this loop runs on a poll interval
async def log_loop_task_ended(event_filter, poll_interval):
    while True:
        for _ in event_filter.get_new_entries():
            try_withdraw_reward()
        await asyncio.sleep(poll_interval)


def listen_to_end_task_event():
    contract_address = get_contract_address()
    federated_ML = w3.eth.contract(contract_address, abi=get_ABI(contract_address))
    event_filter = federated_ML.events.TaskEnded.createFilter(fromBlock="latest")
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(asyncio.gather(log_loop(event_filter, 2)))
    finally:
        # close loop to free up system resources
        loop.close()


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
