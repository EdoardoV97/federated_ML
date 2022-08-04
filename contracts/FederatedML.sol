// SPDX-License-Identifier: MIT

pragma solidity ^0.8.13;
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/structs/EnumerableSet.sol";
import "@chainlink/contracts/src/v0.8/VRFConsumerBase.sol";
import "@chainlink/contracts/src/v0.8/ChainlinkClient.sol";
import "@chainlink/contracts/src/v0.8/interfaces/LinkTokenInterface.sol";

contract FederatedML is Ownable, VRFConsumerBase, ChainlinkClient {
    //
    using EnumerableSet for EnumerableSet.AddressSet;
    using Chainlink for Chainlink.Request;

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
        bool fee;
        bool rewardTaken;
        uint16 votesReceived;
        address[] votesGranted;
        bytes32 secretVote;
        bool alreadySelected;
        string modelHash;
    }
    struct Round {
        EnumerableSet.AddressSet workers;
        uint16 roundCommitment;
        address[] ranking;
    }

    STATE public state = STATE.FUNDING;
    uint256 public workersNumber;
    uint256 public roundsNumber;
    uint256 public workersInRound;
    uint256 public topWorkersInRound;
    uint256 public entranceFee;
    string public initialModelHash;
    uint16 public voteMinutes;
    uint16 public registrationMinutes;
    address public coordinatorSC;
    address public linkTokenAddress;
    // To keep track of the rounds
    Round[] rounds;
    // To keep track of the rewards in a round
    uint256[] public rewards;
    uint256 public totalRoundReward;
    // Variables for the vrf_coordinator
    uint256 public fee;
    bytes32 public keyhash;
    // Variables for the api_oracle
    address private oracleApiAddress;
    bytes32 private jobId;
    bytes32 lastTimerRequestId;

    mapping(address => uint256) public addressToAmountFunded;
    EnumerableSet.AddressSet funders;
    mapping(address => WorkerInfo) public addressToWorkerInfo;
    EnumerableSet.AddressSet workers;

    EnumerableSet.AddressSet private residualWorkers;

    // Events
    event RequestedRandomness(bytes32 requestId); // For the VRF coordinator
    event RoundWorkersSelection(address[] workers);
    event LastRoundWorkersSelection(address[] workers);
    event LastRoundDisclosurePhase();
    event TaskEnded();

    constructor(
        // uint16 _workersNumber,
        // uint16 _roundsNumber,
        // uint16 _voteMinutes,
        // uint16 _registrationMinutes,
        // string memory _taskDescription
        string memory _initialModelHash,
        address _vrfCoordinator,
        address _linkTokenAddress,
        uint256 _fee,
        bytes32 _keyhash,
        address _oracleApiAddress,
        bytes32 _jobId
    ) VRFConsumerBase(_vrfCoordinator, _linkTokenAddress) {
        // require(
        //     _workersNumber % _roundsNumber == 0,
        //     "The number of workers must be a multiple of the number of rounds!"
        // );
        // workersNumber = _workersNumber;
        // roundsNumber = _roundsNumber;
        workersNumber = 6;
        roundsNumber = 3;
        fee = _fee;
        keyhash = _keyhash;
        oracleApiAddress = _oracleApiAddress;
        jobId = _jobId;
        // voteMinutes = _voteMinutes;
        voteMinutes = 10;
        // registrationMinutes = _registrationMinutes;
        registrationMinutes = 5;
        initialModelHash = _initialModelHash;
        linkTokenAddress = _linkTokenAddress;
        workersInRound = workersNumber / roundsNumber;
        topWorkersInRound = 1;
    }

    function fund() public payable {
        require(state == STATE.FUNDING, "Is not possible to further fund!");
        addressToAmountFunded[msg.sender] += msg.value;
        EnumerableSet.add(funders, msg.sender);
    }

    function stopFunding() public onlyOwner {
        require(state == STATE.FUNDING, "Is not possible to stop funding now!");
        // Verify there are enough LINK tokens
        require(
            LinkTokenInterface(linkTokenAddress).balanceOf(address(this)) >=
                (roundsNumber * 2) * fee, // *2 because in every round one timer and one random number +1 for the first timer but also -1 because no random number for the last round
            "There are not enough Link funded to run the task!"
        );
        state = STATE.REGISTERING;
        computeFeeAndRewards();
        // Start a timer, after which we need to cancel the task and refund all funders and workers
        startTimer(registrationMinutes);
    }

    function computeFeeAndRewards() internal {
        uint256 lowerBound;
        uint256 upperBound;
        uint256 bounty = address(this).balance;
        uint256 r1;
        uint256[] memory coefficients = new uint256[](topWorkersInRound);
        uint256 coefficientsSum;
        for (uint256 j = 0; j < coefficients.length; j++) {
            coefficients[j] = computeRewardCoefficient(j + 1);
            coefficientsSum += coefficients[j];
        }
        r1 =
            (bounty * 10**18 * 10**18) /
            (coefficientsSum *
                roundsNumber *
                10**18 -
                ((workersNumber * 10**18 * 10**18) /
                    (((topWorkersInRound * 10**18) / 2) + 2 * 10**18)));

        upperBound =
            ((((workersInRound - 2 * topWorkersInRound + 1) * 10**18) /
                (workersInRound - 1)) * r1) /
            10**18;

        lowerBound =
            (r1 * 10**18) /
            (((topWorkersInRound * 10**18) / 2) + 2 * 10**18);

        require(
            lowerBound <= upperBound,
            "Is not possible to compute a valid fee in the current setting!"
        );
        r1 = r1 / 10**18;
        upperBound = upperBound / 10**18;
        lowerBound = lowerBound / 10**18;

        entranceFee = lowerBound;
        for (uint64 j = 0; j < coefficients.length; j++) {
            rewards.push(coefficients[j] * r1);
            totalRoundReward += rewards[j];
        }
        return;
    }

    function computeRewardCoefficient(uint256 _j) internal returns (uint256) {
        return (workersInRound - 2 * _j + 1) / (workersInRound - 1);
    }

    function register() public payable {
        require(state == STATE.REGISTERING, "Is not possible to register now!");
        require(msg.value == entranceFee, "Minimum fee not satisfied!");
        require(
            addressToWorkerInfo[msg.sender].fee == false,
            "You are already registered!"
        ); // It requires that entranceFee is not 0
        addressToWorkerInfo[msg.sender].fee = true;
        EnumerableSet.add(workers, msg.sender);
        if (EnumerableSet.length(workers) >= workersNumber) {
            initializeRound();
        }
    }

    function withdrawReward() public payable {
        require(
            addressToWorkerInfo[msg.sender].fee == true,
            "You were not registered!"
        );
        // Search the round in which there is the worker
        int256 roundIndex;
        roundIndex = searchRoundOfWorker(msg.sender);
        // Check if the worker was selected in a round
        require(roundIndex != -1, "You have not yet worked in a round!");
        // Check the round is concluded and also the successive
        require(
            rounds[uint256(roundIndex)].roundCommitment == workersInRound,
            "The round is not terminated!"
        );
        require(
            rounds.length == roundsNumber ||
                rounds[uint256(roundIndex) + 1].roundCommitment ==
                workersInRound,
            "The successive round is not already terminated!"
        );
        require(
            addressToWorkerInfo[msg.sender].rewardTaken == false,
            "The reward was already withdrawed!"
        );
        // Compute the rankings is not yet done
        if (rounds[uint256(roundIndex)].ranking.length == 0) {
            // Not last round case
            if (uint256(roundIndex) != roundsNumber - 1) {
                rounds[uint256(roundIndex)].ranking = computeRanking(
                    uint256(roundIndex)
                );
            } else {
                // Last Round Case
                // Check if last but one round's ranking not already computed
                if (rounds[uint256(roundIndex - 1)].ranking.length == 0) {
                    rounds[uint256(roundIndex - 1)].ranking = computeRanking(
                        uint256(roundIndex - 1)
                    );
                }
                rounds[uint256(roundIndex)].ranking = computeLastRoundRanking(
                    uint256(roundIndex)
                );
            }
        }
        // w.r.t. the ranking give the correct reward
        for (uint256 i = 0; i < topWorkersInRound; i++) {
            if (msg.sender == rounds[uint256(roundIndex)].ranking[i]) {
                payable(msg.sender).transfer(rewards[i]);
            }
        }
        addressToWorkerInfo[msg.sender].rewardTaken = true;
    }

    function searchRoundOfWorker(address _worker) internal returns (int256) {
        for (uint256 index = 0; index < rounds.length; index++) {
            if (EnumerableSet.contains(rounds[index].workers, _worker)) {
                return int256(index);
            }
        }
        return -1;
    }

    function computeRanking(uint256 _roundIndex)
        internal
        returns (address[] memory)
    {
        address[] memory ranking = new address[](workersInRound);
        uint256[] memory votes = new uint256[](workersInRound);
        for (
            uint256 i = 0;
            i < EnumerableSet.length(rounds[_roundIndex].workers);
            i++
        ) {
            ranking[i] = EnumerableSet.at(rounds[_roundIndex].workers, i);
            votes[i] = addressToWorkerInfo[
                EnumerableSet.at(rounds[_roundIndex].workers, i)
            ].votesReceived;
        }
        (votes, ranking) = quickSort(
            votes,
            ranking,
            0,
            int256(votes.length) - 1
        );
        return ranking;
    }

    function computeLastRoundRanking(uint256 _roundIndex)
        internal
        returns (address[] memory)
    {
        address[] memory ranking = new address[](workersInRound);
        uint256[] memory votes = new uint256[](workersInRound);
        for (
            uint256 i = 0;
            i < EnumerableSet.length(rounds[_roundIndex].workers);
            i++
        ) {
            ranking[i] = EnumerableSet.at(rounds[_roundIndex].workers, i);
            for (uint256 j = 0; j < topWorkersInRound; j++) {
                for (
                    uint256 k = 0;
                    k < addressToWorkerInfo[ranking[i]].votesGranted.length;
                    k++
                ) {
                    if (
                        addressToWorkerInfo[ranking[i]].votesGranted[k] ==
                        rounds[_roundIndex - 1].ranking[j]
                    ) {
                        votes[i]++;
                    }
                }
            }
        }
        (votes, ranking) = quickSort(
            votes,
            ranking,
            0,
            int256(votes.length) - 1
        );
        return ranking;
    }

    function quickSort(
        uint256[] memory _arr,
        address[] memory _arr2,
        int256 _left,
        int256 _right
    ) internal returns (uint256[] memory, address[] memory) {
        int256 i = _left;
        int256 j = _right;
        if (i == j) return (_arr, _arr2);
        uint256 pivot = _arr[uint256(_left + (_right - _left) / 2)];
        while (i <= j) {
            while (_arr[uint256(i)] > pivot) i++;
            while (pivot > _arr[uint256(j)]) j--;
            if (i <= j) {
                (_arr[uint256(i)], _arr[uint256(j)]) = (
                    _arr[uint256(j)],
                    _arr[uint256(i)]
                );
                (_arr2[uint256(i)], _arr2[uint256(j)]) = (
                    _arr2[uint256(j)],
                    _arr2[uint256(i)]
                );
                i++;
                j--;
            }
        }
        if (_left < j) quickSort(_arr, _arr2, _left, j);
        if (i < _right) quickSort(_arr, _arr2, i, _right);
        return (_arr, _arr2);
    }

    function unfund() public payable {
        require(
            state == STATE.FUNDING || state == STATE.TASK_ABORTED,
            "Not possible to unfund in this phase!"
        );
        require(
            addressToAmountFunded[msg.sender] != 0,
            "You have no funded this task!"
        );
        payable(msg.sender).transfer(addressToAmountFunded[msg.sender]);
        addressToAmountFunded[msg.sender] = 0;
        EnumerableSet.remove(funders, msg.sender);
    }

    function unregister() public payable {
        require(
            state == STATE.REGISTERING || state == STATE.TASK_ABORTED,
            "Not possible to unregister in this phase!"
        );
        require(
            addressToWorkerInfo[msg.sender].fee == true,
            "You are not registered to this task!"
        );
        payable(msg.sender).transfer(entranceFee);
        addressToWorkerInfo[msg.sender].fee = false;
        // remove from the list of
        EnumerableSet.remove(workers, msg.sender);
    }

    function initializeRound() internal {
        // Request random numbers to the oracle to choose the workers for the round
        state = STATE.ROUND_PREPARATION;
        bytes32 requestId = requestRandomness(keyhash, fee);
        emit RequestedRandomness(requestId);
    }

    function startRound(uint256 _randomness) internal {
        address[] memory selectedWorkersArray = new address[](workersInRound);
        uint256 index = _randomness % EnumerableSet.length(workers);
        uint16 counter = 0;
        uint16 arrayIndex = 0;
        // Given the random numbers use it as indexes to get the workers sequentially
        while (counter < workersInRound) {
            address w = EnumerableSet.at(workers, index);
            if (!addressToWorkerInfo[w].alreadySelected) {
                addressToWorkerInfo[w].alreadySelected = true;
                selectedWorkersArray[arrayIndex] = w;
                arrayIndex++;
                counter++;
            }
            if (index == EnumerableSet.length(workers) - 1) {
                index = 0;
            } else {
                index++;
            }
        }
        uint256 idx = rounds.length;
        rounds.push();
        Round storage tempRound = rounds[idx];
        for (uint256 k = 0; k < selectedWorkersArray.length; k++) {
            EnumerableSet.add(tempRound.workers, selectedWorkersArray[k]);
        }
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
        setChainlinkToken(linkTokenAddress);
        setChainlinkOracle(oracleApiAddress);
        req.addUint("until", block.timestamp + _voteMinutes * 1 minutes);
        lastTimerRequestId = sendChainlinkRequest(req, fee);
    }

    function timerEnded(bytes32 _requestId)
        public
        recordChainlinkFulfillment(_requestId)
    {
        require(lastTimerRequestId == _requestId, "Alredy passed the phase!");
        if (state == STATE.ROUND_IN_PROGRESS) {
            endRound();
        }
        if (state == STATE.REGISTERING) {
            state = STATE.TASK_ABORTED;
        }
        if (state == STATE.LAST_ROUND_IN_PROGRESS) {
            state = STATE.LAST_ROUND_DISCLOSING;
            rounds[rounds.length - 1].roundCommitment = 0; // Reset to count the disclosures
            startTimer(voteMinutes);
            emit LastRoundDisclosurePhase();
        }
        if (state == STATE.LAST_ROUND_DISCLOSING) {
            state = STATE.TASK_ENDED;
            emit TaskEnded();
        }
        return;
    }

    function endRound() internal {
        // Start next round (pay attention to the last!)
        if (rounds.length == roundsNumber) {
            state = STATE.TASK_ENDED;
            return;
        }
        if (rounds.length == roundsNumber - 1) {
            startLastRound();
            return;
        }
        initializeRound();
    }

    function startLastRound() internal {
        address[] memory selectedWorkersArray = new address[](workersInRound);
        uint256 index = 0;
        uint16 counter = 0;
        uint16 arrayIndex = 0;
        // Get the remaining workers sequentially
        while (counter < workersInRound) {
            address w = EnumerableSet.at(workers, index);
            if (!addressToWorkerInfo[w].alreadySelected) {
                addressToWorkerInfo[w].alreadySelected = true;
                selectedWorkersArray[arrayIndex] = w;
                arrayIndex++;
                counter++;
            }
            if (index == EnumerableSet.length(workers) - 1) {
                index = 0;
            } else {
                index++;
            }
        }
        uint256 idx = rounds.length;
        rounds.push();
        Round storage tempRound = rounds[idx];
        for (uint256 k = 0; k < selectedWorkersArray.length; k++) {
            EnumerableSet.add(tempRound.workers, selectedWorkersArray[k]);
        }
        // Emit an event with the choosen workers for the round
        emit LastRoundWorkersSelection(selectedWorkersArray);
        // Set the new state
        state = STATE.LAST_ROUND_IN_PROGRESS;
        // Start the timer for the round duration
        startTimer(voteMinutes);
    }

    function getPreviousModels() public view returns (string[] memory) {
        // Returns the models of the previous round (the initilization in case of the first round)
        require(
            state == STATE.ROUND_IN_PROGRESS ||
                state == STATE.LAST_ROUND_IN_PROGRESS,
            "There is not a round in progress currently!"
        );
        // require(
        //     EnumerableSet.contains(
        //         rounds[rounds.length - 1].workers,
        //         msg.sender
        //     ) == true,
        //     "You are not a worker of the current round!"
        // );
        string[] memory previousModelHashes = new string[](workersInRound);
        if (rounds.length == 1) {
            string[] memory startingModel = new string[](1);
            startingModel[0] = initialModelHash;
            return startingModel;
        }
        for (
            uint256 i = 0;
            i < EnumerableSet.length(rounds[rounds.length - 2].workers);
            i++
        ) {
            previousModelHashes[i] = addressToWorkerInfo[
                EnumerableSet.at(rounds[rounds.length - 2].workers, i)
            ].modelHash;
        }
        return previousModelHashes;
    }

    function commitWork(uint16[] memory _votes, string memory _updatedModel)
        external
    {
        require(
            state == STATE.ROUND_IN_PROGRESS,
            "You cannot commit your work in this phase!"
        );
        // Check if the workers is one of the round and it has not already committed
        require(
            EnumerableSet.contains(
                rounds[rounds.length - 1].workers,
                msg.sender
            ),
            "You are not a selected worker of this round!"
        );
        require(
            addressToWorkerInfo[msg.sender].votesGranted.length == 0,
            "You have alredy submitted your work!"
        );
        if (rounds.length != 1) {
            // Check votes validity
            require(checkVotesValidity(_votes), "Your votes are not valid!");
            // Save and apply the votes
            // Convert indexes to respective addresses
            addressToWorkerInfo[msg.sender]
                .votesGranted = convertIndexesToAddresses(_votes);
            for (uint16 index = 0; index < _votes.length; index++) {
                addressToWorkerInfo[
                    EnumerableSet.at(
                        rounds[rounds.length - 2].workers,
                        _votes[index]
                    )
                ].votesReceived++;
            }
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

    function checkVotesValidity(uint16[] memory _votes)
        internal
        returns (bool)
    {
        // Check correct number of votes
        if (_votes.length == topWorkersInRound) {
            for (uint16 index = 0; index < _votes.length; index++) {
                // Check correct bound of the vote
                if (_votes[index] < 0 && _votes[index] >= workersInRound) {
                    return false;
                }
                for (uint16 k = index + 1; k < _votes.length; k++) {
                    if (_votes[index] == _votes[k]) {
                        return false;
                    }
                }
            }
        } else {
            return false;
        }
        return true;
    }

    function convertIndexesToAddresses(uint16[] memory _votes)
        internal
        returns (address[] memory)
    {
        address[] memory votesAddresses = new address[](_votes.length);
        for (uint256 i = 0; i < _votes.length; i++) {
            votesAddresses[i] = EnumerableSet.at(
                rounds[rounds.length - 2].workers,
                _votes[i]
            );
        }
        return votesAddresses;
    }

    function commitSecretVote(bytes32 _secretVote) external {
        // Check if it is the last round
        require(
            state == STATE.LAST_ROUND_IN_PROGRESS,
            "You cannot commit a secret vote in this phase!"
        );
        // Check if the workers is one of the round and it has not already committed
        require(
            EnumerableSet.contains(
                rounds[rounds.length - 1].workers,
                msg.sender
            ),
            "You are not a selected worker of this round!"
        );
        require(
            addressToWorkerInfo[msg.sender].secretVote == 0,
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
            startTimer(voteMinutes);
            emit LastRoundDisclosurePhase();
        }
    }

    function discloseSecretVote(uint16[] memory _votes, string memory _salt)
        external
    {
        // Check disclosure phase
        require(
            state == STATE.LAST_ROUND_DISCLOSING,
            "You cannot disclose a secret vote in this phase!"
        );
        // Check if the workers is one of the last round and it has committed a secret vote
        require(
            EnumerableSet.contains(
                rounds[rounds.length - 1].workers,
                msg.sender
            ),
            "You are not a selected worker of this round!"
        );
        require(
            addressToWorkerInfo[msg.sender].secretVote != 0,
            "You have not submitted your work in time!"
        );
        // Check the validity of the vote
        require(
            checkSecretVoteValidity(_votes, _salt),
            "Your secret votes are not valid!"
        );
        // Save and apply the vote (the parameter is the index of the voted models)
        addressToWorkerInfo[msg.sender]
            .votesGranted = convertIndexesToAddresses(_votes);
        for (uint16 index = 0; index < _votes.length; index++) {
            addressToWorkerInfo[
                EnumerableSet.at(
                    rounds[rounds.length - 2].workers,
                    _votes[index]
                )
            ].votesReceived++;
        }
        rounds[rounds.length - 1].roundCommitment++;
        // If it is the last disclosure, end the task
        if (rounds[rounds.length - 1].roundCommitment == workersInRound) {
            state = STATE.TASK_ENDED;
            emit TaskEnded();
        }
    }

    function checkSecretVoteValidity(
        uint16[] memory _votes,
        string memory _salt
    ) internal returns (bool) {
        if (
            keccak256(abi.encodePacked(_votes, _salt)) ==
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

    // Fake function to be deleted after testing locally
    // function fulfillRandomnessTesting(uint256 _randomness) public {
    //     require(state == STATE.ROUND_PREPARATION, "You aren't there yet!");
    //     require(_randomness > 0, "random-not-found");
    //     startRound(_randomness);
    // }

    // function getWorkersInRound(uint256 index)
    //     public
    //     view
    //     returns (address[] memory)
    // {
    //     require(index < rounds.length, "Index out of bound!");
    //     address[] memory temp = new address[](
    //         EnumerableSet.length(rounds[index].workers)
    //     );
    //     for (uint256 i = 0; i < temp.length; i++) {
    //         temp[i] = EnumerableSet.at(rounds[index].workers, i);
    //     }
    //     return temp;
    // }

    // function getRankingInRound(uint256 index)
    //     public
    //     view
    //     returns (address[] memory)
    // {
    //     require(index < rounds.length, "Index out of bound!");
    //     return rounds[index].ranking;
    // }
}
