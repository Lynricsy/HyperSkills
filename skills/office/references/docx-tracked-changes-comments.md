# Tracked changes and comments in Word documents

Verified against: WordprocessingML (ECMA-376), pandoc 3.10, LibreOffice 26.2

## Contents

- [When redlining is the requirement](#when-redlining-is-the-requirement)
- [Insertions](#insertions)
- [Deletions](#deletions)
- [Deleting a whole paragraph](#deleting-a-whole-paragraph)
- [Formatting changes](#formatting-changes)
- [Splitting a run to edit part of a sentence](#splitting-a-run-to-edit-part-of-a-sentence)
- [Verifying revisions](#verifying-revisions)
- [Comments: the six parts](#comments-the-six-parts)
- [Reading a document that already has revisions](#reading-a-document-that-already-has-revisions)

## When redlining is the requirement

"Show me what changed" and "make the change" are different deliverables. A
reviewer who needs to accept or reject each edit in Word needs revision markup
inside `word/document.xml`; a clean rewrite is useless to them. Regenerating the
document from scratch cannot produce revisions, so this work always goes through
the unpack, edit, repack path.

Every revision element carries the same three attributes:

| Attribute | Meaning |
|---|---|
| `w:id` | Unique integer per revision within the document |
| `w:author` | Shown in the review pane; use one consistent author name |
| `w:date` | ISO 8601 with `Z`, for example `2026-09-10T00:00:00Z` |

Duplicate `w:id` values are the most common self-inflicted wound: Word groups
revisions by id, so two unrelated edits sharing an id accept and reject
together. Allocate ids from one counter above the highest id already present.

## Insertions

Wrap the new runs in `<w:ins>`. The runs themselves are ordinary — inserted text
still lives in `<w:t>`.

```xml
<w:ins w:id="102" w:author="Reviewer" w:date="2026-09-10T00:00:00Z">
  <w:r><w:t>30</w:t></w:r>
</w:ins>
```

## Deletions

Wrap the removed runs in `<w:del>` **and** change every `<w:t>` inside them to
`<w:delText>`. This is the step people miss. A `<w:del>` containing `<w:t>` is
contradictory: consumers treat the text as still present, so rejecting the
revision leaves the text there twice and accepting it leaves it there once.

```xml
<w:del w:id="101" w:author="Reviewer" w:date="2026-09-10T00:00:00Z">
  <w:r><w:delText>60</w:delText></w:r>
</w:del>
```

`xml:space="preserve"` matters on `<w:delText>` exactly as it does on `<w:t>`:
without it, leading and trailing spaces are dropped and the reject text loses
its word spacing.

## Deleting a whole paragraph

A paragraph is two things: its content and its paragraph mark. Marking only the
runs deleted leaves an empty paragraph behind after the change is accepted. Mark
the paragraph mark too, by putting a `<w:del>` inside the paragraph mark's run
properties:

```xml
<w:p>
  <w:pPr>
    <w:rPr>
      <w:del w:id="103" w:author="Reviewer" w:date="2026-09-10T00:00:00Z"/>
    </w:rPr>
  </w:pPr>
  <w:del w:id="104" w:author="Reviewer" w:date="2026-09-10T00:00:00Z">
    <w:r><w:delText>Either party may terminate with 30 days written notice.</w:delText></w:r>
  </w:del>
</w:p>
```

The mirror image applies to inserting a paragraph: put `<w:ins>` in the new
paragraph's `w:pPr/w:rPr` so that rejecting the change removes the paragraph
mark as well as the text.

Table rows follow the same pattern with `<w:trPr><w:ins/></w:trPr>` and
`<w:trPr><w:del/></w:trPr>`.

## Formatting changes

Changing only formatting is `<w:rPrChange>` inside the run properties, holding
the *previous* properties:

```xml
<w:r>
  <w:rPr>
    <w:b/>
    <w:rPrChange w:id="105" w:author="Reviewer" w:date="2026-09-10T00:00:00Z">
      <w:rPr/>
    </w:rPrChange>
  </w:rPr>
  <w:t>net 30</w:t>
</w:r>
```

The paragraph-level equivalent is `<w:pPrChange>`, and it also stores the old
properties, not the new ones.

## Splitting a run to edit part of a sentence

Word fragments text across runs for reasons that have nothing to do with
meaning — a spell-check boundary, a proofing language change, an earlier edit.
A visible phrase is therefore not necessarily one `<w:r>`, and string-replacing
across a run boundary silently fails to match.

Split the containing run into three before marking anything: unchanged prefix,
the part being changed, unchanged suffix. Then wrap only the middle. Keep run
properties identical across the three parts or the surviving text changes
appearance.

```xml
<!-- before -->
<w:r><w:t xml:space="preserve">Payment terms are net 60 from receipt.</w:t></w:r>

<!-- after -->
<w:r><w:t xml:space="preserve">Payment terms are net </w:t></w:r>
<w:del w:id="101" w:author="Reviewer" w:date="2026-09-10T00:00:00Z">
  <w:r><w:delText>60</w:delText></w:r>
</w:del>
<w:ins w:id="102" w:author="Reviewer" w:date="2026-09-10T00:00:00Z">
  <w:r><w:t>30</w:t></w:r>
</w:ins>
<w:r><w:t xml:space="preserve"> from receipt.</w:t></w:r>
```

## Verifying revisions

A rendered page is the wrong gate for redlining: LibreOffice draws both the
deleted and the inserted text, so the preview reads `net 6030` and looks broken
when the markup is in fact correct. `[verified]`

Check the two resolved versions instead — they are the only thing the reviewer
will ever see:

```bash
pandoc --track-changes=reject -f docx -t plain edited.docx   # must read "net 60"
pandoc --track-changes=accept -f docx -t plain edited.docx   # must read "net 30"
pandoc --track-changes=all    -f docx -t markdown edited.docx  # lists author and date
```

If reject does not reproduce the original text, the deletion markup is wrong. If
accept still shows the old text, the runs were not converted to `<w:delText>`.
`[verified]`

## Comments: the six parts

A comment is not a single element. Adding one to a document that has never had
comments means adding parts, relationships and content types together, and every
piece has to line up on the same `w:id`:

| Part | Purpose |
|---|---|
| `word/comments.xml` | The comment text (`<w:comment w:id=… w:author=… w:date=…>`) |
| `word/commentsExtended.xml` | Threading and resolved state, keyed by paragraph id |
| `word/commentsIds.xml` | Durable ids that survive round trips |
| `word/commentsExtensible.xml` | Newer metadata such as presence |
| `word/people.xml` | Author identities referenced by the threads |
| `word/document.xml` | The anchor: range start, range end, reference |

In the document body, a comment spans a range:

```xml
<w:commentRangeStart w:id="1"/>
<w:r><w:t>net 30</w:t></w:r>
<w:commentRangeEnd w:id="1"/>
<w:r>
  <w:rPr><w:rStyle w:val="CommentReference"/></w:rPr>
  <w:commentReference w:id="1"/>
</w:r>
```

Checklist for a first comment:

- Add each new part to `[Content_Types].xml` with its own override.
- Add a relationship for each new part in `word/_rels/document.xml.rels`.
- Keep `w:id` consistent across `commentRangeStart`, `commentRangeEnd`,
  `commentReference` and `word/comments.xml`.
- A missing `commentRangeEnd` or an id that matches nothing makes Word report
  the file as unreadable and offer to repair it.

Word tolerates `commentsExtended`, `commentsIds`, `commentsExtensible` and
`people` being absent — they only add threading and identity. Start with
`comments.xml` plus the anchor, verify, then add threading if replies matter.

## Reading a document that already has revisions

Extraction defaults hide pending edits. `pandoc -f docx` behaves as
`--track-changes=accept`, so a contract with unaccepted redlines reads as if the
redlines were already agreed. `[verified]` When the point of reading is to
report what is pending, use `--track-changes=all` and say who proposed what.

<!-- sources: ecma-376, pandoc-docs, anthropic-docx -->
