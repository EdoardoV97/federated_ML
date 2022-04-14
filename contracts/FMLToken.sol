// SPDX-License-Identifier: MIT
pragma solidity ^0.8.13;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract DappToken is ERC20 {
    constructor(uint256 initialSupply) public ERC20("FML Token", "FML") {
        _mint(msg.sender, initialSupply);
    }
}
