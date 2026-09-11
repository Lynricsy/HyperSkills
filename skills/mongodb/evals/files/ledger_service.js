// services/ledger/transfer.js — Node driver 6.x
// Deployed as 24 Kubernetes pods against a 3-member self-managed replica set.
// Symptoms in production:
//   * bursts of "connection pool cleared" and "Server selection timed out"
//   * one duplicated payout after a primary stepdown last month
//   * p99 on /transfer is 900ms although the server logs show no slow queries
//   * the nightly export job dies after ~12 minutes with "cursor id not found"

const { MongoClient } = require('mongodb');

async function transfer(fromId, toId, amountCents, idem) {
  const client = new MongoClient(process.env.MONGO_URL, {
    maxPoolSize: 500,
    minPoolSize: 100,
    retryWrites: false,
    w: 1,
    journal: false,
    serverSelectionTimeoutMS: 2000,
  });
  await client.connect();
  const db = client.db('ledger');
  const session = client.startSession();
  try {
    session.startTransaction();
    await db.collection('accounts').updateOne(
      { _id: fromId },
      { $inc: { balanceCents: -amountCents } },
      { session }
    );
    await db.collection('accounts').updateOne(
      { _id: toId },
      { $inc: { balanceCents: amountCents } },
      { session }
    );
    await db.collection('entries').insertOne(
      { fromId, toId, amountCents, idem, at: new Date() },
      { session }
    );
    // Post the webhook while the transaction is open so we never post for a
    // transfer that later rolls back.
    await postWebhook({ fromId, toId, amountCents });
    await session.commitTransaction();
  } catch (err) {
    await session.abortTransaction();
    throw err;
  } finally {
    await session.endSession();
    await client.close();
  }
}

// Read the balance straight after the transfer to render the receipt.
async function balanceAfterTransfer(db, accountId) {
  return db
    .collection('accounts')
    .findOne({ _id: accountId }, { readPreference: 'secondaryPreferred' });
}

// Nightly export.
async function exportAll(db, write) {
  const cursor = db.collection('entries').find({});
  for await (const doc of cursor) {
    await write(doc); // writes to S3, ~40ms each
  }
}

module.exports = { transfer, balanceAfterTransfer, exportAll };
