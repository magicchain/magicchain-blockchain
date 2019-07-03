# Overview

This specification defines a content format of every magic item, described as ERC721 token, emitted by [MagicChain721 smartcontract](https://github.com/magicchain/magicchain-blockchain/blob/master/smartcontracts/MagicChain721.sol).

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in RFC 2119.

# Format in general

Every magic item content described as 5 words uint256. All unused bits MUST be set to zero.

# Format in details

## Word 1

No|Offset (bits)|Size (bits)|Description|Smartcontract restrictions
--------|--------|--------|--------|--------
1|0|5|Class of magic item|MUST be constant
2|5|3|Type of magic item (0 - general, 1 - epiq, 2 - rare, 3 - season)|MUST be constant
3|8|14|Kind of magic item of specified class and type|MUST be constant
4|22|13|Base power of magic item|-
5|35|10|Value of power increase|-
6|45|7|Probability of power increase|-
7|52|10|Value of power decrease|-
8|62|7|Probability of power decrease|-
9|69|7|Level of magic item|MUST NOT decrease
10|76|8|Counter of applied modifiers|MUST NOT descrease
11|81|4|Amount of extensions|MUST NOT descrease

If the number of extensions is not zero, then an array of extensions follows. Each item of array has the structure:

No|Offset (bits)|Size (bits)|Description|Smartcontract restrictions
--------|--------|--------|--------|--------
-|-|4|Class of extension|SHOULD NOT descrease
-|-|14|Kind of extension of specified class|SHOULD be constant

## Word 2

Continuos of array of extensions:

No|Offset (bits)|Size (bits)|Description|Smartcontract restrictions
--------|--------|--------|--------|--------
-|-|4|Class of extension|SHOULD NOT descrease
-|-|14|Kind of extension of specified class|SHOULD be constant

## Word 3

Reserved. MUST be zero.

## Word 4

Reserved. MUST be zero.

## Word 5

Reserved. MUST be zero.

# How to control content

To control content of magic items contract MagicChain721 functions can be used.


## Mint tokens with specified content

    /**
     * @dev Function to mint tokens.
     * @param to The address that will receive the minted tokens.
     * @param tokenId The token id to mint.
     * @param enableTime since enableTime token will become available.
     * @return A boolean that indicates if the operation was successful.
     */
    function mint(address to, uint256 tokenId,
                  uint256 b0, uint256 b1, uint256 b2, uint256 b3, uint256 b4,
                  string memory uri, uint256 enableTime) public onlyOwner returns (bool);

## Get content for specified token

    /**
     * @dev Returns content for a given token ID.
     * Throws if the token ID does not exist.
     * @param tokenId uint256 ID of the token to query
     */
    function tokenContent(uint256 tokenId) external view returns (uint256, uint256, uint256, uint256, uint256);

## Set content for specified token

    /**
     * @dev Function to set the token content for a given token.
     * Reverts if the token ID does not exist.
     * @param tokenId uint256 ID of the token to set its content
     */
    function setTokenContent(uint256 tokenId, uint256 b0, uint256 b1, uint256 b2, uint256 b3, uint256 b4)
    onlyOwner public;
