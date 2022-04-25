from scripts.Client.client_ml import LocalOutput
from web3 import Web3
import json

CHOSEN_NETWORK = "ganache-local"

with open("scripts/Client/client-config.json", "r") as file:
    json_file = json.load(file)
    w3 = Web3(Web3.HTTPProvider(json_file[CHOSEN_NETWORK]["provider"]))
    chain_id = int(json_file[CHOSEN_NETWORK]["chain-id"])
    my_address = json_file[CHOSEN_NETWORK]["address"]
    private_key = json_file[CHOSEN_NETWORK]["private-key"]


def get_contract_address():
    with open("build/deployments/map.json", "r") as file:
        json_file = json.load(file)
        return json_file[str(5777)]["FederatedML"][0]


def get_ABI(contract_address):
    with open("build/deployments/5777/" + contract_address + ".json", "r") as file:
        json_file = json.load(file)
        return json_file["abi"]


def connect_to_IPFS():
    # TODO
    pass


def get_from_IPFS(modelsHash: list(str)):
    # TODO
    models_path = []
    return models_path


def store_to_IPFS(filepath):
    # TODO
    ipfs_api = connect_to_IPFS()

    file_hash = ipfs_api.add(filepath)
    return file_hash


def getModels():
    modelsHash = []
    # TODO call the smart contract
    # contract_address = get_contract_address()
    # federated_ML = w3.eth.contract(contract_address, abi=get_ABI(contract_address))
    # (
    #     pulled_model,
    #     data_points_pulled_model,
    # ) = federated_ML.functions.retrieveModel().call()
    models_path = get_from_IPFS(modelsHash)
    return models_path


def sendResponse(local_output: LocalOutput):
    filepath = ""
    local_output.model.save_weights(filepath, overwrite=True)
    file_hash = store_to_IPFS(filepath)
    # TODO call the smart contract
    # contract_address = get_contract_address()

    # integer_rep_new_model = [safe_check_toWei(x) for x in new_model]

    # federated_ML = w3.eth.contract(contract_address, abi=get_ABI(contract_address))
    # transaction = federated_ML.functions.updateModel(
    #     integer_rep_new_model, old_data_points, new_local_data_points
    # ).buildTransaction(
    #     {
    #         "chainId": chain_id,
    #         "gasPrice": w3.eth.gas_price,
    #         "from": my_address,
    #         "nonce": w3.eth.getTransactionCount(my_address),
    #     }
    # )

    # signed_transaction = w3.eth.account.sign_transaction(
    #     transaction, private_key=private_key
    # )
    # tx_hash = w3.eth.send_raw_transaction(signed_transaction.rawTransaction)
    # print("Pushing new model...")
    # tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    # print("DONE!")
    pass
