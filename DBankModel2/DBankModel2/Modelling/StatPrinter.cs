using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;
using DBankModel2.Blockchains;

namespace DBankModel2.Modelling
{
    public class StatPrinter 
    {
        public decimal InitialSupply { get; set; } = 21000000;
        public decimal UnfreezeTokensPerBlock { get; set; } = 5;
        public decimal TotalSupplyLimit { get; set; } = 42000000;

        public static void PrintStates(string path, List<ColdStackingState> states, Settings settings)
        {
            var cutDecimalCoef = (decimal)Math.Pow(10, MagicChain223.decimals);
            var startDate = new DateTime(DateTime.UtcNow.Year, 1, 1);

            var sb = new StringBuilder();
            // 5 ;
            sb.AppendLine(PrintKeyValue("startDate", startDate.ToShortDateString()));
            sb.AppendLine(PrintKeyValue("BlockTime, seconds", (settings.BlockTimeSeconds).ToString()));
            sb.AppendLine(PrintKeyValue("InitialSupply", settings.InitialSupply.ToString("F")));
            sb.AppendLine(PrintKeyValue("TotalSupplyLimit", settings.TotalSupplyLimit.ToString("F")));
            sb.AppendLine(PrintKeyValue("UnfreezeTokensPerBlock", settings.UnfreezeTokensPerBlock.ToString("F")));
            sb.AppendLine(PrintKeyValue("ColdPeriod, blocks", settings.ColdPeriodBlocks.ToString()));
            sb.AppendLine(PrintKeyValue("ColdPeriod, day", (settings.ColdPeriodBlocks * settings.BlockTimeSeconds / 60/60/24).ToString("F")));
            sb.AppendLine(PrintKeyValue("ModelPeriod, year", (settings.ModelPeriodSeconds / 31556926).ToString("F")));
            sb.AppendLine(PrintKeyValue("HoldPercent", (settings.HoldPercent).ToString("P")));
            sb.AppendLine(PrintKeyValue("", ""));
            sb.AppendLine($"BlockNumber;Supply;StakingRewardPool;OnColdStacking;Date;RewardPercent");
            for (int i = 0; i < states.Count; i++)
            {
                var state = states[i];
                sb.AppendLine(
                    $"{state.Block.Number};{state.Supply / cutDecimalCoef};{state.StakingRewardPool / cutDecimalCoef};{state.OnColdStacking / cutDecimalCoef};{GetDate(startDate, state)};{state.Percent:P}");
            }

            File.WriteAllText(path, sb.ToString());
        }

        private static string GetDate(DateTime startDate, ColdStackingState state)
        {
            return (startDate.AddSeconds(state.Block.Number * 15)).ToShortDateString();

        }

        private static string PrintKeyValue(string key, string value)
        {
            return $"{key};{value};;;;";
        }
    }
}