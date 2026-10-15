using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Billing.Tests
{
    [TestClass]
    public class InvoiceCalculatorTests
    {
        [TestMethod]
        public void Total_SumsLineItems()
        {
            var calc = new InvoiceCalculator();
            Assert.AreEqual(2448L, calc.Total(new[] { (1099L, 2), (250L, 1) }));
        }
    }
}
