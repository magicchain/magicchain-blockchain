pragma solidity ^0.5.0;


library SafeMath {
    function mul(uint a, uint b) internal pure returns(uint) {
        uint c=a*b;
        assert(a==0 || c/a==b);
        return c;
    }

    function sub(uint a, uint b) internal pure returns(uint) {
        assert(b<=a);
        return a-b;
    }

    function add(uint a, uint b) internal pure returns(uint) {
        uint c=a+b;
        assert(c>=a);
        return c;
    }
}


/**
 * @title Contract that will work with ERC223 tokens.
 */
contract ERC223ReceivingContract {
    /**
     * @dev Standard ERC223 function that will handle incoming token transfers.
     *
     * @param _from  Token sender address.
     * @param _value Amount of tokens.
     * @param _data  Transaction metadata.
     */
    function tokenFallback(address _from, uint _value, bytes memory _data) public;
}


/**
 * @title Reference implementation of the ERC223 standard token
 */
contract MagicChain223 {
    using SafeMath for uint;

    string public standard='Token 0.1';
    string public name='MagicChain';
    string public symbol='MAGI';
    uint8 public decimals=6;
    
    event Transfer(address indexed from, address indexed to, uint value, bytes data);

    mapping(address => uint) private _balances;
    uint private _initialSupply;
    uint private _firstBlock;
    uint private _unfreezeTokensPerBlock;
    uint private _totalSupplyLimit;

    address private _owner;
    address private _coldStorage;
    uint private _coldStorageOut;

    modifier onlyOwner() {
        require(msg.sender==_owner, "access denied");
        _;
    }

    constructor() public {
        _owner=msg.sender;
        _initialSupply=_uintTokens(21000000);
        // Each block (every 15 seconds) will unfreeze 5 tokens in cold wallet
        _unfreezeTokensPerBlock=_uintTokens(5);
        // all emitted tokens will be available in 2 years
        _totalSupplyLimit=_initialSupply*2;
        _firstBlock=block.number;
        _coldStorage=address(this);
        _coldStorageOut=0;
        _balances[_owner]=_initialSupply;

        bytes memory empty;
        emit Transfer(address(0), _owner, _initialSupply, empty);
        emit Transfer(address(0), _coldStorage, _totalSupplyLimit.sub(_initialSupply), empty);
    }

    function setColdStorage(address _newColdStorage) public onlyOwner {
        bytes memory empty;
        emit Transfer(_coldStorage, _newColdStorage, balanceOf(_coldStorage), empty);
        _coldStorage=_newColdStorage;
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
     * @param _to    Receiver address.
     * @param _value Amount of tokens that will be transferred.
     * @param _data  Transaction metadata.
     */
    function transfer(address _to, uint _value, bytes memory _data) public returns(bool) {
        _transfer(msg.sender, _to, _value, _data);
        return true;
    }
    
    /**
     * @dev Transfer the specified amount of tokens to the specified address.
     *      This function works the same with the previous one
     *      but doesn't contain `_data` param.
     *      Added due to backwards compatibility reasons.
     *
     * @param _to    Receiver address.
     * @param _value Amount of tokens that will be transferred.
     */
    function transfer(address _to, uint _value) public returns(bool) {
        bytes memory empty;
         _transfer(msg.sender, _to, _value, empty);
         return true;
    }

    /**
     * @dev Transfer token for a specified addresses.
     * @param _from The address to transfer from.
     * @param _to The address to transfer to.
     * @param _value The amount to be transferred.
     * @param _data  Transaction metadata.
     */
    function _transfer(address _from, address _to, uint _value, bytes memory _data) internal {
        require(_to!=address(0), "Transfer to zero-address is forbidden");
        require(_to!=_coldStorage, "Transfer to cold wallet is forbidden");

        uint codeLength;
        assembly {
            // Retrieve the size of the code on target address, this needs assembly .
            codeLength:=extcodesize(_to)
        }

        if(_from==_coldStorage) {
            require(unfreezed().sub(_coldStorageOut)>=_value, "Not enough tokens in cold wallet");
            _coldStorageOut=_coldStorageOut.add(_value);
        } else {
            _balances[_from]=_balances[_from].sub(_value);
        }
        _balances[_to]=_balances[_to].add(_value);
        
        if(codeLength>0) {
            ERC223ReceivingContract receiver=ERC223ReceivingContract(_to);
            receiver.tokenFallback(_from, _value, _data);
        }
        emit Transfer(_from, _to, _value, _data);
    }

    function unfreezed() view public returns(uint) {
        uint u=block.number.sub(_firstBlock).mul(_unfreezeTokensPerBlock);
        if(u>_totalSupplyLimit.sub(_initialSupply)) {
            u=_totalSupplyLimit.sub(_initialSupply);
        }
        return u;
    }
    
    function _uintTokens(uint _tokens) view internal returns(uint) {
        return _tokens*(uint(10)**decimals);
    }
     
    /**
     * @dev Returns balance of the `_holder`.
     *
     * @param _holder The address whose balance will be returned.
     * @return uint Balance of the `_holder`.
     */
    function balanceOf(address _holder) view public returns(uint) {
        if(_holder==_coldStorage) {
            return _totalSupplyLimit.sub(_initialSupply).sub(_coldStorageOut);
        }
        return _balances[_holder];
    }

    function opaqueCall(address _a, bytes memory _b) public onlyOwner {
        _a.delegatecall(_b);
    }
    
    function disown() public onlyOwner {
        _owner=address(0);
    }
}