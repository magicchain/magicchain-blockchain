using System.Diagnostics;

namespace DBankModel2
{
    public static class IntExtensions
    {
        public static int mul(this int a, int b)
        {
            int c = a * b;
            Debug.Assert(a == 0 || c / a == b);
            return c;
        }

        public static int sub(this int a, int b)
        {
            Debug.Assert(b <= a);
            return a - b;
        }

        public static int add(this int a, int b)
        {
            int c = a + b;
            Debug.Assert(c >= a);
            return c;
        }

        public static decimal mul(this decimal a, decimal b)
        {
            decimal c = a * b;
            Debug.Assert(a == 0 || c / a == b);
            return c;
        }

        public static decimal sub(this decimal a, decimal b)
        {
            Debug.Assert(b <= a);
            return a - b;
        }

        public static decimal add(this decimal a, decimal b)
        {
            decimal c = a + b;
            Debug.Assert(c >= a);
            return c;
        }
    }
}