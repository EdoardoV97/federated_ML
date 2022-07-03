# NB TO RUN THIS TEST DO NOT USE BROWNIE. Browse to the file directory and run it as a normal python script
import unittest
import requests

# Add a file to IPFS manually through the companion and then paste the hash here to test
TEST_HASH = "QmfYwyZqpMxorkMHkYuKmEsxyG6ia2V3ZkRc4HmjMCRv6s"

# Test to store a model
@unittest.skip("Passed")
def test_store_to_IPFS():
    file_path = "./MNIST_initial_model.h5"
    response = requests.post(
        "http://127.0.0.1:5001/api/v0/add",
        files={file_path: open(file_path, "rb")},
    )
    p = response.json()
    hash = p["Hash"]
    print(hash)


# Test to retrieve a model
@unittest.skip("Passed")
def test_download_from_IPFS():
    params = {"arg": TEST_HASH}
    response = requests.post("http://127.0.0.1:5001/api/v0/get", params=params)
    print(response)
    with open("modelFromIPFS.h5", "wb") as f:
        f.write(response.content)
