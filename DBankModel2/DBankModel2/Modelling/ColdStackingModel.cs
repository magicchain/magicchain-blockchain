using System.Collections.Generic;
using System.Threading.Tasks;
using DBankModel2.Blockchains;

namespace DBankModel2.Modelling
{
    public class ColdStackingModel
    {
        private readonly MagicChain223 _magicChain223;
        private readonly BlockGenerator _blockGenerator;
        private readonly Settings _settings;

        public ColdStackingModel(
            Settings settings,
            MagicChain223 magicChain223,
            BlockGenerator blockGenerator)
        {
            _settings = settings;
            _magicChain223 = magicChain223;
            _blockGenerator = blockGenerator;
        }

        public List<ColdStackingState> Run()
        {
            var blockCount = _settings.ModelPeriodSeconds / _settings.BlockTimeSeconds;

            var states = new List<ColdStackingState>();
            decimal prevSupply = _magicChain223.InitialSupply;
            for (int i = 0; i < blockCount; i++)
            {
                var block = _blockGenerator.NewBlock();

                if (i != 0 && i % _settings.ColdPeriodBlocks == 0)
                {
                    var stakingRewardPool = _magicChain223.Supply - prevSupply;
                    var onColdStacking = prevSupply * _settings.HoldPercent;

                    states.Add(new ColdStackingState()
                    {
                        Block = block,
                        Supply = _magicChain223.Supply,
                        StakingRewardPool = stakingRewardPool,
                        OnColdStacking = onColdStacking,
                        Percent = stakingRewardPool / prevSupply
                    });

                    prevSupply = _magicChain223.Supply;
                }
            }

            return states;
        }
    }
}