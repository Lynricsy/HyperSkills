// Home-feed schema, code-first with Pothos 4 (@pothos/core ^4.15).
import SchemaBuilder from '@pothos/core';

import type { Context, ImageRow, PostRow } from './context';

const builder = new SchemaBuilder<{
  Context: Context;
  Objects: { Post: PostRow; Image: ImageRow };
}>({});

builder.objectType('Image', {
  fields: (t) => ({
    url: t.exposeString('url'),
    width: t.exposeInt('width'),
  }),
});

builder.objectType('Post', {
  fields: (t) => ({
    id: t.exposeID('id', { nullable: false }),
    title: t.exposeString('title', { nullable: false }),
    // Ranking service; times out a few times an hour.
    relevanceScore: t.float({
      nullable: false,
      resolve: (post, _args, ctx) => ctx.ranking.score(post.id),
    }),
    // Image CDN metadata lookup.
    heroImage: t.field({
      type: 'Image',
      resolve: (post, _args, ctx) => ctx.cdn.lookup(post.heroImageId),
    }),
    tags: t.stringList({
      resolve: (post) => post.tags,
    }),
  }),
});

builder.queryType({
  fields: (t) => ({
    feed: t.field({
      type: ['Post'],
      args: { first: t.arg.int() },
      resolve: (_root, args, ctx) => ctx.db.feed(ctx.viewerId, args.first ?? 20),
    }),
  }),
});

export const schema = builder.toSchema();
