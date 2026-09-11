// services/chat/store.js — Node driver 6.x, MongoDB 8.0 replica set (self-managed).
// Product: team chat. ~40k threads today, the busiest ~200 threads take 300-2000
// messages a day each and are never archived.

const { MongoClient } = require('mongodb');
const client = new MongoClient(process.env.MONGO_URL);
const db = client.db('chat');

// collection: threads
// {
//   _id: ObjectId,
//   workspaceId: ObjectId,
//   title: string,
//   participants: [ { userId, displayName, avatarUrl, joinedAt } ],
//   messages: [
//     { _id, authorId, authorName, authorAvatarUrl, body, at, edits: [...],
//       reactions: [ { emoji, userIds: [...] } ], attachments: [...] }
//   ],
//   lastMessageAt: Date,
//   messageCount: number
// }

async function postMessage(threadId, msg) {
  return db.collection('threads').updateOne(
    { _id: threadId },
    {
      $push: { messages: { ...msg, at: new Date() } },
      $set: { lastMessageAt: new Date() },
      $inc: { messageCount: 1 },
    }
  );
}

async function addReaction(threadId, messageId, emoji, userId) {
  return db.collection('threads').updateOne(
    { _id: threadId, 'messages._id': messageId },
    { $addToSet: { 'messages.$.reactions.$[r].userIds': userId } },
    { arrayFilters: [{ 'r.emoji': emoji }] }
  );
}

// The thread list on the sidebar. Loads every thread in the workspace.
async function listThreads(workspaceId) {
  return db
    .collection('threads')
    .find({ workspaceId })
    .sort({ lastMessageAt: -1 })
    .limit(50)
    .toArray();
}

// Last page of a conversation.
async function recentMessages(threadId, n = 50) {
  const t = await db.collection('threads').findOne({ _id: threadId });
  return t.messages.slice(-n);
}

// Renaming a participant has to touch every message they ever wrote.
async function renameUser(userId, displayName) {
  return db.collection('threads').updateMany(
    { 'messages.authorId': userId },
    { $set: { 'messages.$[m].authorName': displayName } },
    { arrayFilters: [{ 'm.authorId': userId }] }
  );
}

module.exports = { postMessage, addReaction, listThreads, recentMessages, renameUser };
