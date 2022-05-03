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
        ROUND_IN_PROGRESS,
        LAST_ROUND_IN_PROGRESS,
        LAST_ROUND_DISCLOSING
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
        uint16 roundCommitment;
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
    uint16 registrationMinutes;
    address coordinatorSC;
    // To keep track of the rounds
    Round[] rounds;
    // To keep track of the rewards in a round
    uint256[] rewards;
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
    event LastRoundWorkersSelection(address[] workers);
    event LastRoundDisclosurePhase();
    event TaskEnded();

    constructor(
        string memory _taskScript,
        uint16 _workersNumber,
        uint16 _roundsNumber,
        uint16 _voteMinutes,
        uint16 _registrationMinutes;
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

        // Start a timer, after which we need to cancel the task and refund all funders and workers
        startTimer(registrationMinutes);
    }

    function computeFee() internal returns (uint256) {
        // TODO
        // Compute the fees and the rewards in a round accordingly
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
        startTimer(voteMinutes);
    }

    function startTimer(uint16 _voteMinutes) internal {
        Chainlink.Request memory req = buildChainlinkRequest(
            jobId,
            address(this),
            this.timerEnded.selector
        );
        req.addUint("until", now + _voteMinutes * 1 minutes);
        lastTimerRequestId = sendChainlinkRequestTo(oracleApiAddress, req, fee);
    }

    function timerEnded(bytes32 _requestId)
        public
        recordChainlinkFulfillment(_requestId)
    {
        require(lastTimerRequestId == _requestId, "Alredy passed the phase!");
        if(state == STATE.ROUND_PREPARATION){
            endRound();
        }
        if(state == STATE.REGISTERING){
            state = STATE.TASK_ABORTED;
        }
        return;
    }

    function endRound() internal {
        // Assign rewards?! Better to check the position when someone claim the rewards!
        //TODO
        // Start next round (pay attention to the last!)
        if (rounds.length == roundsNumber) {
            STATE = STATE.TASK_ENDED;
            return;
        }
        if (rounds.length == roundsNumber - 1) {
            startLastRound();
            return;
        }
        initializeRound();
    }

    function startLastRound() internal {
        EnumerableSet.AddressSet selectedWorkers;
        address[] selectedWorkersArray;
        uint256 index = 0;
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
        emit LastRoundWorkersSelection(selectedWorkersArray);
        // Set the new state
        state = STATE.LAST_ROUND_IN_PROGRESS;
        // Start the timer for the round duration
        startTimer(voteMinutes);
    }

    // function quick(<<type>> memory data) internal pure {
    //     if (data.length > 1) {
    //         quickPart(data, 0, data.length - 1);
    //     }
    // }
    // function quickPart(<<type>> memory data, uint low, uint high) internal pure {
    //     if (low < high) {
    //         uint pivotVal = data[(low + high) / 2];

    //         uint low1 = low;
    //         uint high1 = high;
    //         for (;;) {
    //             while (data[low1] < pivotVal) low1++;
    //             while (data[high1] > pivotVal) high1--;
    //             if (low1 >= high1) break;
    //             (data[low1], data[high1]) = (data[high1], data[low1]);
    //             low1++;
    //             high1--;
    //         }
    //         if (low < high1) quickPart(data, low, high1);
    //         high1++;
    //         if (high1 < high) quickPart(data, high1, high);
    //     }
    // }

    function getPreviousModels() public view returns (string[]) {
        // Returns the models of the previous round (the initilization in case of the first round)
        require(
            state == STATE.ROUND_IN_PROGRESS ||
                state == STATE.LAST_ROUND_IN_PROGRESS,
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
        // meglio mettere i votes come gli hash e non come gli indici visto che il set di workers non è ordinato
        require(
            state = STATE.ROUND_IN_PROGRESS,
            "You cannot commit your work in this phase!"
        );
        // Check if the workers is one of the round and it has not already committed
        require(
            contains(rounds[rounds.length - 1].workers, msg.sender),
            "You are not a selected worker of this round!"
        );
        require(
            addressToWorkerInfo[msg.sender].votesGranted.length == 0,
            "You have alredy submitted your work!"
        );
        // Check votes validity
        require(checkVotesValidity(_votes), "Your votes are not valid!");
        // Save and apply the vote (the parameter is the index of the voted models)
        addressToWorkerInfo[msg.sender].votesGranted = _votes;
        for (uint16 index = 0; index < _votes.length; index++) {
            addressToWorkerInfo[
                at(rounds[rounds.length - 1].workers, _votes[index])
            ].votesReceived++;
        }
        // Save the updated model
        addressToWorkerInfo[msg.sender].modelHash = _updatedModel;
        // Increment the commitment counter of the current round
        rounds[rounds.length - 1].roundCommitment++;
        // If it is the last commit of the round end the round
        if (rounds[rounds.length - 1].roundCommitment == workersInRound) {
            endRound();
        }
    }

    function checkVotesValidity(uint16[] _votes) internal returns (bool) {
        mapping(uint16 => bool) modelsVotedIndexes;
        // Check correct number of votes
        if (_votes.length == topWorkersInRound) {
            for (uint16 index = 0; index < _votes.length; index++) {
                // Check correct bound of the vote
                if (_votes[index] < 0 && _votes[index] >= workersInRound) {
                    return false;
                }
                // Check no double votes
                if (modelsVotedIndexes[_votes[index]]) {
                    modelsVotedIndexes[_votes[index]] = true;
                } else {
                    return false;
                }
            }
        } else {
            return false;
        }
        return true;
    }

    function commitSecretVote(string _secretVote) external {
        // Check if it is the last round
        require(
            state == STATE.LAST_ROUND_IN_PROGRESS,
            "You cannot commit a secret vote in this phase!"
        );
        // Check if the workers is one of the round and it has not already committed
        require(
            contains(rounds[rounds.length - 1].workers, msg.sender),
            "You are not a selected worker of this round!"
        );
        require(
            bytes(addressToWorkerInfo[msg.sender].secretVote).length == 0,
            "You have alredy submitted your work!"
        );
        // Save the secret vote
        addressToWorkerInfo[msg.sender].secretVote = _secretVote;
        // Increment the commitment counter of the current round
        rounds[rounds.length - 1].roundCommitment++;
        // If it was the last secret vote begin the disclosure phase
        if (rounds[rounds.length - 1].roundCommitment == workersInRound) {
            state = STATE.LAST_ROUND_DISCLOSING;
            rounds[rounds.length - 1].roundCommitment = 0; // Reset to count the disclosures
            emit LastRoundDisclosurePhase();
        }
    }

    function discloseSecretVote(uint16[] _votes, string memory _salt) external {
        // Check disclosure phase
        require(
            state == STATE.LAST_ROUND_DISCLOSING,
            "You cannot disclose a secret vote in this phase!"
        );
        // Check if the workers is one of the last round and it has committed a secret vote
        require(
            contains(rounds[rounds.length - 1].workers, msg.sender),
            "You are not a selected worker of this round!"
        );
        require(
            bytes(addressToWorkerInfo[msg.sender].secretVote).length != 0,
            "You have not submitted your work in time!"
        );
        // Check the validity of the vote
        require(
            checkSecretVoteValidity(_votes, _salt),
            "Your secret votes are not valid!"
        );
        // If it is the last disclosure, end the task
        if (rounds[rounds.length - 1].roundCommitment == workersInRound) {
            state = STATE.TASK_ENDED;
            emit TaskEnded();
        }
    }

    function checkSecretVoteValidity(uint16[] _votes, string memory _salt)
        internal
        returns (bool)
    {
        if (
            keccak256(_votes, _salt) ==
            addressToWorkerInfo[msg.sender].secretVote &&
            checkVotesValidity(_votes)
        ) {
            return true;
        }
        return false;
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
