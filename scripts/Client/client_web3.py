from web3 import Web3
from decimal import Decimal

# For connecting to ganache
w3 = Web3(Web3.HTTPProvider("http://0.0.0.0:8545"))
chain_id = 1337
my_address = "0x938a83Eb94AA291CC028a4af8cDe421Aff3fBF65"
private_key = "0xc58b986f5a4acab4acb21d4516fdba6e1e73ed9c9bf051d83617ca0522f16c53"

contract_address = "0x8c672404b6E81AE1404Bd0Aa16458EC64006FF83"


def get_ABI():
    pass


def pullModel():
    federated_ML = w3.eth.contract(contract_address, abi=get_ABI())
    (
        pulled_model,
        data_points_pulled_model,
    ) = federated_ML.functions.retrieveModel().call()
    print(
        f"The number of data points of the current model is: {data_points_pulled_model}"
    )
    print(f"The pulled model is: {pulled_model}")
    float_rep_pulled_model = [Web3.fromWei(x, "gwei") for x in pulled_model]
    return float_rep_pulled_model, data_points_pulled_model


def pushModel(new_model, old_data_points, new_local_data_points):
    integer_rep_new_model = [Web3.toWei(x, "gwei") for x in new_model]

    federated_ML = w3.eth.contract(contract_address, abi=get_ABI())
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
    print("Updating stored Value...")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
