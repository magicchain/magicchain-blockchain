using System;
using System.Collections.Generic;

namespace DBankModel2.Blockchains
{
    public class MagicChain223
    {
        public const int decimals = 6;
        private decimal _initialSupply;
        private int _firstBlock;
        private decimal _unfreezeTokensPerBlock;
        private decimal _totalSupplyLimit;

        private readonly Settings _settings;
        string _owner;
        private readonly Blockchain _blockchain;
        string _coldStorage;
        decimal _coldStorageOut;

        Dictionary<string, decimal> _balances = new Dictionary<string, decimal>();

        public MagicChain223(
            Settings settings,
            string owner, 
            Blockchain blockchain)
        {
            _settings = settings;
            _owner = owner;
            _blockchain = blockchain;
            _initialSupply = UintTokens(settings.InitialSupply);
            _unfreezeTokensPerBlock = UintTokens(settings.UnfreezeTokensPerBlock);
            _totalSupplyLimit = UintTokens(settings.TotalSupplyLimit);
            _firstBlock = blockchain.Number;
            _coldStorage = string.Empty;
            _coldStorageOut = 0;
            _balances[_owner] = _initialSupply;
        }

        public void SetColdStorage(string newColdStorage)
        {
            _coldStorage = newColdStorage;
        }

        public decimal Supply => _initialSupply.add(Unfreezed());
        public decimal InitialSupply => _initialSupply;
        public decimal UnfreezeTokensPerBlock => _unfreezeTokensPerBlock;
        

        public decimal Unfreezed() 
        {
            decimal u = ((decimal)_blockchain.Number.sub(_firstBlock)).mul(_unfreezeTokensPerBlock);
            if (u > _initialSupply)
            {
                u = _totalSupplyLimit.sub(_initialSupply);
            }
            return u;
        }

        private void Require(bool condition)
        {
            if (!condition)
                throw new Exception("require failure");
        }

        private decimal UintTokens(decimal tokens)
        {
            return tokens * (int)Math.Pow(10, decimals);
        }

      
    }
}