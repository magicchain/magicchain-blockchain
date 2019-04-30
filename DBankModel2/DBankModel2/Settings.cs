
namespace DBankModel2
{
    public class Settings
    {
        public string Owner { get; set; } = "0x5115aAeD86eC9F8502340a316e640cA70051ad6c";
        public int BlockTimeSeconds { get; set; } = 15;
        public int ModelPeriodSeconds { get; set; } = 31556926 * 3; // 1 year
        public decimal HoldPercent { get; set; } = 1; 
        public int ColdPeriodBlocks { get; set; } = 172800;
        public decimal InitialSupply { get; set; } = 21000000;
        public decimal UnfreezeTokensPerBlock { get; set; } = 5;
        public decimal TotalSupplyLimit { get; set; } = 42000000;
        public string OutputPath { get; set; } = "ColdStackingModel.csv";
    }
}