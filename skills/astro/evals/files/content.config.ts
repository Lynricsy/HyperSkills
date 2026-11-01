// src/content.config.ts (moved here from src/content/config.ts during the Astro 7 upgrade)
import { defineCollection, reference } from 'astro:content';
import { z } from 'astro/zod';

const blog = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    pubDate: z.coerce.date(),
    draft: z.boolean().default(false),
    author: reference('authors'),
  }),
});

const authors = defineCollection({
  type: 'data',
  schema: z.object({ name: z.string(), email: z.email() }),
});

export const collections = { blog, authors };
