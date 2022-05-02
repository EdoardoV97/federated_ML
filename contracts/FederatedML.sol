// SPDX-License-Identifier: MIT

pragma solidity ^0.8.13;
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";
import "@chainlink/contracts/src/v0.6/VRFConsumerBase.sol";
import "@chainlink/contracts/src/v0.6/ChainlinkClient.sol";

contract FederatedML is Ownable, VRFConsumerBase, ChainlinkClient {
    //
    using EnumerableSet for EnumerableSet.AddressSet;

    enum STATE {
        FUNDING,
        REGISTERING,
        TASK_ENDED,
        TASK_ABORTED,
        ROUND_PREPARATION,
        ROUND_IN_PROGRESS
    }
    struct WorkerInfo {
        uint256 fee;
        uint256 reward;
        uint16 votesReceived;
        address[] votesGranted;
        string secretVote;
        bool alreadySelected;
        string modelHash;
    }
    struct Round {
        EnumerableSet.AddressSet workers;
    }

    STATE public state;
    string taskScript;
    uint16 workersNumber;
    uint16 roundsNumber;
    uint16 workersInRound;
    uint16 topWorkersInRound;
    uint256 entranceFee;
    uint256 bounty;
    string initialModelHash;
    uint16 voteMinutes;
    address coordinatorSC;
    // To keep track of the rounds
    Round[] rounds;
    // Variables for the vrf_coordinator
    uint256 public fee;
    bytes32 public keyhash;
    // Variables for the api_oracle
    address private oracleApiAddress;
    bytes32 private jobId;
    bytes32 lastTimerRequestId;

    mapping(address => uint256) public addressToAmountFunded;
    EnumerableSet.AddressSet public funders;
    mapping(address => WorkerInfo) public addressToWorkerInfo;
    EnumerableSet.AddressSet public workers;

    EnumerableSet.AddressSet private residualWorkers;

    // Events
    event RequestedRandomness(bytes32 requestId); // For the VRF coordinator
    event RoundWorkersSelection(address[] workers);

    constructor(
        string memory _taskScript,
        uint16 _workersNumber,
        uint16 _roundsNumber,
        uint16 _voteMinutes,
        string _initialModelHash,
        address _vrfCoordinator,
        address _link,
        uint256 _fee,
        bytes32 _keyhash,
        address _oracleApiAddress,
        bytes32 _jobId
    ) public VRFConsumerBase(_vrfCoordinator, _link) {
        require(
            _workersNumber % _roundsNumber == 0,
            "The number of workers must be a multiple of the number of rounds!"
        );
        taskScript = _taskScript;
        workersNumber = _workersNumber;
        roundsNumber = _roundsNumber;
        state = STATE.FUNDING;
        fee = _fee;
        keyhash = _keyhash;
        oracleApiAddress = _oracleApiAddress;
        jobId = _jobId;
        voteMinutes = _voteMinutes;
        initialModelHash = _initialModelHash;
    }

    function fund() public payable {
        require(state == STATE.FUNDING, "Is not possible to further fund!");
        addressToAmountFunded[msg.sender] += msg.value;
        add(funders, msg.sender);
    }

    function stopFunding() public onlyOwner {
        require(state == STATE.FUNDING, "Is not possible to stop funding now!");
        state = STATE.REGISTERING;
        entranceFee = computeFee();
        // TODO verify there are enough LINK tokens

        // TODO Start a timer, after which we need to cancel the task and refund all funders, workers and the admin
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
        add(workers, msg.sender);
        if (length(workers) >= workersNumber) {
            initializeRound();
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
            state == STATE.FUNDING || state == STATE.TASK_ABORTED,
            "Not possible to unfund in this phase!"
        );
        require(
            addressToAmountFunded[msg.sender] != 0,
            "You have no funded this task!"
        );
        msg.sender.transfer(addressToAmountFunded[msg.sender]);
        addressToAmountFunded[msg.sender] = 0;
        remove(funders, msg.sender);
    }

    function unregister() public {
        require(
            state == STATE.REGISTERING || state == STATE.TASK_ABORTED,
            "Not possible to unregister in this phase!"
        );
        require(
            addressToWorkerInfo[msg.sender].fee != 0,
            "You are not registered to this task!"
        );
        msg.sender.transfer(addressToWorkerInfo[msg.sender].fee);
        addressToWorkerInfo[msg.sender].fee = 0;
        // remove from the list of
        remove(workers, msg.sender);
    }

    function initializeRound() internal {
        // Request random numbers to the oracle to choose the workers for the round
        state = STATE.ROUND_PREPARATION;
        bytes32 requestId = requestRandomness(keyhash, fee);
        emit RequestedRandomness(requestId);
    }

    function startRound(uint256 _randomness) internal {
        EnumerableSet.AddressSet selectedWorkers;
        address[] selectedWorkersArray;
        uint256 index = _randomness % length(workers);
        uint16 counter = 0;
        // Given the random numbers use it as indexes to get the workers sequentially
        while (counter < workersInRound) {
            address w = at(workers, index);
            if (!addressToWorkerInfo[w].alreadySelected) {
                addressToWorkerInfo[w].already = true;
                add(selectedWorkers, w);
                selectedWorkersArray.push(w);
                counter++;
            }
            if (index == length(workers) - 1) {
                index = 0;
            } else {
                index++;
            }
        }
        rounds.push(Round(selectedWorkers));
        // Emit an event with the choosen workers for the round
        emit RoundWorkersSelection(selectedWorkersArray);
        // Set the new state
        state = STATE.ROUND_IN_PROGRESS;
        // Start the timer for the round duration
        startTimer();
    }

    function startTimer() internal {
        Chainlink.Request memory req = buildChainlinkRequest(
            jobId,
            address(this),
            this.timerEnded.selector
        );
        req.addUint("until", now + voteMinutes * 1 minutes);
        lastTimerRequestId = sendChainlinkRequestTo(oracleApiAddress, req, fee);
    }

    function timerEnded(bytes32 _requestId)
        public
        recordChainlinkFulfillment(_requestId)
    {
        require(lastTimerRequestId == _requestId, "Alredy passed the round!");
        endRound();
    }

    function endRound() internal {
        // TODO
        // Assign rewards
        // Start next round
    }

    function getPreviousModels() public view returns (string[]) {
        // Returns the models of the previous round (the initilization in case of the first round)
        require(
            state == STATE.ROUND_IN_PROGRESS,
            "There is not a round in progress currently!"
        );
        require(
            contains(rounds[rounds.length - 1].workers, msg.sender) == true,
            "You are not a worker of the current round!"
        );
        string[] previousModelHashes;
        if (rounds.length == 0) {
            return [initialModelHash];
        }
        for (
            uint256 i = 0;
            index < length(rounds[rounds.length - 2].workers);
            index++
        ) {
            previousModelHashes.push(
                addressToWorkerInfo[at(rounds[rounds.length - 1].workers, i)]
                    .modelHash
            );
        }
        return previousModelHashes;
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

    function fulfillRandomness(bytes32 _requestId, uint256 _randomness)
        internal
        override
    {
        require(state == STATE.ROUND_PREPARATION, "You aren't there yet!");
        require(_randomness > 0, "random-not-found");
        startRound(_randomness);
    }
}
