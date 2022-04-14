from re import X
from web3 import Web3
from decimal import Decimal
import json

# For connecting to ganache
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
chain_id = 1337
my_address = "0xd2015d33DC60D27A902b1F4Fb2Ea5aFD1a5293BE"
private_key = "0x4af55be9c3cf3f310cafd81c12d1ed0b510ada4da54d05a3e914bc1bc40e6afc"

def get_contract_address():
    with open('build/deployments/map.json', 'r') as file:
        json_file = json.load(file)
        return json_file[str(5777)]['FederatedML'][0]


def get_ABI(contract_address):
    with open('build/deployments/5777/'  + contract_address + '.json', 'r') as file:
        json_file = json.load(file)
        return json_file['abi']


def safe_check_toWei(number):
    if number < 0:
        return - Web3.toWei(abs(number), "gwei")
    else:
        return Web3.toWei(number, "gwei")


def safe_check_fromWei(number):
    if number < 0:
        return - Web3.fromWei(abs(number), "gwei")
    else:
        return Web3.fromWei(number, "gwei")


def pullModel():
    contract_address = get_contract_address()
    federated_ML = w3.eth.contract(contract_address, abi=get_ABI(contract_address))
    (
        pulled_model,
        data_points_pulled_model,
    ) = federated_ML.functions.retrieveModel().call()
    print(
        f"The number of data points of the GLOBAL model is: {data_points_pulled_model}"
    )
    float_rep_pulled_model = [float(safe_check_fromWei(x)) for x in pulled_model]
    print(f"Model[PULLED GLOBAL ONE]: {float_rep_pulled_model}")
    return float_rep_pulled_model, data_points_pulled_model


def pushModel(new_model, old_data_points, new_local_data_points):
    contract_address = get_contract_address()

    integer_rep_new_model = [safe_check_toWei(x) for x in new_model]
    # integer_rep_new_model = []
    # for i in range(len(new_model)):
    #     if new_model[i] < 0:
    #         integer_rep_new_model.append(-Web3.toWei(abs(new_model[i]), "gwei"))
    #     else:
    #         integer_rep_new_model.append(Web3.toWei(new_model[i], "gwei"))

    federated_ML = w3.eth.contract(contract_address, abi=get_ABI(contract_address))
    transaction = federated_ML.functions.updateModel(
        integer_rep_new_model, old_data_points, new_local_data_points
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
