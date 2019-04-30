using System;
using System.Collections.Generic;
using System.IO;
using System.Reflection.Metadata;
using System.Text;
using System.Threading.Tasks;
using DBankModel2.Blockchains;
using DBankModel2.Modelling;

namespace DBankModel2
{
    class Program
    {
        private static Settings _settings = new Settings();
        

        static async Task Main(string[] args)
        {
            Console.WriteLine("***** Start *****");
            
            //await Task.Run(Run);

            var settings = new Settings();
            var blockchain = new Blockchain();
            var magicChain223 = new MagicChain223(settings, _settings.Owner, blockchain);
            var blockGenerator = new BlockGenerator(blockchain);
            var coldStackingModel = new ColdStackingModel(_settings,magicChain223, blockGenerator);

            var states = coldStackingModel.Run();
            var path = settings.OutputPath;

            StatPrinter.PrintStates(path, states, settings);

            Console.WriteLine("***** model process end *****");
            Console.WriteLine($"look at result here: {path}");
            Console.WriteLine($"press any key to continue...");
            Console.ReadKey();
        }
    }
}
