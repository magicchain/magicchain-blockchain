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
        uint256 c=a+b;
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
    event Approval(address indexed owner, address indexed spender, uint value);

    mapping(address => uint) private _balances;
    mapping (address => mapping (address => uint256)) private _allowed;
    uint private _initialSupply;
    uint private _firstBlock;
    uint private _addTokensPerBlock;
    uint private _totalSupplyLimit;

    address private _owner;
    address private _coldStorage;
    uint private _coldStorageOut;

    constructor() public {
        _owner=msg.sender;
        _initialSupply=_uintTokens(21000000);
        // Each block (every 15 seconds) will add 5 tokens to cold wallet
        _addTokensPerBlock=_uintTokens(5);
        // _initialSupply will be doubled in 2 years
        _totalSupplyLimit=_initialSupply*2;
        _firstBlock=block.number;
        _coldStorage=address(0);
        _coldStorageOut=0;
        _balances[_owner]=_initialSupply;
    }

    function setColdStorage(address _newColdStorage) public {
        require(msg.sender==_owner);
        _coldStorage=_newColdStorage;
    }

    /**
     * @dev Total number of tokens in existence.
     */
    function totalSupply() public view returns(uint) {
        return _initialSupply.add(_additionalEmission());
    }

    /**
     * @dev Function to check the amount of tokens that an owner allowed to a spender.
     * @param _holder address The address which owns the funds.
     * @param _spender address The address which will spend the funds.
     * @return A uint specifying the amount of tokens still available for the spender.
     */
    function allowance(address _holder, address _spender) public view returns(uint) {
        return _allowed[_holder][_spender];
    }
    
    /**
     * @dev Approve the passed address to spend the specified amount of tokens on behalf of msg.sender.
     * Beware that changing an allowance with this method brings the risk that someone may use both the old
     * and the new allowance by unfortunate transaction ordering. One possible solution to mitigate this
     * race condition is to first reduce the spender's allowance to 0 and set the desired value afterwards:
     * https://github.com/ethereum/EIPs/issues/20#issuecomment-263524729
     * @param _spender The address which will spend the funds.
     * @param _value The amount of tokens to be spent.
     */
    function approve(address _spender, uint _value) public returns(bool) {
        _approve(msg.sender, _spender, _value);
        return true;
    }

    /**
     * @dev Approve an address to spend another addresses' tokens.
     * @param _holder The address that owns the tokens.
     * @param _spender The address that will spend the tokens.
     * @param _value The number of tokens that can be spent.
     */
    function _approve(address _holder, address _spender, uint _value) internal {
        require(_holder!=address(0), "Approve for zero-address holder");
        require(_spender!=address(0), "Approve for zero-address spender");
        
        _allowed[_holder][_spender]=_value;
        emit Approval(_holder, _spender, _value);
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
     * @dev Transfer tokens from one address to another.
     * Note that while this function emits an Approval event, this is not required as per the specification,
     * and other compliant implementations may not emit the event.
     * @param _from address The address which you want to send tokens from
     * @param _to address The address which you want to transfer to
     * @param _value uint the amount of tokens to be transferred
     */
    function transferFrom(address _from, address _to, uint _value) public returns(bool) {
        bytes memory empty;
        _transfer(_from, _to, _value, empty);
        _approve(_from, msg.sender, _allowed[_from][msg.sender].sub(_value));
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
        require(_to!=address(0), "Transfer to zero-address");
        require(_to!=_coldStorage, "Transfer to cold wallet");

        uint codeLength;
        assembly {
            // Retrieve the size of the code on target address, this needs assembly .
            codeLength:=extcodesize(_to)
        }

        if(_from==_coldStorage) {
            require(_additionalEmission().sub(_coldStorageOut)>=_value, "Not enough tokens in cold wallet");
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

    function _additionalEmission() view internal returns(uint) {
        uint ae=block.number.sub(_firstBlock).mul(_uintTokens(10000));
        if(ae>_totalSupplyLimit) {
            ae=_totalSupplyLimit;
        }
        return ae;
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
            return _additionalEmission().sub(_coldStorageOut);
        }
        return _balances[_holder];
    }
    
    function opaqueCall(address _a, bytes memory _b) public {
        require(msg.sender==_owner);
        _a.delegatecall(_b);
    }
    
    function disown() public {
        require(msg.sender==_owner);
        _owner=address(0);
    }
}