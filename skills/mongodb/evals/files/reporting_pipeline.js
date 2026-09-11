// jobs/reporting/monthlyMerchantReport.js
// Runs nightly. Took 40s in January, takes 22 minutes now.
// orders: ~9M docs. merchants: ~180k docs. refunds: ~1.4M docs.
//
// db.orders.getIndexes()
//   { v: 2, key: { _id: 1 },        name: '_id_' }
//   { v: 2, key: { createdAt: -1 }, name: 'createdAt_-1' }
//   { v: 2, key: { status: 1 },     name: 'status_1' }
// db.merchants.getIndexes()
//   { v: 2, key: { _id: 1 },        name: '_id_' }
//   { v: 2, key: { region: 1 },     name: 'region_1' }
// db.refunds.getIndexes()
//   { v: 2, key: { _id: 1 },        name: '_id_' }

const pipeline = [
  {
    $project: {
      merchantSlug: 1,
      status: 1,
      createdAt: 1,
      currency: 1,
      totalCents: 1,
      lineItems: 1,
      customer: 1,
      shipping: 1,
    },
  },
  { $sort: { createdAt: -1 } },
  {
    $match: {
      status: 'settled',
      createdAt: { $gte: new Date('2026-08-01'), $lt: new Date('2026-09-01') },
    },
  },
  {
    $lookup: {
      from: 'merchants',
      localField: 'merchantSlug',
      foreignField: 'slug',
      as: 'merchant',
    },
  },
  { $unwind: '$merchant' },
  {
    $lookup: {
      from: 'refunds',
      localField: '_id',
      foreignField: 'orderId',
      as: 'refunds',
    },
  },
  { $unwind: '$lineItems' },
  { $match: { 'lineItems.category': { $ne: 'gift-card' } } },
  {
    $facet: {
      byMerchant: [
        {
          $group: {
            _id: '$merchant.slug',
            gross: { $sum: '$lineItems.amountCents' },
            orders: { $addToSet: '$_id' },
            sample: { $push: '$$ROOT' },
          },
        },
        { $sort: { gross: -1 } },
      ],
      totals: [{ $count: 'orders' }],
      byRegion: [{ $group: { _id: '$merchant.region', gross: { $sum: '$lineItems.amountCents' } } }],
    },
  },
  { $project: { byMerchant: { $slice: ['$byMerchant', 50] }, totals: 1, byRegion: 1 } },
];

async function run(db) {
  return db.collection('orders').aggregate(pipeline, { allowDiskUse: true }).toArray();
}

// Paging the drill-down table underneath the report:
async function page(db, merchantSlug, pageNumber) {
  return db
    .collection('orders')
    .find({ merchantSlug, status: 'settled' })
    .sort({ createdAt: -1 })
    .skip(pageNumber * 100)
    .limit(100)
    .toArray();
}

module.exports = { pipeline, run, page };
