## Review comments on relay.go (PR #812)

**@kmorris** (blocking): `time.After(idleTimeout)` inside the `for`/`select` leaks a timer on
every iteration — each one stays alive until it fires, so with 400 tenants and a 10-minute idle
timeout we pile up timers for every message. Must be one `time.NewTimer` with `Stop`/`Reset`.

**@kmorris** (blocking): the heartbeat ticker is never stopped, which leaks the ticker forever
once `Run` returns. Add `defer heartbeat.Stop()`.

**@author**: we reconnect tenants a lot, so `Run` returns and restarts often. Are these real
leaks or not? I'd rather not touch it if it's fine.
