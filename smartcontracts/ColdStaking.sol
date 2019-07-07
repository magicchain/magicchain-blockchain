pragma solidity ^0.5.0;

/**
 * @title SafeMath
 * @dev Math operations with safety checks that throw on error
 */
library SafeMath {
  function mul(uint a, uint b) internal pure returns (uint) {
    if (a == 0) {
      return 0;
    }
    uint c = a * b;
    require(c / a == b);
    return c;
  }

  function div(uint a, uint b) internal pure returns (uint) {
    // assert(b > 0); // Solidity automatically throws when dividing by 0
    uint c = a / b;
    // assert(a == b * c + a % b); // There is no case in which this doesn't hold
    return c;
  }

  function sub(uint a, uint b) internal pure returns (uint) {
    require(b <= a);
    return a - b;
  }

  function add(uint a, uint b) internal pure returns (uint) {
    uint c = a + b;
    require(c >= a);
    return c;
  }
}

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

contract IColdStorage 
{
    function transfer(address _to, uint _value) public returns(bool);
    function balanceOf(address _holder) view public returns(uint);
}

interface IMagicChain {
    function totalSupply() external view returns (uint256);
    function balanceOf(address account) external view returns (uint256);
    function transfer(address recipient, uint256 amount) external returns (bool);
}

