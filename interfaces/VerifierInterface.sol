pragma solidity ^0.8.13;

interface VerifierInterface {
    function isValid(bytes32 fact) external view returns (bool);
}
