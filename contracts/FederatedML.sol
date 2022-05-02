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
        address[] votesGranted;
        string secretVote;
    }
    struct Round {
        address[] workers;
    }
    event RoundWorkersSelection(address[] workers);

    STATE public state;
    string taskScript;
    uint16 workersNumber;
    uint16 roundsNumber;
    uint16 workersInRound;
    uint256 entranceFee;
    uint256 bounty;
    address coordinatorSC;
    Round[] rounds;

    mapping(address => uint256) public addressToAmountFunded;
    address[] public funders;
    mapping(address => WorkerInfo) public addressToWorkerInfo;
    address[] public workers;

    constructor(
        string memory _taskScript,
        uint16 _workersNumber,
        uint16 _roundsNumber
    ) {
        require(
            _workersNumber % _roundsNumber == 0,
            "The number of workers must be a multiple of the number of rounds!"
        );
        taskScript = _taskScript;
        workersNumber = _workersNumber;
        roundsNumber = _roundsNumber;
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
            startRound();
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

    function startRound() internal {
        //TODO
        // Request random numbers to the oracle to choose the workers for the round
    }

    function nextRound() internal {
        //TODO
        // Given the random numbers use it as indexes to get the workers (take next if already choose)
        // Emit an event with the choosen workers for the round
    }

    function getPreviousModels() public view returns (string[]) {
        //TODO
        // Returns the models of the previous round (the initilization in case of the first round)
    }

    function commitWork(uint16[] _votes, string memory _updatedModel) external {
        //TODO
        // Check if the workers is one of the round and it has not already committed
        // Save the vote (the parameter is the index of the voted models)
        // Save the updated model
        // If it is the last commit of the round start the next
        // If it is the second to last, start the last round
    }

    function commitSecretVote(string _secretVote) external {
        //TODO
        // Check if it is the last round
        // Check if the workers is one of the round and it has not already committed
        // Save the secret vote
        // If it was the last secret vote begin the disclosure phase
    }

    function discloseSecretVote(uint16[] _votes, string memory salt) external {
        //TODO
        // Check disclosure phase
        // Check if the workers is one of the last round and it has committed a secret vote
        // Check the validity of the vote
        // If it is the last disclosure, end the task
    }
}
