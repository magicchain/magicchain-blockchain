using System;
using System.Threading.Tasks;

namespace DBankModel2.Blockchains
{
    public class BlockGenerator 
    {
        private static long _blockNumber = 0;
        private readonly Blockchain _blockchain;

        public BlockGenerator(Blockchain blockchain) 
        {
            _blockchain = blockchain;
        }

        public BlockInfo NewBlock()
        {
            var block = new BlockInfo()
            {
                Number = ++_blockNumber,
                Hash = Guid.NewGuid().ToString(),
                TimespanUnixSeconds = new DateTimeOffset(DateTime.UtcNow).ToUnixTimeSeconds()
            };

            _blockchain.Blocks.Add(block);
            return block;
        }
    }
}