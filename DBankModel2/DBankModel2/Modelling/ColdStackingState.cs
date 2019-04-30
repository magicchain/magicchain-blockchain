using DBankModel2.Blockchains;

namespace DBankModel2.Modelling
{
    public class ColdStackingState
    {
        public BlockInfo Block { get; set; }
        public decimal Supply { get; set; }
        public decimal StakingRewardPool { get; set; }
        public decimal OnColdStacking { get; set; }
        public decimal Percent { get; set; }
    }
}