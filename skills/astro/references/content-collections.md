# Content collections

Verified against: Astro 7.3

## Contents

- [Shape of the current API](#shape-of-the-current-api)
- [Build-time collections](#build-time-collections)
- [Built-in loaders](#built-in-loaders)
- [`glob()` options that matter at scale](#glob-options-that-matter-at-scale)
- [Schemas](#schemas)
- [References between collections](#references-between-collections)
- [Images in collection schemas](#images-in-collection-schemas)
- [Querying](#querying)
- [Rendering body content](#rendering-body-content)
- [Generating routes](#generating-routes)
- [Custom build-time loaders](#custom-build-time-loaders)
- [Live collections](#live-collections)
- [Failure modes](#failure-modes)

## Shape of the current API

Every collection is defined by a **loader** and, optionally, a Zod **schema**.
There are two kinds:

| | Build-time | Live |
|---|---|---|
| Config file | `src/content.config.ts` | `src/live.config.ts` |
| Definition | `defineCollection()` | `defineLiveCollection()` |
| Query | `getCollection()`, `getEntry()`, `getEntries()` | `getLiveCollection()`, `getLiveEntry()` |
| Runs | During build / content sync, persisted to the data store | On every request |
| Needs an adapter | No | Yes |

Both files may exist in one project; pick per data source. Default to build-time
and use live only when the data must be current at request time — live
collections re-fetch per request, cannot render MDX, and cannot optimise images.
`[official]`

## Build-time collections

```ts
// src/content.config.ts
import { defineCollection, reference } from "astro:content";
import { glob, file } from "astro/loaders";
import { z } from "astro/zod";

const blog = defineCollection({
  loader: glob({ pattern: "**/*.{md,mdx}", base: "./src/content/blog" }),
  schema: z.object({
    title: z.string(),
    description: z.string(),
    pubDate: z.coerce.date(),
    updatedDate: z.coerce.date().optional(),
    author: reference("authors"),
    tags: z.array(z.string()).default([]),
    draft: z.boolean().default(false),
  }),
});

const authors = defineCollection({
  loader: glob({ pattern: "**/*.json", base: "./src/data/authors" }),
  schema: z.object({
    name: z.string(),
    homepage: z.url().optional(),
  }),
});

export const collections = { blog, authors };
```

Three things about this file are load-bearing:

- The path is `src/content.config.ts`, not `src/content/config.ts`. The old
  location is not read. `[official]`
- `loader` is required. There is no `type: "content"` / `type: "data"` any more,
  and no implicit collection created by a folder under `src/content/` — that
  directory is now just a place the loader's `base` happens to point at.
  `[official]`
- `z` comes from `astro/zod`. Importing it from `astro:content`, or from
  `astro:schema`, is deprecated; importing a separately installed `zod` risks a
  different major version than the one Astro validates with. `[official]`

Run `astro sync` (or any `astro dev` / `astro build` / `astro check`) after
changing this file — collection types are generated into `.astro/types.d.ts`,
and a stale file is the usual cause of "property does not exist on type"
directly after an edit.

## Built-in loaders

`glob({ pattern, base })` loads a directory of Markdown, MDX, Markdoc, JSON,
YAML or TOML files, generating a URL-friendly `id` per file. `pattern` uses
micromatch syntax.

`file(path, { parser? })` loads many entries from **one** file. JSON and YAML
arrays and TOML top-level tables are parsed automatically. Each entry must carry
its own unique `id` — unlike `glob()`, `file()` generates nothing. Use `parser`
for anything else, including selecting one key out of a combined document:

```ts
const dogs = defineCollection({
  loader: file("src/data/pets.json", { parser: (text) => JSON.parse(text).dogs }),
});
```

## `glob()` options that matter at scale

- `generateId: ({ entry, base, data }) => string` overrides the default
  `github-slugger` id. The default lowercases; supply this when ids must keep
  their original case or come from a data field. `[official]`
- `retainBody: false` (default `true`) drops the raw source from the data store.
  `entry.body` becomes `undefined`, while `entry.rendered.html` and
  `entry.filePath` still work. This is the fix for a deployed data store that has
  grown past a platform size limit, and it is dramatic for MDX. `[official]`
- `deferRender: true` (Astro 7.1+, default `false`) stops the loader from
  rendering every Markdown entry during sync and instead renders on use. The
  default eager rendering caches HTML across builds, but holding all of it in
  memory is what makes a very large collection run the build out of memory. It
  has no effect on MDX, Markdoc or data entries. `[official]`

Reach for `retainBody: false` for a *size* limit and `deferRender: true` for an
*out-of-memory* build; they solve different problems.

## Schemas

The schema validates each entry at sync time and produces the entry types. Zod 4
semantics apply: `[official]`

- Formats live at the top level: `z.email()`, `z.url()`, `z.uuid()` — not
  `z.string().email()`.
- Custom messages use `error`, not `message`: `z.string().min(5, { error: "…" })`.
- `.default()` must match the **output** type, after transforms. Use
  `.prefault()` for the old input-side behaviour.
- Frontmatter dates arrive as strings; `z.coerce.date()` converts them.

A validation failure fails the build with the offending file and field named.
That is the point — it turns "undefined title on one of 400 pages" into a build
error.

## References between collections

`reference("authors")` validates that the value names an existing entry and
converts it into a `{ collection, id }` handle. Resolve handles with `getEntry()`
or `getEntries()`:

```astro
---
import { getEntry, getEntries } from "astro:content";
const post = await getEntry("blog", Astro.params.id);
const author = await getEntry(post.data.author);
const related = await getEntries(post.data.relatedPosts);
---
```

## Images in collection schemas

Declare the schema as a function to receive the `image` helper. It validates the
frontmatter path relative to the entry file and returns image metadata usable as
`<Image src={…} />`: `[official]`

```ts
const blog = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/blog" }),
  schema: ({ image }) =>
    z.object({
      title: z.string(),
      cover: image(),
      coverAlt: z.string(),
    }),
});
```

A `z.string()` cover field yields a bare path with no dimensions, which is how
collection-driven pages end up shifting layout.

## Querying

```ts
const all = await getCollection("blog");
const one = await getEntry("dogs", "poodle");
const published = await getCollection("blog", ({ data }) => data.draft !== true);
const drafts = await getCollection("blog", ({ data }) =>
  import.meta.env.PROD ? data.draft !== true : true,
);
const englishDocs = await getCollection("docs", ({ id }) => id.startsWith("en/"));
```

`getCollection()` order is non-deterministic and platform-dependent. Sort
explicitly whenever order is visible: `[official]`

```ts
const posts = (await getCollection("blog")).sort(
  (a, b) => b.data.pubDate.valueOf() - a.data.pubDate.valueOf(),
);
```

Entries expose `id`, `data`, and (for Markdown-family entries) `body`. There is
no `slug` property; the routing key is `id`. Override it per entry with a `slug`
field in the frontmatter if a human-chosen permalink is needed — the value lands
in `id`.

## Rendering body content

`render()` is a standalone import, not a method on the entry: `[official]`

```astro
---
import { getEntry, render } from "astro:content";
const post = await getEntry("blog", "post-1");
if (!post) throw new Error("Entry not found");
const { Content, headings } = await render(post);
---
<h1>{post.data.title}</h1>
<Content />
```

`headings` is the rendered heading list, useful for a table of contents.

## Generating routes

Collections live outside `src/pages/`, so they produce no routes on their own.

Static build:

```astro
---
// src/pages/posts/[id].astro
import { getCollection, render } from "astro:content";

export async function getStaticPaths() {
  const posts = await getCollection("blog");
  return posts.map((post) => ({ params: { id: post.id }, props: { post } }));
}

const { post } = Astro.props;
const { Content } = await render(post);
---
<Content />
```

On demand, with an adapter: read the param, query directly, and handle the miss.
Use `getEntry()` for a build-time collection and `getLiveEntry()` for a live one.

## Custom build-time loaders

A custom loader fetches from a CMS, database or API during the build and writes
into the data store, which buys the same `getCollection()` / `render()` surface
and schema validation as local files. When a loader supplies a `schema`, declare
it with `createSchema()` and type the loader object with `satisfies` — schema
types are inferred now, not generated, and a plain function-valued `schema` is
no longer supported. `[official]`

## Live collections

```ts
// src/live.config.ts
import { defineLiveCollection } from "astro:content";
import { z } from "astro/zod";
import { storeLoader } from "@mystore/astro-loader";

const products = defineLiveCollection({
  loader: storeLoader({ endpoint: process.env.STORE_API }),
  schema: z.object({ id: z.string(), name: z.string(), price: z.number() }),
});

export const collections = { products };
```

There are no built-in live loaders — supply a third-party one or implement
`loadCollection` / `loadEntry` yourself. Queries return `{ entries, error }` or
`{ entry, error }`; the error is an `AstroError`, and a live page should handle
it (commonly `Astro.rewrite("/404")`) rather than assume data. A schema, when
present, takes precedence over the loader's own types. `[official]`

Live loaders may return cache hints, which surface as `cacheHint` on the result
and feed the route cache without hand-written headers (Astro 7+).

## Failure modes

| Symptom | Cause |
|---|---|
| `Collection does not exist` after adding a folder | No collection defined; a folder under `src/content/` is not a collection by itself |
| `Content collection missing loader` | `type:` was used instead of `loader:` |
| Types missing right after editing the config | `.astro/types.d.ts` is stale; run `astro sync` |
| `entry.slug` is `undefined` | Use `entry.id` |
| `post.render is not a function` | Use the standalone `render(post)` |
| Zod error on `z.string().email()` | Zod 4 moved formats to `z.email()` |
| Build out of memory on a large Markdown collection | Eager render during sync; set `deferRender: true` |
| Deployed data store over the platform size limit | Set `retainBody: false` |
| Pages ordered differently between machines | `getCollection()` order is unspecified; sort explicitly |

<!-- sources: withastro-docs, awesome-copilot-astro, gigio-astro-dev, incluud-astro-skills -->