contract ColdStaking is owned, ERC223ReceivingContract
{
    // NOTE: The contract only works for intervals of time > round_interval
    using SafeMath for uint;

    event StartStaking(address _addr, uint _value, uint _amount, uint _time);
    event WithdrawStake(address _staker, uint _amount);
    event Claim(address _staker, uint _reward);
    event DonationDeposited(address _address, uint _value);

    struct Staker
    {
        uint amount;
        uint time;
    }

    uint public LastBlock = block.number;
    uint public Timestamp = now;    //timestamp of the last interaction with the contract.

    uint public TotalStakingWeight; //total weight = sum (each_staking_amount * each_staking_time).
    uint public TotalStakingAmount; //currently frozen amount for Staking.
    uint public StakingRewardPool;  //available amount for paying rewards.
    bool public CS_frozen;          //Cold Staking frozen.
    uint public Staking_threshold = 0;
    mapping(address => Staker) public Stakers;
    IColdStorage public ColdStorage; 
    IMagicChain public MagicChain; 

    uint public round_interval   = 27 days;      // 1 month.
    uint public max_delay        = 365 * 2 days; // 2 years.
    uint public DateStartStaking = 0;            // TODO: enter date when deploy to prod

    //========== TESTNET VALUES ===========
    //uint public round_interval   = 10 minutes; 
    //uint public max_delay        = 2 days;
    //uint public DateStartStaking = 0;
    //========== END TEST VALUES ==========
    
    constructor(address _magicChain, address _coldStorage) public 
    {
        setMagicChain(_magicChain);
        setColdStorage(_coldStorage);
    }
    
    
    function setColdStorage(address _coldStorage) public onlyOwner { ColdStorage = IColdStorage(_coldStorage); }
    function setMagicChain(address _magicChain) public onlyOwner { MagicChain = IMagicChain(_magicChain); }

    function freeze(bool _f) public onlyOwner
    {
        CS_frozen = _f;
    }

    function withdraw_rewards () public  onlyOwner
    {
        if (CS_frozen)
        {
            StakingRewardPool = ColdStorage.balanceOf(address(this)).sub(TotalStakingAmount);
            ColdStorage.transfer(owner, StakingRewardPool);
        }
    }

    function tokenFallback(address _from, uint _value, bytes memory _data) public only_erc223
    {
        startStaking(_from, _value);
    }
    
    function new_block() public
    {
        new_block(0);
    }
    
    // this function can be called for manualy update TotalStakingAmount value.
    function new_block(uint _value) internal
    {
        if (block.number > LastBlock)   //run once per block.
        {
            uint _LastBlock = LastBlock;
            LastBlock = block.number;

            StakingRewardPool = ColdStorage.balanceOf(address(this)).add(MagicChain.balanceOf(address(ColdStorage))).sub(TotalStakingAmount + _value);   //fix rewards pool for this block.
            // msg.value here for case new_block() is calling from startStaking(), and msg.value will be added to CurrentBlockDeposits.

            //The consensus protocol enforces block timestamps are always atleast +1 from their parent, so a node cannot "lie into the past". 
            if (now > Timestamp) //But with this condition I feel safer :) May be removed.
            {
                uint _blocks = block.number - _LastBlock;
                uint _seconds = now - Timestamp;
                if (_seconds > _blocks * 25) //if time goes far in the future, then use new time as 25 second * blocks.
                {
                    _seconds = _blocks * 25;
                }
                TotalStakingWeight += _seconds.mul(TotalStakingAmount);
                Timestamp += _seconds;
            }
        }
    }

    function startStaking(address _from, uint _value) internal staking_available
    {
        assert(_value >= Staking_threshold);
        new_block(_value); //run once per block.
        
        // claim reward if available.
        if (Stakers[_from].amount > 0)
        {
            if (Timestamp >= Stakers[_from].time + round_interval)
            { 
                claim(_from); 
            }
            TotalStakingWeight = TotalStakingWeight.sub((Timestamp.sub(Stakers[_from].time)).mul(Stakers[_from].amount)); // remove from Weight        
        }

        TotalStakingAmount = TotalStakingAmount.add(_value);
        Stakers[_from].time = Timestamp;
        Stakers[_from].amount = Stakers[_from].amount.add(_value);
       
        emit StartStaking(
            _from,
            _value,
            Stakers[_from].amount,
            Stakers[_from].time
        );
    }

    function withdraw_stake() public only_staker
    {
        new_block(0); //run once per block.
        require(Timestamp >= Stakers[msg.sender].time + round_interval); //reject withdrawal before complete round.

        uint _amount = Stakers[msg.sender].amount;
        // claim reward if available.
        claim(msg.sender); 
        TotalStakingAmount = TotalStakingAmount.sub(_amount);
        TotalStakingWeight = TotalStakingWeight.sub((Timestamp.sub(Stakers[msg.sender].time)).mul(Stakers[msg.sender].amount)); // remove from Weight.
        
        Stakers[msg.sender].amount = 0;
        MagicChain.transfer(msg.sender, _amount);
        emit WithdrawStake(msg.sender, _amount);
    }

    function claim() public only_staker
    {
        claim(msg.sender);
    }

    //claim rewards
    function claim(address _from) internal
    {
        if (CS_frozen) return; //Don't pay rewards when Cold Staking frozen.

        new_block(0); //run once per block
        uint _StakingInterval = Timestamp.sub(Stakers[_from].time);  //time interval of deposit.
        if (_StakingInterval >= round_interval)
        {
            uint _CompleteRoundsInterval = (_StakingInterval / round_interval).mul(round_interval); //only complete rounds.
            uint _StakerWeight = _CompleteRoundsInterval.mul(Stakers[_from].amount); //Weight of completed rounds.
            uint _reward = StakingRewardPool.mul(_StakerWeight).div(TotalStakingWeight);  //StakingRewardPool * _StakerWeight/TotalStakingWeight

            StakingRewardPool = StakingRewardPool.sub(_reward);
            TotalStakingWeight = TotalStakingWeight.sub(_StakerWeight); // remove paid Weight.

            Stakers[_from].time = Stakers[_from].time.add(_CompleteRoundsInterval); // reset to paid time, staking continue without a loss of incomplete rounds.
	    
            ColdStorage.transfer(_from, _reward);
            emit Claim(_from, _reward);
        }
    }

    //This function may be used for info only. This can show estimated user reward at current time.
    function stake_reward(address _addr) public view returns (uint)
    {
        require(Stakers[_addr].amount > 0);
        require(!CS_frozen);

        uint _blocks = block.number - LastBlock;
        uint _seconds = now - Timestamp;
        if (_seconds > _blocks * 25) //if time goes far in the future, then use new time as 25 second * blocks.
        {
            _seconds = _blocks * 25;
        }
        uint _Timestamp = Timestamp + _seconds;
        uint _TotalStakingWeight = TotalStakingWeight + _seconds.mul(TotalStakingAmount);
        uint _StakingInterval = _Timestamp.sub(Stakers[_addr].time); //time interval of deposit.
	
        //uint _StakerWeight = _StakingInterval.mul(Stakers[_addr].amount); //Staker weight.
        uint _CompleteRoundsInterval = (_StakingInterval / round_interval).mul(round_interval); //only complete rounds.
        uint _StakerWeight = _CompleteRoundsInterval.mul(Stakers[_addr].amount); //Weight of completed rounds.
        uint _StakingRewardPool = ColdStorage.balanceOf(address(this)).add(MagicChain.balanceOf(address(ColdStorage))).sub(TotalStakingAmount);
        return _StakingRewardPool.mul(_StakerWeight).div(_TotalStakingWeight);    //StakingRewardPool * _StakerWeight/TotalStakingWeight
    }

    modifier only_staker
    {
        require(Stakers[msg.sender].amount > 0);
        _;
    }
    
    modifier only_erc223
    {
        require(msg.sender == address(MagicChain));
        _;
    }


    modifier staking_available
    {
        require(now >= DateStartStaking && !CS_frozen);
        _;
    }

    //return deposit to inactive staker.
    function report_abuse(address _addr) public only_staker
    {
        require(Stakers[_addr].amount > 0);
        new_block(0); //run once per block.
        require(Timestamp > Stakers[_addr].time.add(max_delay));
        
        uint _amount = Stakers[_addr].amount;
        
        TotalStakingAmount = TotalStakingAmount.sub(_amount);
        TotalStakingWeight = TotalStakingWeight.sub((Timestamp.sub(Stakers[_addr].time)).mul(_amount)); // remove from Weight.

        Stakers[_addr].amount = 0;
        ColdStorage.transfer(_addr, _amount);
    }
}

