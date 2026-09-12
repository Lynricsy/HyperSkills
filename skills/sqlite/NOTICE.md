# NOTICE — sqlite

This skill is a curated rewrite by HyperSkills (MIT). It adapts material from:

- TerminalSkills/skills (Apache-2.0) — https://github.com/TerminalSkills/skills @ 56037efc04d0ffd20a0a85b18894115df74bd70f — paths: skills/sqlite/SKILL.md, LICENSE — Connection release and online-backup entry points, rewritten in SKILL.md and references/connections-and-transactions.md and references/wal-backup-and-recovery.md; introductory CRUD and fixed tuning values omitted.
- SimHacker/moollm (MIT) — https://github.com/SimHacker/moollm @ 541bf236194bddca05a12008505df0931c86ee85 — paths: skills/sqlite/SKILL.md, LICENSE — Embedded-engine boundaries, affinity and durability cautions, rewritten in SKILL.md and references/types-and-migrations.md and references/wal-backup-and-recovery.md; MOOLLM integrations removed.
- RightNow-AI/openfang (Apache-2.0) — https://github.com/RightNow-AI/openfang @ acf2587e46be174c10200489c9a2d23a39a98aeb — paths: crates/openfang-skills/bundled/sqlite-expert/SKILL.md, LICENSE-APACHE — Short explicit transactions, single-writer limits and covering-index observation, rewritten in SKILL.md and references/connections-and-transactions.md and references/query-plans-and-indexes.md; fixed cache and BLOB thresholds rejected.
- harness-studio/harness-studio (MIT) — https://github.com/harness-studio/harness-studio @ caa0c9b8a36ac6397ac70a8e551410790106d626 — paths: skills/sqlite-concurrency/SKILL.md, LICENSE — Atomic SQL and early write-ownership intent, rewritten in references/connections-and-transactions.md; erroneous aiosqlite thread claims and process-local bootstrap guarantees rejected.

Reference-only sources (no content copied):

- https://www.sqlite.org/lang_transaction.html (NONE) — https://www.sqlite.org/lang_transaction.html
- https://www.sqlite.org/isolation.html (NONE) — https://www.sqlite.org/isolation.html
- https://www.sqlite.org/pragma.html (NONE) — https://www.sqlite.org/pragma.html
- https://www.sqlite.org/c3ref/busy_handler.html (NONE) — https://www.sqlite.org/c3ref/busy_handler.html
- https://www.sqlite.org/wal.html (NONE) — https://www.sqlite.org/wal.html
- https://www.sqlite.org/backup.html (NONE) — https://www.sqlite.org/backup.html
- https://www.sqlite.org/lang_vacuum.html (NONE) — https://www.sqlite.org/lang_vacuum.html
- https://www.sqlite.org/datatype3.html (NONE) — https://www.sqlite.org/datatype3.html
- https://www.sqlite.org/stricttables.html (NONE) — https://www.sqlite.org/stricttables.html
- https://www.sqlite.org/foreignkeys.html (NONE) — https://www.sqlite.org/foreignkeys.html
- https://www.sqlite.org/lang_createtable.html (NONE) — https://www.sqlite.org/lang_createtable.html
- https://www.sqlite.org/lang_altertable.html (NONE) — https://www.sqlite.org/lang_altertable.html
- https://www.sqlite.org/autoinc.html (NONE) — https://www.sqlite.org/autoinc.html
- https://www.sqlite.org/eqp.html (NONE) — https://www.sqlite.org/eqp.html
- https://www.sqlite.org/optoverview.html (NONE) — https://www.sqlite.org/optoverview.html
- https://www.sqlite.org/expridx.html (NONE) — https://www.sqlite.org/expridx.html
- https://www.sqlite.org/partialindex.html (NONE) — https://www.sqlite.org/partialindex.html
- https://www.sqlite.org/lang_analyze.html (NONE) — https://www.sqlite.org/lang_analyze.html
