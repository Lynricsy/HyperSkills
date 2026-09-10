# Supabase Realtime

Verified against: Supabase Realtime (platform), `@supabase/supabase-js` 2.x.

## Contents

- [Three features, one transport](#three-features-one-transport)
- [Choosing between Postgres Changes and Broadcast](#choosing-between-postgres-changes-and-broadcast)
- [Channel authorization](#channel-authorization)
- [Broadcasting from the database](#broadcasting-from-the-database)
- [Postgres Changes details](#postgres-changes-details)
- [Presence](#presence)
- [Operational notes](#operational-notes)

## Three features, one transport

A **channel** is a room identified by a topic string, and it is either public or private. All
three features ride the same WebSocket:

| Feature | Carries | Durability |
|---|---|---|
| Broadcast | arbitrary messages between clients, or from the database | fire-and-forget |
| Presence | who is currently in the channel | in-memory, per connection |
| Postgres Changes | row-level `INSERT`/`UPDATE`/`DELETE` events from the WAL | fire-and-forget |

None of them is a queue. If the receiver may be offline when the message is produced, write the
work to a durable table (or `pgmq`) and let the reader catch up; use Realtime only to wake it.

A private channel and a public channel with the same topic name are **different channels** and
messages do not cross between them.

## Choosing between Postgres Changes and Broadcast

```
Do subscribers need per-user filtering of row changes by RLS?
├─ yes, and subscriber count is modest ........ Postgres Changes
└─ no, or fan-out is large (~3000+ subscribers on the same changes)
   └─ trigger + realtime.broadcast_changes() on a private channel
```

The reason is mechanical: Postgres Changes authorizes **every event against every subscriber**. One
write to a table with 100 subscribed users runs 100 authorization checks, so throughput scales with
subscriber count rather than write rate. Changes are also processed on a single thread to preserve
order, which means a bigger compute add-on does not meaningfully raise Postgres Changes throughput.
Broadcast sends each change once and fans it out.

## Channel authorization

Private channels are authorized by RLS policies on `realtime.messages`, evaluated **when the
client joins**, using the JWT, the request headers and the topic.

```sql
create policy "members receive room broadcasts"
  on realtime.messages for select to authenticated
  using (
    realtime.messages.extension = 'broadcast'
    and exists (
      select 1 from public.rooms_users
      where user_id = (select auth.uid())
        and room_topic = (select realtime.topic())
    )
  );
```

- `realtime.topic()` returns the topic being joined; JWT claims are available through
  `current_setting('request.jwt.claims')::json`.
- `extension` records the message type (`broadcast`, `presence`), so one table carries policies for
  both features. `SELECT` governs receiving, `INSERT` governs sending.
- RLS is already enabled on `realtime.messages`; do not try to enable it.
- The `realtime` schema is locked. Creating a table or function there fails with
  `permission denied for schema realtime`, whether from SQL or the dashboard — managing policies on
  `realtime.messages` is the one permitted operation.
- Realtime runs the policy query and rolls it back; nothing is stored in `realtime.messages` by the
  authorization check itself.
- The client must opt in, or the policies are never consulted:

  ```ts
  const channel = supabase.channel('room-1', { config: { private: true } })
  channel
    .on('broadcast', { event: 'message' }, (payload) => console.log(payload))
    .subscribe((status, err) => {
      if (status !== 'SUBSCRIBED') console.error(status, err)
    })
  ```

- To make private the only option, turn off "Allow public access" in the project's Realtime
  settings. Until then a client that omits `private: true` joins a public channel of the same name
  and bypasses the policies entirely.
- Complex policies cost join latency and connection throughput, since they run per join. Keep the
  predicate indexed and shallow.
- Always inspect the `subscribe` callback status. A failed join reports through it; ignoring the
  callback turns an authorization failure into "realtime just doesn't work".

## Broadcasting from the database

`realtime.send()` writes to `realtime.messages`, and Realtime reads that table's WAL to fan the
message out. Two helpers:

- `realtime.send(payload, event, topic, private)` — arbitrary payload shape.
- `realtime.broadcast_changes(...)` — payload shaped like a Postgres Changes event, for use in a
  row trigger.

```sql
create or replace function public.broadcast_order_change()
returns trigger language plpgsql security definer as $$
begin
  perform realtime.broadcast_changes(
    'orders:' || coalesce(new.account_id, old.account_id)::text,  -- topic
    tg_op, tg_op, tg_table_name, tg_table_schema, new, old
  );
  return null;
end;
$$;

create trigger orders_broadcast
  after insert or update or delete on public.orders
  for each row execute function public.broadcast_order_change();
```

The `private` flag on `realtime.send` must match the client's channel config: a private broadcast
only reaches private channels, a public broadcast only reaches public ones. A mismatch is silent —
the insert succeeds and nobody receives anything. Note also that this flag only controls who may
*subscribe*; it does not restrict who can read `realtime.messages` from the database side.

`realtime.send` swallows its own errors so a failing broadcast cannot break the transaction that
triggered it. That is deliberate, and it means a broken topic name produces no error anywhere.

## Postgres Changes details

- Tables must be in the publication Realtime reads; add them explicitly rather than assuming.
- Use `select` on the subscription to receive only the columns you need. The default event carries
  the whole row, which matters for tables with large `jsonb`, `text` or `bytea` columns.
- **`DELETE` events are not filtered by RLS**, because Postgres cannot check access to a row that
  no longer exists. Never rely on RLS to keep the contents of a deleted row private.
- Tables outside `public` need `grant select on <schema>.<table> to authenticated` for the role in
  the access token — and then RLS, or that grant is unfettered read access.
- The `realtime` schema holds `subscription` (Postgres Changes subscribers) and `messages` (a
  daily-partitioned table used for authorization and database broadcast). Partitions older than
  three days are cleaned up automatically.

## Presence

Presence state lives in memory and is synchronised between clients; treat it as "who is connected
right now", never as durable data. A reconnect replays `sync`, so handlers must be idempotent.
Presence is authorized by the same `realtime.messages` policies, matching on
`extension = 'presence'`.

## Operational notes

- Realtime holds several Postgres connections of its own — an authorization pool, one for database
  broadcast, and (only if Postgres Changes is in use) pools for subscription management, cleanup
  and WAL pulling. Pool sizes scale with the compute add-on, and they count against the database's
  connection budget.
- At most two replication slots are used: one for database broadcast, one for Postgres Changes.
- Keep the JWT expiry window short for private channels: authorization is checked at join time, so
  a long-lived token keeps its access until the connection drops.
- Public Realtime connections are capped at 24 hours unless upgraded to user-level authentication.

<!-- sources: supabase-docs, quinto-realtime, supabase-official-skill -->
