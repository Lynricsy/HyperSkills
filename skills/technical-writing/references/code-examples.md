# Code examples that run

## Contents

- [The bar](#the-bar)
- [Declare the missing prerequisite or fix the block](#declare-the-missing-prerequisite-or-fix-the-block)
- [Never use an ellipsis for omitted code](#never-use-an-ellipsis-for-omitted-code)
- [Placeholders and sample credentials](#placeholders-and-sample-credentials)
- [Minimal means minimal](#minimal-means-minimal)
- [Showing output](#showing-output)
- [Introducing a block](#introducing-a-block)
- [Formatting](#formatting)
- [Language variants](#language-variants)
- [Checking a page's examples](#checking-a-pages-examples)

## The bar

Every code block is either pasteable and runnable as written, given the
prerequisites the page has already declared, or it explicitly states what is
missing. There is no third state. A block that is neither is a block the reader
will run, and its failure will read as a defect in the product.

"Given the prerequisites the page has declared" is the whole subtlety. A block
that needs an optional dependency, a running service, a credential or a prior
block's variables is fine — as long as the page said so **before** the block,
in a form the reader can act on.

## Declare the missing prerequisite or fix the block

Work through each block and name what it needs that the page has not supplied:

| What the block needs | What the page must have before it |
|---|---|
| An import from an optional extra | the install line including the extra |
| A credential read from the environment | the exact variable name the code reads |
| A service on a port | the command that starts it, and a check it is up |
| A variable defined earlier | either the earlier block, or a repeat of the definition |
| A file on disk | the command or content that creates it |
| A specific version | the version constraint, stated |

The failure this prevents looks like a product bug and is a documentation bug:
an install line that omits the extra, followed twenty lines later by the import
that needs it. The reader gets `ImportError` with no reason to connect it to
step 1.

Blocks that need something unobtainable — a private endpoint, a paid tier, a
cluster — say so in one line above the block. That line is not a failure of the
page; omitting it is.

## Never use an ellipsis for omitted code

Mark omissions with a comment in the language of the sample, never `...` or `…`.
[official]

```python
r = client.request("GET", "/ping")
# handle the response
```

```yaml
spec:
  template:
    # several lines of pod spec omitted
    spec:
      containers:
        - image: IMAGE_URL
```

Three reasons, in order of how often they bite:

1. `...` is valid syntax in some languages and meaningful in others — a legal
   expression in Python, a document separator in YAML — so the paste fails, or
   worse succeeds, with an error that has nothing to do with the omission.
2. A comment says what was omitted; an ellipsis says only that something was.
3. It is the only marker a reader can distinguish from real code at a glance.

A block containing an omission should not be presented as one-click copyable; if
the renderer offers a copy button, the block should be complete.

## Placeholders and sample credentials

- Use the provider's documented test prefix where one exists (`sk_test_…`), or
  an obvious placeholder the page explains (`YOUR_API_KEY`,
  `<project-id>`). Keep one convention per page.
- Never write a sample that pattern-matches a live credential. It gets pasted
  into real code, and it trips secret scanners — including forge push
  protection, which blocks the push of the file containing it. [community]
- Use the reserved example domains and names for hosts, emails and people:
  `example.com`, `example.org`. A real-looking third-party host in a sample
  eventually receives traffic.
- When a placeholder must be substituted, say so next to it, once. A page that
  tells the reader to expect output from `https://api.example.com` has turned a
  placeholder into a broken promise.

## Minimal means minimal

An example demonstrates exactly one thing. Everything else in the block is
noise the reader has to decide whether to keep:

- No error handling that is not the point of the example, and none that
  silently swallows the error the example would otherwise show.
- No logging setup, no argument parsing, no framework scaffolding, unless they
  are the subject.
- No unused imports, no unused parameters, no configuration set to its default.
- No abbreviations invented for the example (`c = Client(...)`); the reader will
  copy the name.

The exception is the prerequisite kind of noise: an example that omits the
authentication it in fact needs is not minimal, it is broken.

## Showing output

Show the output whenever the reader needs it to know whether their run
succeeded. Keep it in a separate block from the input, so the copy button does
not hand them the output as code:

```
$ python limits.py
waited 0.00s  status 200
waited 0.19s  status 200
```

Quote what the command actually printed. Reconstructed output is the most
plausible-looking wrong thing on a documentation page: it is the part nobody
double-checks, and a reader whose real output differs cannot tell whether they
broke something.

Truncate long output with the same discipline as code — a comment or a bracketed
note, never a bare ellipsis.

## Introducing a block

Precede each block with a sentence saying what it shows. Use a colon when the
block follows immediately, a full stop when anything intervenes: [official]

- Recommended: "The following sample shows how to use `request`:" then the
  block.
- Recommended: "The following sample shows how to use `request`. For other
  methods, see the reference." then the block.
- Not recommended: "…see the reference:" then the block — the colon now points
  at the wrong thing.

Refer to code elements with a qualifying noun: *the `example.yaml` file*, *the
`timeout` parameter*, not `example.yaml` standing alone. It reads better and
survives translation. [official]

## Formatting

- Fence every block and tag the language, so highlighting and tooling work.
- Follow the project's own formatter for the language; where there is none, use
  spaces, two per level for most languages.
- Wrap at about 80 characters. Readers in a narrow pane, a side-by-side diff or
  a printed page lose the right-hand side of anything longer.
- Show a command as the reader types it, one command per line, with the prompt
  only when you also show output.
- Do not put a comment on a line that is already at the wrap limit; put it
  above.

## Language variants

Show the same example in another language only where the product genuinely ships
several SDKs and the page is reference or how-to. Every extra variant is another
copy to keep correct, and a stale variant in a language you do not use is the
one that goes unnoticed for a year. A tutorial picks one language and says so.

## Checking a page's examples

- [ ] A clean environment was created from the page's own declared
      prerequisites.
- [ ] Every block was pasted in order and run; failures were fixed in the page,
      not in the environment.
- [ ] Every symbol, keyword argument, method name, field and exception name
      exists in the current source with that spelling.
- [ ] Every default and accepted value shown matches the source.
- [ ] Every environment variable shown is the one the code reads.
- [ ] Output blocks are captured, not written from memory.
- [ ] No bare ellipsis anywhere in any block.
- [ ] No credential that could be mistaken for a live one.
- [ ] Where the environment could not be created, the delivery says which
      blocks were not run.

<!-- sources: google-devdocs-style, mblode-docs-writing, diataxis -->
