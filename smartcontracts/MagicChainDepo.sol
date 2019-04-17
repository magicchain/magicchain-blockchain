pragma solidity ^0.5.0;


contract Owned
{
    address public owner;
    address public newOwner;

    constructor() public
    {
        owner=msg.sender;
    }

    modifier onlyOwner
    {
        require(owner==msg.sender);
        _;
    }

    function changeOwner(address _newOwner) public onlyOwner
    {
        require(_newOwner!=address(0));
        newOwner=_newOwner;
    }

    function acceptOwnership() public
    {
        require(msg.sender==newOwner);
        owner=newOwner;
        delete newOwner;
    }
}

interface AbstractDepositHost
{
    function forwardETHDeposit(uint32 _userid) external payable;
}

interface ERC223
{
    function transfer(address _to, uint _value, bytes calldata _data) external returns(bool);
}

contract DepositWallet
{
    AbstractDepositHost private host;
    uint32 private userid;

    constructor(AbstractDepositHost _host, uint32 _userid) public
    {
        require(_host!=AbstractDepositHost(address(0)));

        host=_host;
        userid=_userid;
    }

    function() external payable
    {
        host.forwardETHDeposit.value(address(this).balance).gas(3000000)(userid);
    }

    function tokenFallback(address /*_from*/, uint _value, bytes calldata /*_data*/) external
    {
        bytes memory data=new bytes(4);
        data[0]=byte(uint8(userid/(2**24)));
        data[1]=byte(uint8(userid/(2**16)));
        data[2]=byte(uint8(userid/(2**8)));
        data[3]=byte(uint8(userid));

        require(ERC223(msg.sender).transfer(address(host), _value, data));
    }
}

contract DepositHost is Owned, AbstractDepositHost
{
    address payable public forwardAddress;
    address public depositMaster;
    mapping (uint32 => address) public depositAddresses;

    event ETHDeposit(uint32 userid, uint amountWei);
    event ERC223Deposit(address indexed contractAddress, uint32 userid, uint amount);
    event NewDepositAddress(uint32 userid, address depositAddress);

    modifier onlyDepositMaster
    {
        require(owner==msg.sender || depositMaster==msg.sender);
        _;
    }

    constructor() public
    {
        depositMaster=owner;
    }

    function setForwardAddress(address payable _forwardAddress) public onlyOwner
    {
        forwardAddress=_forwardAddress;
    }

    function setDepositMaster(address _depositMaster) public onlyOwner
    {
        depositMaster=_depositMaster;
    }

    function forwardETHDeposit(uint32 _userid) public payable
    {
        (bool success, bytes memory data)=forwardAddress.call.gas(3000000).value(address(this).balance)("");
        require(success);
        require(data.length==0);

        emit ETHDeposit(_userid, msg.value);
    }

    function getExistingDepositAddress(uint32 _userid) public view returns(address)
    {
        return depositAddresses[_userid];
    }

    function generateDepositAddress(uint32 _userid) public onlyDepositMaster
    {
        if(depositAddresses[_userid]==address(0))
        {
            depositAddresses[_userid]=address(new DepositWallet(this, _userid));
        }
        emit NewDepositAddress(_userid, depositAddresses[_userid]);
    }

    function tokenFallback(address /*_from*/, uint _value, bytes calldata _data) external
    {
        bytes memory empty;
        require(ERC223(msg.sender).transfer(forwardAddress, _value, empty));

        if(_data.length==4)
        {
            uint32 userid=uint8(byte(_data[0]))*(2**24)+
                          uint8(byte(_data[1]))*(2**16)+
                          uint8(byte(_data[2]))*(2**8)+
                          uint8(byte(_data[3]));
            emit ERC223Deposit(msg.sender, userid, _value);
        }
    }
}