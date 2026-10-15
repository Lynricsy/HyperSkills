using System.Linq.Expressions;
using Microsoft.EntityFrameworkCore;

namespace Inventory.Import;

// .NET 10, EF Core 10 on SQL Server. Registered as scoped; the nightly job resolves one instance
// per supplier feed and calls ImportAsync once. About 3,000 suppliers are imported every night.
public sealed class StockImportService(InventoryDbContext db, ILogger<StockImportService> log)
{
    public async Task<int> ImportAsync(IAsyncEnumerable<FeedRow> feed, string supplierCode, CancellationToken ct)
    {
        // Load this supplier's products once so rows can be matched without a query per row.
        var products = await db.Products
            .Where(BuildSupplierFilter(supplierCode))
            .ToDictionaryAsync(p => p.Sku, ct);

        // Give expired reservations back to stock before applying the delivery feed.
        await db.Products
            .Where(p => p.SupplierCode == supplierCode && p.ReservationExpiresAt < DateTime.UtcNow)
            .ExecuteUpdateAsync(s => s
                .SetProperty(p => p.Stock, p => p.Stock + p.Reserved)
                .SetProperty(p => p.Reserved, 0), ct);

        var processed = 0;
        await foreach (var row in feed.WithCancellation(ct))
        {
            if (products.TryGetValue(row.Sku, out var product))
            {
                product.Stock += row.Delivered;
            }
            else
            {
                db.Products.Add(new Product { Sku = row.Sku, SupplierCode = supplierCode, Stock = row.Delivered });
            }

            processed++;
            var pending = db.ChangeTracker.Entries<Product>()
                .Count(e => e.State is EntityState.Added or EntityState.Modified);
            log.LogDebug("Processed {Processed} rows, {Pending} pending", processed, pending);

            if (pending >= 500)
            {
                await db.SaveChangesAsync(ct);
            }
        }

        await db.SaveChangesAsync(ct);
        return processed;
    }

    // Shared with the admin search screen, which composes several of these.
    private static Expression<Func<Product, bool>> BuildSupplierFilter(string supplierCode)
    {
        var p = Expression.Parameter(typeof(Product), "p");
        var body = Expression.Equal(
            Expression.Property(p, nameof(Product.SupplierCode)),
            Expression.Constant(supplierCode));
        return Expression.Lambda<Func<Product, bool>>(body, p);
    }
}

public sealed record FeedRow(string Sku, int Delivered);

public sealed class Product
{
    public int Id { get; set; }
    public required string Sku { get; set; }
    public required string SupplierCode { get; set; }
    public int Stock { get; set; }
    public int Reserved { get; set; }
    public DateTime? ReservationExpiresAt { get; set; }
}
