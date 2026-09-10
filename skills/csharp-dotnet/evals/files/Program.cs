using Microsoft.EntityFrameworkCore;

var builder = WebApplication.CreateBuilder(args);

builder.Services.AddDbContext<OrdersDbContext>(o =>
    o.UseSqlServer(builder.Configuration.GetConnectionString("Orders")));

builder.Services.AddScoped<IOrderRepository, OrderRepository>();

// Warm cache shared by every request.
builder.Services.AddSingleton<IOrderCache, OrderCache>();

builder.Services.AddSingleton<TenantResolver>();

var probe = builder.Services.BuildServiceProvider();
var startupOptions = probe.GetRequiredService<IConfiguration>().GetSection("Orders");
builder.Services.AddSingleton(new OrdersOptions { Region = startupOptions["Region"]! });

builder.Services.AddOpenApi();

var app = builder.Build();

app.UseMiddleware<TenantMiddleware>();

app.MapGet("/orders/{id:int}", async (int id, IOrderRepository repo) =>
{
    var order = await repo.FindAsync(id);
    if (order is null)
    {
        return Results.NotFound();
    }

    return Results.Ok(order);
});

app.MapPost("/orders", async (CreateOrderRequest request, IOrderRepository repo) =>
{
    var created = await repo.AddAsync(request);
    return Results.Created($"/orders/{created.Id}", created);
});

app.MapGet("/orders/report", (IOrderCache cache) =>
{
    using var http = new HttpClient();
    var raw = http.GetStringAsync("https://internal/reporting/orders").Result;
    return Results.Text(cache.Describe() + raw);
});

app.MapOpenApi();
app.Run();

public sealed class OrderCache : IOrderCache
{
    private readonly OrdersDbContext _db;
    private readonly Dictionary<int, string> _names = new();

    public OrderCache(OrdersDbContext db) => _db = db;

    public string Describe()
    {
        if (_names.Count == 0)
        {
            foreach (var order in _db.Orders.AsNoTracking())
            {
                _names[order.Id] = order.CustomerName;
            }
        }

        return string.Join(",", _names.Values);
    }
}

public sealed class TenantMiddleware
{
    private readonly RequestDelegate _next;
    private readonly IOrderRepository _repo;

    public TenantMiddleware(RequestDelegate next, IOrderRepository repo)
    {
        _next = next;
        _repo = repo;
    }

    public async Task InvokeAsync(HttpContext context)
    {
        context.Items["tenant"] = await _repo.ResolveTenantAsync(context.Request.Host.Host);
        await _next(context);
    }
}

public interface IOrderCache
{
    string Describe();
}

public interface IOrderRepository
{
    Task<Order?> FindAsync(int id);
    Task<Order> AddAsync(CreateOrderRequest request);
    Task<string> ResolveTenantAsync(string host);
}

public sealed record CreateOrderRequest(string CustomerName, decimal Total);

public sealed class Order
{
    public int Id { get; set; }
    public string CustomerName { get; set; } = "";
}

public sealed class OrdersOptions
{
    public string Region { get; set; } = "";
}

public sealed class TenantResolver;

public sealed class OrdersDbContext(DbContextOptions<OrdersDbContext> options) : DbContext(options)
{
    public DbSet<Order> Orders => Set<Order>();
}

public sealed class OrderRepository(OrdersDbContext db) : IOrderRepository
{
    public Task<Order?> FindAsync(int id) => db.Orders.FirstOrDefaultAsync(o => o.Id == id);

    public async Task<Order> AddAsync(CreateOrderRequest request)
    {
        var order = new Order { CustomerName = request.CustomerName };
        db.Orders.Add(order);
        await db.SaveChangesAsync();
        return order;
    }

    public Task<string> ResolveTenantAsync(string host) => Task.FromResult(host);
}
