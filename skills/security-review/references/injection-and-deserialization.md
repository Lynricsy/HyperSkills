# Injection and untrusted deserialization

Verified against: OWASP Top 10 2025

## Contents

- [The shape of every injection bug](#the-shape-of-every-injection-bug)
- [SQL, including the positions you cannot parameterize](#sql-including-the-positions-you-cannot-parameterize)
- [Mass assignment as column injection](#mass-assignment-as-column-injection)
- [NoSQL](#nosql)
- [OS command](#os-command)
- [Template injection](#template-injection)
- [Deserialization](#deserialization)
- [Path traversal and file handling](#path-traversal-and-file-handling)
- [Output-context injection](#output-context-injection)
- [Log injection](#log-injection)
- [Second-order injection](#second-order-injection)
- [What not to report](#what-not-to-report)

## The shape of every injection bug

Untrusted data is concatenated into a string that a second interpreter parses. The fix is
always the same idea and never "escaping": send the data out of band, so the interpreter never
sees it as syntax. Escaping is the fallback for the positions where out-of-band is impossible,
and those positions need an allowlist instead.

Injection is A05:2025 — it moved down from A03:2021, and A03 is now Software Supply Chain
Failures. `[official]`

## SQL, including the positions you cannot parameterize

Parameter binding covers values. It does not cover identifiers, so these positions require an
allowlist and are where injection survives in codebases that "use prepared statements":

- `ORDER BY <column>` and `<direction>`
- Table and column names, schema names
- `LIMIT` / `OFFSET` in some drivers
- Whole predicate fragments assembled for a dynamic filter
- `IN (...)` lists built by string join rather than by generating placeholders

```js
// Injectable. No bind parameter can fix this position.
"... ORDER BY " + req.query.sort + " DESC"
```

```js
// Fixed by mapping the input to a value the code chose, never to the input itself.
const SORTS = { created_at: "created_at", total: "total_cents" };
const column = SORTS[req.query.sort] ?? "created_at";
`... ORDER BY ${column} DESC`
```

The map is over literals the code owns. Validating the string and then interpolating the
validated string is weaker — it survives one refactor of the validator.

Also check:

- ORM escape hatches: `.raw()`, `.extra()`, `RawSQL()`, `queryRaw`, `createQueryBuilder().where()`
  with an interpolated string, `@Query` with concatenation.
- Migrations and admin scripts. They run with higher privileges and get reviewed least.
- Stored procedures built with dynamic SQL inside; parameterizing the call does not parameterize
  the body.
- The database user's privileges. Injection through an account with DDL rights or `COPY` /
  `LOAD_FILE` access escalates from data read to file read or code execution.

## Mass assignment as column injection

```js
// Field names come from the request body and become SQL identifiers.
const assignments = Object.keys(req.body).map((f, i) => `${f} = $${i + 2}`).join(", ");
await pool.query(`UPDATE orders SET ${assignments} WHERE id = $1`, [id, ...values]);
```

Two bugs in one. The values are bound, so the values are safe; the **keys** are interpolated
identifiers, so this is injection. And even with the identifiers fixed, the caller chooses
which columns to write, which means `status`, `total_cents`, `customer_id`, `role` and
`is_admin` are all writable from a route that looks like it edits a note.

The fix is an explicit allowlist of updatable fields, mapped to columns the code names. Frameworks
with "strong parameters" or DTO validation give this for free; check that the route actually uses
it rather than spreading the body.

## NoSQL

- Operator injection: a JSON body where a string was expected lets `{"$ne": null}` or
  `{"$gt": ""}` through a query builder, turning an equality check into "any". Validate types,
  not just presence — a login handler that accepts an object for the password field is an
  authentication bypass.
- `$where`, `mapReduce` and aggregation `$function` evaluate JavaScript server-side.
- Aggregation pipelines assembled from request fragments are the same problem as dynamic SQL.

## OS command

```python
subprocess.run(f"aws s3 cp /tmp/{report_id}.csv {dest}", shell=True, check=True)
```

`shell=True` with any interpolated value is command injection. The fix is an argument list with
no shell:

```python
subprocess.run(["aws", "s3", "cp", f"/tmp/{report_id}.csv", dest], check=True)
```

The argument-list form still needs validation of `report_id` for path traversal, and it does not
save you if the program itself takes a shell-like argument. Watch for:

- Node `child_process.exec` / `execSync` (shell) versus `execFile` / `spawn` (no shell).
- Arguments that begin with `-`: an attacker-controlled value in an argument position can become
  a flag. `--` before positional arguments, where the program supports it.
- Wrappers: `sh -c`, `bash -lc`, `ssh host <cmd>`, `git -c`, `find -exec`, `xargs`, `make`,
  anything that re-parses its argument.
- Environment variables that change a program's behaviour: `LD_PRELOAD`, `GIT_SSH_COMMAND`,
  `PYTHONPATH`, `NODE_OPTIONS`.

## Template injection

Rendering a template **string** that came from a request is code execution in most engines,
which is a different bug from rendering untrusted *data* through a fixed template.

```python
# The template itself is caller-supplied.
spec.get("template", "{rows}").format(rows=rows)
```

Even Python's `str.format` is dangerous with a caller-supplied format string: `{x.__class__}`
and `{0.__globals__}` reach attributes and globals of the arguments. Jinja, Handlebars, ERB,
Freemarker, Velocity and Thymeleaf all have documented paths from template control to code
execution. The fix is that templates are code: they come from the repository, and the caller
supplies only values.

Nearby: format-string sinks in logging (`logger.info(user_input)` where the logger treats the
first argument as a format string), and `eval`-adjacent helpers — `eval`, `exec`, `new Function`,
`vm.runInNewContext`, `setTimeout` with a string, `JSON.parse` reviver abuse in old code.

## Deserialization

Formats that reconstruct arbitrary objects execute code during decoding. Reaching one of these
with caller-controlled bytes is remote code execution, not an information leak:

| Language | Dangerous | Use instead |
|---|---|---|
| Python | `pickle.loads`, `yaml.load` without `SafeLoader`, `dill`, `jsonpickle`, `shelve`, `marshal` | `json`, `yaml.safe_load`, an explicit schema |
| Node | `node-serialize`, `serialize-javascript` with `eval`, `funcster` | `JSON.parse` with schema validation |
| Java | `ObjectInputStream.readObject`, XMLDecoder, XStream with default converters | JSON or protobuf with an allowlist |
| PHP | `unserialize` on user data (POP chains; `phar://` triggers it implicitly) | `json_decode` |
| Ruby | `Marshal.load`, `YAML.load` (pre-Psych-4 semantics) | `JSON.parse`, `YAML.safe_load` |
| .NET | `BinaryFormatter`, `NetDataContractSerializer`, `LosFormatter` | `System.Text.Json` |

```python
# Any caller can hand back a "cursor". pickle reconstructs whatever it says.
state = pickle.loads(base64.b64decode(body["cursor"]))
```

Signing the blob is not a fix, it is a mitigation that moves the problem to key management: the
signature stops forgery but any leak of the key, or any other path into the same decoder,
restores code execution. The fix is a format that cannot construct objects — JSON with an
explicit schema, or a server-side cursor keyed by an opaque id.

The two questions that settle severity: can the caller reach the decode without
authentication, and what identity does the process hold? A deserialization sink in a service
holding broad cloud credentials is worse than the same sink in a sandboxed worker.

## Path traversal and file handling

- Joining a caller-supplied name onto a base directory is traversal unless the result is
  normalized and then checked to still be inside the base. Check after normalization, because
  `..%2f`, `..\\`, unicode variants and symlinks all survive a pre-normalization check.
- Absolute paths defeat a join in most languages: `os.path.join("/base", "/etc/passwd")`
  returns `/etc/passwd`.
- Upload handling: the client-supplied filename, the client-supplied content type and the
  extension are all untrusted. Decide the stored name yourself.
- Archive extraction: entries with `..` or absolute paths (zip slip), symlink entries, and
  decompression ratios that exhaust disk.
- XML parsers: external entity resolution off, DTD processing off. XXE reads local files and
  reaches internal URLs, which makes it an SSRF primitive as well.

## Output-context injection

The interpreter is the browser, and the fix depends on where the value lands: HTML text, an
attribute, a URL, a `<script>` body, CSS. Framework auto-escaping covers HTML text and
attributes and does not cover the others.

The findings worth reporting are the explicit opt-outs with untrusted input:
`dangerouslySetInnerHTML`, `v-html`, `{{{ }}}`, `mark_safe`, `|safe`, `{% autoescape off %}`,
`innerHTML`/`outerHTML`/`insertAdjacentHTML`, `document.write`, `Element.setAttribute` on
`href`/`src`/`on*`, `javascript:` URLs reached from a caller-supplied string, and
`sanitize`-named helpers that only strip `<script>`.

A Content-Security-Policy is defence in depth. Report a missing CSP as Low on its own and as
severity-raising context next to a demonstrated injection.

## Log injection

Unescaped newlines in a logged value forge log entries, which matters when the logs drive
alerting or are parsed downstream. Usually Low. It becomes higher when the log sink executes
anything — a log-to-shell pipeline, a spreadsheet export where a leading `=` is a formula
(CSV injection), or a log viewer that renders HTML.

## Second-order injection

The value is stored safely and then used unsafely later. The store is not the boundary; the
sink is. Two common shapes: a field written through an ORM and later read into a raw query for
a report, and a value validated at the API edge but re-read from the database by a worker that
assumes everything in the table is clean.

When auditing, treat "data from our own database" as untrusted whenever any of that data
originated from a user — which is nearly always.

## What not to report

- A parameterized query, an ORM filter, or an f-string whose interpolated values are all
  constants or configuration.
- `shell=True` with a fully literal command.
- A deserialization call on a file the operator placed on disk, or on a blob the service itself
  wrote and the caller cannot influence. Say that you checked.
- Framework auto-escaping working as documented.
- `md5` or `sha1` used for a cache key, an ETag or a content checksum — not every weak hash is
  a cryptographic failure. When it protects a password or a signature, it is.

Each of these becomes a finding the moment a caller-controlled value reaches it, so the
distinguishing work is the data-flow trace, not the pattern match.

<!-- sources: openai-secbase, sentry-secreview, owasp-top10, tob-insecure-defaults, trilwu-audit -->
