// SPDX-License-Identifier: MIT

pragma solidity ^0.8.13;
import "@openzeppelin/contracts/access/Ownable.sol";

contract FederatedML is Ownable {
    enum STATE {
        FUNDING,
        REGISTERING,
        TASK_STARTED,
        TASK_ENDED
    }
    struct WorkerInfo {
        uint256 fee;
        uint256 reward;
        uint16 votesReceived;
        address voteGranted;
    }
    struct Round {
        address[] workers;
    }

    STATE public state;
    string taskScript;
    uint16 workersNumber;
    uint256 entranceFee;
    uint256 bounty;
    address coordinatorSC;
    Round[] rounds;

    mapping(address => uint256) public addressToAmountFunded;
    address[] public funders;
    mapping(address => WorkerInfo) public addressToWorkerInfo;
    address[] public workers;

    constructor(string memory _taskScript, uint16 _workersNumber) {
        taskScript = _taskScript;
        workersNumber = _workersNumber;
        state = STATE.FUNDING;
    }

    function fund() public payable {
        require(state == STATE.FUNDING, "Is not possible to further fund!");
        addressToAmountFunded[msg.sender] += msg.value;
        funders.push(msg.sender);
    }

    function stopFunding() public onlyOwner {
        require(state == STATE.FUNDING, "Is not possible to stop funding now!");
        state = STATE.REGISTERING;
        entranceFee = computeFee();
    }

    function computeFee() internal returns (uint256) {
        return 0.1 * 10**18;
    }

    function register() public payable {
        require(state == STATE.REGISTERING, "Is not possible to register now!");
        require(msg.value >= entranceFee, "Minimum fee not satisfied!");
        require(
            addressToWorkerInfo[msg.sender].fee != 0,
            "You are already registered!"
        ); // It requires that entranceFee is not 0
        addressToWorkerInfo[msg.sender].fee += msg.value;
        workers.push(msg.sender);
        if (workers.length >= workersNumber) {
            state = STATE.TASK_STARTED;
        }
    }

    function withdrawReward() public payable {
        require(
            addressToWorkerInfo[msg.sender].fee != 0,
            "You were not registered!"
        );
        require(
            addressToWorkerInfo[msg.sender].reward != 0,
            "You have no reward for this task!"
        );
        msg.sender.transfer(addressToWorkerInfo[msg.sender].reward);
        addressToWorkerInfo[msg.sender].reward = 0;
    }

    function unfund() public {
        require(
            state == STATE.FUNDING,
            "Not possible to unfund in this phase!"
        );
        require(
            addressToAmountFunded[msg.sender] != 0,
            "You have no funded this task!"
        );
        msg.sender.transfer(addressToAmountFunded[msg.sender]);
        addressToAmountFunded[msg.sender] = 0;
        removeFunder(msg.sender);
    }

    function unregister() public {
        require(
            state == STATE.REGISTERING,
            "Not possible to unregister in this phase!"
        );
        require(
            addressToWorkerInfo[msg.sender].fee != 0,
            "You are not registered to this task!"
        );
        msg.sender.transfer(addressToWorkerInfo[msg.sender].fee);
        addressToWorkerInfo[msg.sender].fee = 0;
        // remove from the list of
        removeWorker(msg.sender);
    }

    function removeWorker(address addr) internal {
        for (uint16 i = 0; i < workers.length; i++) {
            if (workers[i] == addr) {
                if (workers.length > 1) {
                    workers[i] = workers[workers.length - 1];
                }
                workers.length--;
                return;
            }
        }
    }

    function removeFunder(address addr) internal {
        for (uint16 i = 0; i < funders.length; i++) {
            if (funders[i] == addr) {
                if (funders.length > 1) {
                    funders[i] = funders[funders.length - 1];
                }
                funders.length--;
                return;
            }
        }
    }
}
