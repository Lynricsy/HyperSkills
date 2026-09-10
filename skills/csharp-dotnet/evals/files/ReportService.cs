using System.Text;

namespace Orders.Reporting;

public sealed class ReportService
{
    private readonly IOrderStore _store;
    private readonly IPricingClient _pricing;
    private readonly ILogger<ReportService> _log;
    private readonly Dictionary<string, decimal> _fxRates;

    public ReportService(IOrderStore store, IPricingClient pricing, ILogger<ReportService> log)
    {
        _store = store;
        _pricing = pricing;
        _log = log;
        _fxRates = _pricing.GetRatesAsync().GetAwaiter().GetResult();
    }

    public async void Refresh()
    {
        await _store.RefreshAsync();
        _log.LogInformation("refreshed");
    }

    public async Task<string> BuildAsync(int[] orderIds)
    {
        var sb = new StringBuilder();

        foreach (var id in orderIds)
        {
            var order = await _store.GetAsync(id);
            var price = await _pricing.QuoteAsync(order.Sku);
            sb.Append(order.Sku + ":" + price + ";");
        }

        return sb.ToString();
    }

    public async Task<decimal> TotalAsync(int orderId)
    {
        ValueTask<decimal> pending = _store.GetTotalAsync(orderId);

        if (await pending > 0)
        {
            _log.LogInformation("non-empty order");
        }

        return await pending;
    }

    public Task<string> RenderAsync(int orderId)
    {
        return Task.Run(async () =>
        {
            var order = await _store.GetAsync(orderId);
            return order.Sku.ToUpper();
        });
    }

    public void Enqueue(int orderId)
    {
        _ = _store.RefreshAsync();
    }

    public async Task<IReadOnlyList<string>> SkusAsync(int[] orderIds, CancellationToken ct)
    {
        var results = new List<string>();

        foreach (var id in orderIds)
        {
            var order = await _store.GetAsync(id).ConfigureAwait(false);
            results.Add(order.Sku);
        }

        Thread.Sleep(50);
        return results;
    }
}

public interface IOrderStore
{
    Task<OrderRow> GetAsync(int id);
    ValueTask<decimal> GetTotalAsync(int id);
    Task RefreshAsync();
}

public interface IPricingClient
{
    Task<decimal> QuoteAsync(string sku);
    Task<Dictionary<string, decimal>> GetRatesAsync();
}

public sealed record OrderRow(int Id, string Sku);

public interface ILogger<T>
{
    void LogInformation(string message);
}
