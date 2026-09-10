// Resolvers for the home feed. Backed by Postgres through a thin `db` helper
// and by the ranking service over HTTP.
import { db } from './db.js';
import { ranking } from './ranking.js';
import DataLoader from 'dataloader';

// One loader for the whole process so the cache survives between requests.
export const authorLoader = new DataLoader(async (ids) => {
  const rows = await db.query('SELECT * FROM authors WHERE id = ANY($1)', [ids]);
  return rows;
});

export const resolvers = {
  Query: {
    viewer: (_parent, _args, ctx) => db.one('SELECT * FROM users WHERE id = $1', [ctx.userId]),
    post: (_parent, { id }) => db.one('SELECT * FROM posts WHERE id = $1', [id]),
  },

  Viewer: {
    feed: async (viewer) =>
      db.query('SELECT * FROM posts WHERE author_id IN (SELECT followee_id FROM follows WHERE follower_id = $1) ORDER BY created_at DESC', [viewer.id]),
  },

  Post: {
    // Called once per post in the feed.
    author: (post) => authorLoader.load(post.author_id),

    comments: async (post) =>
      db.query('SELECT * FROM comments WHERE post_id = $1 ORDER BY created_at', [post.id]),

    likeCount: async (post) => {
      const row = await db.one('SELECT count(*) AS n FROM likes WHERE post_id = $1', [post.id]);
      return Number(row.n);
    },

    relevanceScore: async (post, _args, ctx) => {
      const res = await ranking.score({ postId: post.id, userId: ctx.userId });
      return res.score;
    },
  },

  Comment: {
    author: (comment) => authorLoader.load(comment.author_id),
  },

  Author: {
    followerCount: async (author) => {
      const row = await db.one('SELECT count(*) AS n FROM follows WHERE followee_id = $1', [author.id]);
      return Number(row.n);
    },
    posts: (author) => db.query('SELECT * FROM posts WHERE author_id = $1', [author.id]),
  },
};
