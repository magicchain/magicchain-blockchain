pragma solidity ^0.5.0;

contract owned {
    address public owner;
    address public candidate;

    constructor() payable public {
        owner = msg.sender;
    }
    
    modifier onlyOwner {
        require(owner == msg.sender);
        _;
    }
    function changeOwner(address _owner) onlyOwner public {
        candidate = _owner;
    }
    
    function confirmOwner() public {
        require(candidate == msg.sender);
        owner = candidate;
        delete candidate;
    }
}

contract IMagicChain 
{
    function transfer(address _to, uint _value) public returns(bool);
    function balanceOf(address _holder) view public returns(uint);
}

contract ColdStorage is owned
{
    address public ColdStacking;
    IMagicChain public MagicChain;

    modifier onlyColdStacking 
    {
        require(ColdStacking == msg.sender);
        _;
    }
    modifier ownerOrColdStacking 
    {
        require(msg.sender == ColdStacking || msg.sender == owner);
        _;
    }

    constructor(address coldStacking, address magicChain) public 
    {
        ColdStacking = coldStacking;
        MagicChain = IMagicChain(magicChain);
    }

    function setColdStacking(address coldStacking) public onlyOwner { ColdStacking = coldStacking; }
    function setMagicChain(address magicChain) public onlyOwner { MagicChain = IMagicChain(magicChain); }
    
    function transfer(address _to, uint _value) public ownerOrColdStacking returns(bool)
    {
        return MagicChain.transfer(_to, _value);
    }
    
    function balanceOf(address _holder) view public returns(uint)
    {
        return MagicChain.balanceOf(_holder);
    }
  
}