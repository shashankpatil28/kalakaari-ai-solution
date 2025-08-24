// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Minimal anchoring contract for Merkle roots
contract AnchorRegistry {
    event Anchored(bytes32 indexed root, uint256 indexed batchId, address indexed caller);
    uint256 public nextBatchId = 1;

    function anchor(bytes32 root) external returns (uint256 batchId) {
        require(root != bytes32(0), "empty root");
        batchId = nextBatchId++;
        emit Anchored(root, batchId, msg.sender);
    }
}
