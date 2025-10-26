// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * @title CraftAnchor
 * @dev Stores immutable hashes of artisan craft metadata on Polygon blockchain
 * @notice This contract provides tamper-proof anchoring of craft metadata hashes
 */
contract CraftAnchor {
    
    // Structure to store anchor details
    struct AnchorRecord {
        string publicId;      // CraftID (e.g., "CID-00001")
        uint256 timestamp;    // Block timestamp when anchored
        bool exists;          // Flag to check if hash exists
    }
    
    // Mapping from hash to anchor record
    mapping(bytes32 => AnchorRecord) public anchors;
    
    // Event emitted when a new hash is anchored
    event HashAnchored(
        bytes32 indexed hash,
        string publicId,
        uint256 timestamp,
        address indexed anchor
    );
    
    /**
     * @dev Anchors a metadata hash on the blockchain
     * @param h The SHA-256 hash of the craft metadata (32 bytes)
     * @param publicId The CraftID associated with this hash (e.g., "CID-00001")
     */
    function anchor(bytes32 h, string memory publicId) external {
        require(!anchors[h].exists, "Hash already anchored");
        require(bytes(publicId).length > 0, "Public ID cannot be empty");
        
        anchors[h] = AnchorRecord({
            publicId: publicId,
            timestamp: block.timestamp,
            exists: true
        });
        
        emit HashAnchored(h, publicId, block.timestamp, msg.sender);
    }
    
    /**
     * @dev Checks if a hash has been anchored
     * @param h The hash to check
     * @return exists Whether the hash exists on-chain
     * @return timestamp The block timestamp when it was anchored (0 if not anchored)
     */
    function isAnchored(bytes32 h) external view returns (bool exists, uint256 timestamp) {
        AnchorRecord memory record = anchors[h];
        return (record.exists, record.timestamp);
    }
    
    /**
     * @dev Gets the full anchor record for a hash
     * @param h The hash to look up
     * @return publicId The CraftID
     * @return timestamp The anchoring timestamp
     * @return exists Whether the record exists
     */
    function getAnchorRecord(bytes32 h) external view returns (
        string memory publicId,
        uint256 timestamp,
        bool exists
    ) {
        AnchorRecord memory record = anchors[h];
        return (record.publicId, record.timestamp, record.exists);
    }
}
