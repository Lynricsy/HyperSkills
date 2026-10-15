# shortlinks

A tiny link-shortener API we want to run on Cloudflare. Nothing is set up yet - this repository
only has this README and `package.json`.

What it needs to do:

- `POST /links` with `{ "url": "https://..." }` creates a short code and returns it.
- `GET /:code` redirects (302) to the stored URL.
- Every redirect records a click (code, timestamp, country) so we can show per-link click counts
  in a dashboard later.

Expected traffic: a few hundred new links a day, tens of thousands of redirects a day, mostly
from links shared on social media.

Team notes: TypeScript, npm. Nobody on the team has used Cloudflare's tooling before. We have a
Cloudflare account and can log in from our laptops.
