# Team notes

- ProjectDO logs `ms: 0` for every `listTasks` call in production, and the Workers Traces spans
  for the SQL call also show 0 ms. So the Durable Object is fast; the problem must be D1.
- Plan so far: loop over all 38 databases with `wrangler d1 execute <db> --remote --command "..."`
  and eyeball table sizes.
