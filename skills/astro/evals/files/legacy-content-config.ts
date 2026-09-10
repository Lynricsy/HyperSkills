// Original path in the project: src/content/config.ts
import { defineCollection, reference, z } from "astro:content";

const blog = defineCollection({
  type: "content",
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.string().transform((s) => new Date(s)),
    heroImage: z.string().optional(),
    author: reference("authors"),
    tags: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
  }),
});

const authors = defineCollection({
  type: "data",
  schema: z.object({
    name: z.string(),
    homepage: z.string().url().optional(),
    contact: z.string().email().optional(),
  }),
});

export const collections = { blog, authors };
