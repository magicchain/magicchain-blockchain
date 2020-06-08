//SPDX-License-Identifier: GNU lesser General Public License

pragma solidity ^0.6.0;

import "github.com/OpenZeppelin/openzeppelin-contracts/contracts/access/Ownable.sol";
import "github.com/OpenZeppelin/openzeppelin-contracts/contracts/math/SafeMath.sol";
import "github.com/OpenZeppelin/openzeppelin-contracts/contracts/utils/Address.sol";


abstract contract ERC223ReceivingContract {
    function tokenFallback(address sender, uint amount, bytes memory data) public virtual;
}


contract MagicChain223 is Ownable {
    using SafeMath for uint;
    using Address for address;

    string public standard='Token 0.1';
    string public name='MagicChain';
    string public symbol='MAGI';
    uint8 public decimals=6;
    
    event Transfer(address indexed sender, address indexed receiver, uint amount, bytes data);

    mapping(address => uint) private _balances;
    uint private _initialSupply;
    uint private _firstBlock;
    uint private _unfreezeTokensPerBlock;
    uint private _totalSupplyLimit;

    address private _coldStorage;
    uint private _coldStorageOut;


    constructor() public {
        _initialSupply=_uintTokens(21000000);
        // Each block (every 15 seconds) will unfreeze 5 tokens in cold wallet
        _unfreezeTokensPerBlock=_uintTokens(5);
        // all emitted tokens will be available in 2 years
        _totalSupplyLimit=_initialSupply*2;
        _firstBlock=block.number;
        _coldStorage=address(this);
        _coldStorageOut=0;
        _balances[owner()]=_initialSupply;

        bytes memory empty = hex"00000000";
        emit Transfer(address(0), owner(), _initialSupply, empty);
        emit Transfer(address(0), _coldStorage, _totalSupplyLimit.sub(_initialSupply), empty);
    }

    function setColdStorage(address newColdStorage) public onlyOwner {
        bytes memory empty = hex"00000000";
        emit Transfer(_coldStorage, newColdStorage, balanceOf(_coldStorage), empty);
        _coldStorage=newColdStorage;
    }

    /**
     * @dev Total number of tokens in existence.
     */
    function totalSupply() public view returns(uint) {
        return _totalSupplyLimit;
    }

    /**
     * @dev Transfer the specified amount of tokens to the specified address.
     *      Invokes the `tokenFallback` function if the recipient is a contract.
     *      The token transfer fails if the recipient is a contract
     *      but does not implement the `tokenFallback` function
     *      or the fallback function to receive funds.
     *
     * @param receiver Receiver address.
     * @param amount   Amount of tokens that will be transferred.
     * @param data     Transaction metadata.
     */
    function transfer(address receiver, uint amount, bytes memory data) public returns(bool) {
        _transfer(msg.sender, receiver, amount, data);
        return true;
    }
    
    /**
     * @dev Transfer the specified amount of tokens to the specified address.
     *      This function works the same with the previous one
     *      but doesn't contain `_data` param.
     *      Added due to backwards compatibility reasons.
     *
     * @param receiver  Receiver address.
     * @param amount    Amount of tokens that will be transferred.
     */
    function transfer(address receiver, uint amount) public returns(bool) {
        bytes memory empty = hex"00000000";
         _transfer(msg.sender, receiver, amount, empty);
         return true;
    }

    /**
     * @dev Transfer token for a specified addresses.
     * @param sender   The address to transfer from.
     * @param receiver The address to transfer to.
     * @param amount   The amount to be transferred.
     * @param data     Transaction metadata.
     */
    function _transfer(address sender, address receiver, uint amount, bytes memory data) internal {
        require(receiver!=address(0), "Transfer to zero-address is forbidden");
        require(receiver!=_coldStorage, "Transfer to cold wallet is forbidden");

        if(sender==_coldStorage) {
            require(unfreezed().sub(_coldStorageOut)>=amount, "Not enough tokens in cold wallet");
            _coldStorageOut=_coldStorageOut.add(amount);
        } else {
            _balances[sender]=_balances[sender].sub(amount);
        }
        _balances[receiver]=_balances[receiver].add(amount);
        
        if(receiver.isContract()) {
            ERC223ReceivingContract(receiver).tokenFallback(sender, amount, data);
        }
        emit Transfer(sender, receiver, amount, data);
    }

    function unfreezed() view public returns(uint) {
        uint u=block.number.sub(_firstBlock).mul(_unfreezeTokensPerBlock);
        if(u>_totalSupplyLimit.sub(_initialSupply)) {
            u=_totalSupplyLimit.sub(_initialSupply);
        }
        return u;
    }
    
    function _uintTokens(uint tokens) view internal returns(uint) {
        return tokens*(uint(10)**decimals);
    }
     
    /**
     * @dev Returns balance of the `holder`.
     *
     * @param holder The address whose balance will be returned.
     * @return uint Balance of the `holder`.
     */
    function balanceOf(address holder) view public returns(uint) {
        if(holder==_coldStorage) {
            return _totalSupplyLimit.sub(_initialSupply).sub(_coldStorageOut);
        }
        return _balances[holder];
    }
}