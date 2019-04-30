using System.Collections.Generic;

namespace DBankModel2.Blockchains
{
    public class Blockchain
    {
        public int Number => Blocks.Count;
        public const int BlockTimeSeconds = 15;
        public List<BlockInfo> Blocks { get; set; } = new List<BlockInfo>();


    }
}
