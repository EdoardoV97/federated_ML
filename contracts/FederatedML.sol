// SPDX-License-Identifier: MIT

pragma solidity ^0.8.13;

contract FederatedML {
    int256[] public model; // w_i
    int256 public totalDataPoints; // n_i

    constructor(uint256 _weightNumber) {
        model = new int256[](_weightNumber);
    }

    function retrieveModel() public view returns (int256[] memory, int256) {
        return (model, totalDataPoints);
    }

    // _newLocalModel = w_i*
    // _oldDataPoints = o_i* = old number of local data points
    // _newLocalDataPoints = n_i* = number of new local data points
    // o_i* + n_i* = number of local data points used to generate w_i*
    // n_i + n_i* = total number of global data points
    function updateModel(
        int256[] memory _newLocalModel,
        int256 _oldDataPoints,
        int256 _newLocalDataPoints
    ) public {
        for (uint256 i = 0; i < model.length; i++) {
            model[i] =
                ((totalDataPoints - _oldDataPoints) *
                    model[i] +
                    (_newLocalDataPoints + _oldDataPoints) *
                    _newLocalModel[i]) /
                (totalDataPoints + _newLocalDataPoints);
        }
        totalDataPoints += _newLocalDataPoints;
    }
}
