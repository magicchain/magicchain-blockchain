//SPDX-License-Identifier: GNU lesser General Public License

pragma solidity ^0.6.0;

import "github.com/OpenZeppelin/openzeppelin-contracts/contracts/token/ERC721/ERC721.sol";
import "github.com/OpenZeppelin/openzeppelin-contracts/contracts/access/Ownable.sol";


// @dev see https://github.com/magicchain/magicchain-blockchain/blob/master/doc/MagicItemFormat.md
contract MagicChain721 is ERC721, Ownable
{
    event MagicItemMinted(uint256 indexed tokenID, address indexed owner, uint256[5] item);
    event MagicItemChanged(uint256 indexed tokenID, address indexed owner, uint256[5] item);

    mapping(uint256 => uint256[5]) private _tokenContent;
    bool    private _sealed;
    uint256 private _mintCounter;


    constructor () public ERC721("MagicChain", "MCI")
    {
        _setBaseURI("https://magicchain.games/erc721/");
    }

    function seal() public onlyOwner
    {
        _sealed = true;
    }

    function setBaseURI(string memory uri) public onlyOwner
    {
        _setBaseURI(uri);
    }

    function transferFrom(address from, address to, uint256 tokenId) public override
    {
        safeTransferFrom(from, to, tokenId);
    }

    function mint(address to, uint256[5] memory item) public onlyOwner returns (uint256)
    {
        uint8 itemType = uint8((item[0] & uint256(0xe0)) >> 5);
        require(!_sealed || (itemType!=1 && itemType!=2), "MagicChain721: Can't mint epic or rare items after seal");

        uint tokenID = ++_mintCounter;
        _tokenContent[tokenID] = item;
        _safeMint(to, tokenID);
        
        emit MagicItemMinted(tokenID, to, item);
        return tokenID;
    }
    
    function tokenContent(uint256 tokenID) external view returns (uint256[5] memory)
    {
        require(_exists(tokenID), "MagicChain721: Content query for nonexistent token");
        return _tokenContent[tokenID];
    }

    function _itemLevel(uint256 b0) internal pure returns (uint8)
    {
        return uint8((b0 & (uint256(0x7f) << 69)) >> 69);
    }
    
    function _itemModifiers(uint256 b0) internal pure returns (uint8)
    {
        return uint8((b0 & (uint256(0xff) << 76)) >> 76);
    }
    
    function _itemExtensions(uint256 b0) internal pure returns (uint8)
    {
        return uint8((b0 & (uint256(0xf) << 84)) >> 84);
    }
    
    function _canBeChanged(uint256 itemFromB0, uint256 itemToB0) internal pure
    {
        require((itemFromB0 & uint256(0x3fffff)) == (itemToB0 & uint256(0x3fffff)), "MagicChain721: Constant part of content can't be changed");
        require(_itemLevel(itemFromB0) <= _itemLevel(itemToB0), "MagicChain721: Level can't be decreased");
        require(_itemExtensions(itemFromB0) <= _itemExtensions(itemToB0), "MagicChain721: Amount of extensions can't be decreased");
        require(_itemModifiers(itemFromB0) <= _itemModifiers(itemToB0), "MagicChain721: Amount of modifiers can't be decreased");
    }
    
    function setTokenContent(uint256 tokenID, address to, uint256[5] memory item) public onlyOwner
    {
        require(_exists(tokenID), "MagicChain721: setContent query for nonexistent token");
        _canBeChanged(_tokenContent[tokenID][0], item[0]);
        _tokenContent[tokenID] = item;
        safeTransferFrom(_msgSender(), to, tokenID);
        emit MagicItemChanged(tokenID, to, item);
    }
}