# Security and access control

Verified against: Redis 8.10.1.

## Contents

- [What the stock instance gives an attacker](#what-the-stock-instance-gives-an-attacker)
- [ACL users](#acl-users)
- [Command categories](#command-categories)
- [Key and channel patterns](#key-and-channel-patterns)
- [Selectors](#selectors)
- [Why rename-command is the fallback](#why-rename-command-is-the-fallback)
- [TLS](#tls)
- [Network exposure](#network-exposure)
- [Scripts, injection and untrusted input](#scripts-injection-and-untrusted-input)
- [Secrets and credential rotation](#secrets-and-credential-rotation)
- [Audit checklist](#audit-checklist)

## What the stock instance gives an attacker

`ACL GETUSER default` on an unconfigured instance `[verified]`:

```
flags: on, nopass, sanitize-payload
commands: +@all
keys: ~*
channels: &*
```

No password, every command, every key, every channel. `protected-mode yes` is the only thing
standing between that and the network, and it stops applying the moment `bind` names a
non-loopback interface or a password is set. Every "Redis exposed to the internet" incident is
this configuration plus one firewall mistake.

Three layers, all of them required — any one alone leaves a hole:

1. Authentication, with a distinct identity per client.
2. Authorisation, scoped to the keys and commands that client needs.
3. Network isolation, so an unauthenticated peer cannot reach the port at all.

## ACL users

`requirepass` is the legacy shortcut that sets a password on `default`. Prefer a real user per
application, because that is what makes the blast radius of a leaked credential bounded and
makes `SLOWLOG`/`CLIENT LIST` attributable.

```
ACL SETUSER cache-reader on >{{password}} ~cache:* +@read +scan
ACL SETUSER cache-writer on >{{password}} ~cache:* +@read +@write -@dangerous
ACL SETUSER worker      on >{{password}} ~queue:* ~job:* +@read +@write +@stream
ACL SETUSER default      off
ACL SAVE                                   # persists to aclfile if one is configured
```

- `on`/`off` enables the user; disabling `default` is the single highest-value change on a
  shared instance.
- Rules are applied in order and are additive/subtractive, so `+@all -@dangerous` and
  `-@all +@read` express very different intents. Read the result back with
  `ACL GETUSER <name>` rather than trusting the rule string.
- `ACL LIST` shows every user's effective rules; `ACL WHOAMI` shows who the current connection
  is; `ACL CAT` lists the categories (30 on 8.10.1 `[verified]`).
- `ACL LOG` records denied commands with the reason (`command`, `key`, `channel`, `auth`) and
  the user — the first place to look when an application starts failing after a tightening, and
  a genuine intrusion signal on its own.
- Store users in an `aclfile` rather than in `redis.conf` so they can be reloaded
  (`ACL LOAD`) without a restart, and so the config file is not where passwords live.

## Command categories

Subtract capability by category; enumerating individual commands goes stale with every release.

| Category | Contains | Typical decision |
|---|---|---|
| `@read` | `GET`, `MGET`, `HGET`, `SISMEMBER`, `ZRANGE`, … | Grant to any reader |
| `@write` | `SET`, `DEL`, `HSET`, `XADD`, … | Grant to writers only |
| `@keyspace` | `KEYS`, `SCAN`, `DBSIZE`, `EXPIRE`, `TYPE`, … | Grant `+scan` explicitly rather than the whole category |
| `@dangerous` | `FLUSHALL`, `FLUSHDB`, `KEYS`, `DEBUG`, `SHUTDOWN`, `CLIENT`, `CONFIG`, `MONITOR`, … | `-@dangerous` on every application user |
| `@admin` | `CONFIG`, `SHUTDOWN`, `REPLICAOF`, `ACL`, `CLUSTER`, … | Operators only, never an application |
| `@scripting` | `EVAL`, `EVALSHA`, `FCALL`, `FUNCTION`, … | Grant only where the app actually runs scripts; a script can reach any key the user can |
| `@pubsub` | `SUBSCRIBE`, `PUBLISH`, `PSUBSCRIBE`, … | Pair with a `&channel:*` pattern |
| `@blocking` | `BLPOP`, `BRPOP`, `XREAD BLOCK`, `WAIT`, … | Queue consumers only |
| `@slow` | Everything with non-constant complexity | Useful as a review lens, too broad to deny outright |

`COMMAND INFO keys` reports `@keyspace @read @slow @dangerous` `[verified]`, which is why
`-@dangerous` on an application user removes `KEYS` without any command renaming. `ACL CAT
<category>` lists a category's members on the running server — the authoritative answer for
that version.

One important consequence: `@scripting` bypasses nothing, but a script runs with the calling
user's permissions, so granting `EVAL` to a user with `~*` grants everything `EVAL` can reach.
Prefer `FUNCTION LOAD` by an operator plus `+fcall` on the named function for the application.

## Key and channel patterns

- `~cache:*` grants access to keys with that prefix; several patterns can be listed. `%R~` and
  `%W~` (7.0+) grant read-only or write-only access to a pattern, which is how a reader is
  prevented from overwriting what it reads.
- `allkeys` / `~*` is the default for `default` and should appear on no other user.
- `&channel:*` does the same for Pub/Sub channels; `resetchannels` clears them. Without a
  channel pattern a user with `@pubsub` can publish anywhere, including to keyspace
  notification channels.
- Patterns are glob-style on the whole key name, which is the concrete reason key naming is a
  security decision: a keyspace without stable prefixes cannot be partitioned by ACL. On a
  multi-tenant instance the tenant segment has to come first for `~tenant:42:*` to mean
  anything.

## Selectors

A selector (7.0+) attaches an extra permission set to a user, so one identity can have
different rights on different key spaces:

```
ACL SETUSER svc on >{{password}} ~app:* +@read +@write (~audit:* +@read)
```

The parenthesised selector grants read-only access to `audit:*` without widening the base
rules. Use it instead of creating a second user when the same process legitimately needs two
scopes; the `ACL LOG` entries stay attributable to one identity.

## Why rename-command is the fallback

`rename-command FLUSHALL ""` in the config still works, but it is the worse tool:

- It changes the wire protocol for everyone, so client libraries, cluster tooling,
  `redis-cli --cluster`, monitoring agents and Sentinel break in ways that look like bugs
  rather than policy.
- It is instance-wide: an operator cannot keep the command while denying it to the application.
- It is invisible to `ACL LOG`, so an attempt leaves no audit trail.
- It cannot be changed without a restart, and it is not replicated, so a replica and its
  primary can disagree.

Use ACL categories first. Keep `rename-command` for a server too old for ACLs (pre-6.0) or for
a command that has no category granularity you need.

## TLS

- Redis does not encrypt by default. `tls-port 6380` plus `tls-cert-file`, `tls-key-file` and
  `tls-ca-cert-file` enables it; setting `port 0` alongside disables the plaintext port, which
  is the part people forget.
- `tls-auth-clients yes` requires client certificates — mutual TLS, and the only way to
  authenticate a peer rather than a secret.
- Replication and cluster bus traffic need `tls-replication yes` and `tls-cluster yes`
  separately; enabling TLS for clients leaves the replication stream in clear text otherwise.
- Clients must verify: a client configured with certificate verification disabled has
  encryption without authentication, which does not defend against a man in the middle.
- TLS costs CPU on the same thread that runs commands. Measure before and after on a
  latency-sensitive instance.

## Network exposure

```
bind 127.0.0.1 10.0.3.14        # explicit interfaces, never 0.0.0.0
protected-mode yes
port 0                          # when tls-port is in use
```

- `bind 0.0.0.0` with `protected-mode no` is the configuration behind every public-Redis
  incident. `protected-mode` refuses connections from non-loopback addresses only while there
  is no password and no explicit `bind` — it is a guard rail for a default install, not a
  security control.
- Put the instance on a private network or a security group that allows only the application
  subnet. Redis has no per-command rate limiting and no connection-level anomaly detection;
  the network is the outer boundary.
- The cluster bus listens on `port + 10000` and must be reachable between nodes and nowhere
  else. A firewall rule that opens only 6379 breaks the cluster; one that opens both to the
  world exposes it twice.
- `CONFIG SET` is itself an attack surface: an authenticated client with `@admin` can change
  `dir` and `dbfilename` and write a file anywhere Redis can write. This is the mechanism
  behind Redis-to-shell exploits, and the reason `@admin` never belongs on an application user.
- `MONITOR` streams every command, including every value. It is in `@dangerous` and `@admin`
  for that reason; treat access to it as access to the data.

## Scripts, injection and untrusted input

- Values are opaque to Redis, so there is no SQL-injection equivalent for `GET`/`SET`. The
  injection surface is **key names** and **script arguments**.
- Never build a key name from unvalidated user input. A user-controlled key name escapes the
  prefix an ACL pattern relies on — `cache:` plus an input of `../` is harmless, but an input
  containing the delimiter merges two namespaces, and an input allowed to be `*` turns a
  pattern-based delete into a wider one.
- Pass data to scripts through `ARGV`, never by string-concatenating it into the script body.
  A concatenated script is a new SHA on every call (destroying the script cache) and lets input
  become Lua.
- Declare every key a script touches in `KEYS`. Beyond Cluster correctness, it is what lets the
  ACL check the keys before the script runs.
- Keep `@scripting` off users that do not need it, and prefer a named function with `+fcall`
  over open `EVAL`.

## Secrets and credential rotation

- ACL passwords are stored as SHA-256 hashes; `>password` sets from plaintext, `#<hash>` sets
  from a hash, so a deployment pipeline never needs the plaintext on the server host.
- A user can hold several passwords at once, which is what makes rotation possible without
  downtime: add the new one, roll the clients, remove the old one.
- Never put a credential in a key name, in a `CLIENT SETNAME`, or on a `redis-cli` command
  line — all three end up in `SLOWLOG`, `CLIENT LIST`, `MONITOR` output and shell history.
  `redis-cli` reads `REDISCLI_AUTH` from the environment for this reason.
- `CONFIG GET requirepass` returns the password to anyone with `@admin`, which is another
  reason to use `aclfile` and drop `requirepass`.

## Audit checklist

- [ ] `ACL GETUSER default` — is it `off`, or at least without `nopass` and without `~*`?
- [ ] `ACL LIST` — does every user's key pattern match what that service actually touches?
- [ ] Does any application user hold `@admin`, `@dangerous`, `CONFIG`, `DEBUG` or `MONITOR`?
- [ ] `CONFIG GET bind protected-mode port tls-port` — is the plaintext port off where TLS is
      required, and is `bind` explicit?
- [ ] Is `tls-replication` / `tls-cluster` on where client TLS is on?
- [ ] Is the port reachable only from the application subnet, and is the cluster bus port
      (`port + 10000`) restricted to the nodes?
- [ ] `ACL LOG` — any denials that indicate probing rather than a misconfigured client?
- [ ] Are keys built from user input anywhere, and is the prefix an ACL depends on derivable
      from that input?
- [ ] Is `aclfile` in use, so users can be rotated and reloaded without a restart?
- [ ] Does every service call `CLIENT SETNAME`, so denials and slow commands are attributable?

<!-- sources: redis-agent-skills, redis-io-docs, redis-oss -->
