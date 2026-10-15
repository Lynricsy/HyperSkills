using System.Threading.Tasks;
using Microsoft.Azure.Functions.Extensions.DependencyInjection;
using Microsoft.Azure.WebJobs;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Newtonsoft.Json;

[assembly: FunctionsStartup(typeof(Contoso.OrderSync.Startup))]

namespace Contoso.OrderSync
{
    public class Startup : FunctionsStartup
    {
        public override void Configure(IFunctionsHostBuilder builder)
        {
            builder.Services.AddSingleton<IErpClient, ErpClient>();
        }
    }

    // Payload published by the storefront; the ERP rejects messages whose field names differ.
    public class OrderMessage
    {
        [JsonProperty("order_id")]
        public string OrderId { get; set; }

        [JsonProperty("customer_ref")]
        public string CustomerRef { get; set; }

        [JsonProperty("total_cents")]
        public long TotalCents { get; set; }
    }

    public class SyncOrders
    {
        private readonly IErpClient _erp;
        public SyncOrders(IErpClient erp) => _erp = erp;

        [FunctionName("SyncOrders")]
        public async Task Run(
            [ServiceBusTrigger("orders", Connection = "ServiceBus")] OrderMessage order,
            [ServiceBus("erp-acks", Connection = "ServiceBus")] IAsyncCollector<OrderMessage> acks,
            ILogger log)
        {
            log.LogInformation("Syncing order {OrderId}", order.OrderId);
            await _erp.PushAsync(order);
            await acks.AddAsync(order);
        }
    }
}
