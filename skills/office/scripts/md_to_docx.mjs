#!/usr/bin/env node
// Markdown -> Word (.docx) with no native dependency: `docx` + `marked` only.
//
// Usage: node md_to_docx.mjs <input.md> [output.docx]
// Install once: cd scripts && npm install
//
// Supports YAML front matter (title/subtitle/date/version/audience) rendered as
// a title page, ATX headings, paragraphs with inline emphasis and links,
// bullet/ordered lists, fenced code blocks, tables, horizontal rules, and
// images resolved relative to the input file.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

// `docx` and `marked` are not vendored. Import them dynamically so a missing
// `npm install` produces the one command that fixes it instead of a stack trace.
let marked, docx;
try {
  ({ marked } = await import("marked"));
  docx = await import("docx");
} catch (err) {
  if (err?.code !== "ERR_MODULE_NOT_FOUND") throw err;
  const dir = path.dirname(fileURLToPath(import.meta.url));
  console.error(
    `Missing Node dependencies for md_to_docx.mjs (docx, marked).\n` +
      `Fix: cd ${dir} && npm install`,
  );
  process.exit(2);
}

const {
  AlignmentType,
  BorderStyle,
  Document,
  ExternalHyperlink,
  HeadingLevel,
  ImageRun,
  Packer,
  PageBreak,
  Paragraph,
  ShadingType,
  Table,
  TableCell,
  TableRow,
  TextRun,
  WidthType,
} = docx;

// Word measures images in EMU but the docx builder takes points; 1 inch = 72 pt
// and the default Letter page with 1" margins leaves 6.5" of text width.
const MAX_IMAGE_WIDTH_PT = 6.5 * 72;
// docx accepts an explicit image type only from this set; anything else must be
// converted first, because a wrong or missing type writes a media part with an
// "undefined" extension and no content-type override.
const IMAGE_TYPES = { ".png": "png", ".jpg": "jpg", ".jpeg": "jpg", ".gif": "gif", ".bmp": "bmp" };
// Calibri and Consolas are what Word itself defaults to; both have metric
// substitutes on Linux, so LibreOffice-rendered previews match Word's layout.
const BODY_FONT = "Calibri";
const CODE_FONT = "Consolas";
const HEADING_COLOR = "1F3864";
const CODE_SHADE = "F2F2F2";
const TABLE_HEADER_SHADE = "DEE6F1";
const HEADINGS = [
  HeadingLevel.HEADING_1,
  HeadingLevel.HEADING_2,
  HeadingLevel.HEADING_3,
  HeadingLevel.HEADING_4,
  HeadingLevel.HEADING_5,
  HeadingLevel.HEADING_6,
];

function fail(message) {
  console.error(`error: ${message}`);
  process.exit(1);
}

function splitFrontMatter(text) {
  if (!text.startsWith("---")) return { meta: {}, body: text };
  const end = text.indexOf("\n---", 3);
  if (end === -1) return { meta: {}, body: text };
  const meta = {};
  for (const line of text.slice(4, end).split("\n")) {
    const idx = line.indexOf(":");
    if (idx === -1) continue;
    meta[line.slice(0, idx).trim()] = line
      .slice(idx + 1)
      .trim()
      .replace(/^["']|["']$/g, "");
  }
  return { meta, body: text.slice(end + 4).replace(/^\n/, "") };
}

/** PNG/JPEG/GIF/BMP intrinsic size, so images keep their aspect ratio. */
function imageSize(buffer, ext) {
  if (ext === ".png" && buffer.length > 24) {
    return { width: buffer.readUInt32BE(16), height: buffer.readUInt32BE(20) };
  }
  if (ext === ".gif" && buffer.length > 10) {
    return { width: buffer.readUInt16LE(6), height: buffer.readUInt16LE(8) };
  }
  if (ext === ".bmp" && buffer.length > 26) {
    return { width: buffer.readInt32LE(18), height: Math.abs(buffer.readInt32LE(22)) };
  }
  if (ext === ".jpg" || ext === ".jpeg") {
    let offset = 2;
    while (offset + 9 < buffer.length) {
      if (buffer[offset] !== 0xff) {
        offset += 1;
        continue;
      }
      const marker = buffer[offset + 1];
      const length = buffer.readUInt16BE(offset + 2);
      if (marker >= 0xc0 && marker <= 0xcf && ![0xc4, 0xc8, 0xcc].includes(marker)) {
        return { height: buffer.readUInt16BE(offset + 5), width: buffer.readUInt16BE(offset + 7) };
      }
      offset += 2 + length;
    }
  }
  // Unknown geometry: fall back to a square that respects the width budget.
  return { width: MAX_IMAGE_WIDTH_PT, height: MAX_IMAGE_WIDTH_PT };
}

function inlineRuns(tokens, style = {}) {
  const runs = [];
  for (const token of tokens ?? []) {
    switch (token.type) {
      case "strong":
        runs.push(...inlineRuns(token.tokens, { ...style, bold: true }));
        break;
      case "em":
        runs.push(...inlineRuns(token.tokens, { ...style, italics: true }));
        break;
      case "del":
        runs.push(...inlineRuns(token.tokens, { ...style, strike: true }));
        break;
      case "codespan":
        runs.push(new TextRun({ text: token.text, font: CODE_FONT, ...style }));
        break;
      case "br":
        runs.push(new TextRun({ text: "", break: 1 }));
        break;
      case "link":
        runs.push(
          new ExternalHyperlink({
            link: token.href,
            children: inlineRuns(token.tokens, { ...style, style: "Hyperlink" }),
          })
        );
        break;
      case "image":
        runs.push(imageRun(token.href, token.text));
        break;
      default:
        runs.push(new TextRun({ text: token.raw ?? token.text ?? "", ...style }));
    }
  }
  return runs;
}

let sourceDir = ".";

function imageRun(href, alt) {
  const resolved = path.resolve(sourceDir, href);
  const ext = path.extname(resolved).toLowerCase();
  const type = IMAGE_TYPES[ext];
  if (!type) {
    return new TextRun({
      text: `[unsupported image format ${ext || "(none)"}: ${href}]`,
      italics: true,
    });
  }
  if (!fs.existsSync(resolved)) {
    return new TextRun({ text: `[image not found: ${href}]`, italics: true });
  }
  const data = fs.readFileSync(resolved);
  const { width, height } = imageSize(data, ext);
  const scale = Math.min(1, MAX_IMAGE_WIDTH_PT / width);
  // `type` is mandatory: without it the media part is written as
  // "<hash>.undefined" and no consumer can map it to a content type.
  return new ImageRun({
    type,
    data,
    altText: alt ? { name: alt, description: alt, title: alt } : undefined,
    transformation: { width: Math.round(width * scale), height: Math.round(height * scale) },
  });
}

function listParagraphs(token, depth = 0) {
  const out = [];
  for (const item of token.items) {
    const children = [];
    const nested = [];
    for (const child of item.tokens ?? []) {
      if (child.type === "list") nested.push(...listParagraphs(child, depth + 1));
      else if (child.type === "text" || child.type === "paragraph") children.push(...inlineRuns(child.tokens));
      else nested.push(...blockParagraphs(child));
    }
    out.push(
      new Paragraph({
        children: children.length ? children : [new TextRun("")],
        numbering: token.ordered ? { reference: "md-ordered", level: depth } : undefined,
        bullet: token.ordered ? undefined : { level: depth },
        indent: token.ordered ? { left: 360 * (depth + 1), hanging: 360 } : undefined,
        spacing: { after: 60 },
      })
    );
    out.push(...nested);
  }
  return out;
}

function codeParagraphs(token) {
  return token.text.split("\n").map(
    (line) =>
      new Paragraph({
        children: [new TextRun({ text: line || " ", font: CODE_FONT, size: 20 })],
        shading: { type: ShadingType.CLEAR, fill: CODE_SHADE },
        spacing: { after: 0 },
      })
  );
}

function tableBlock(token) {
  const widthPct = { size: 100, type: WidthType.PERCENTAGE };
  const header = new TableRow({
    tableHeader: true,
    children: token.header.map(
      (cell) =>
        new TableCell({
          shading: { type: ShadingType.CLEAR, fill: TABLE_HEADER_SHADE },
          children: [new Paragraph({ children: inlineRuns(cell.tokens, { bold: true }) })],
        })
    ),
  });
  const rows = token.rows.map(
    (row) =>
      new TableRow({
        children: row.map(
          (cell) => new TableCell({ children: [new Paragraph({ children: inlineRuns(cell.tokens) })] })
        ),
      })
  );
  return new Table({ width: widthPct, rows: [header, ...rows] });
}

function blockParagraphs(token) {
  switch (token.type) {
    case "heading":
      return [
        new Paragraph({
          heading: HEADINGS[Math.min(token.depth, 6) - 1],
          children: inlineRuns(token.tokens, { color: HEADING_COLOR }),
          spacing: { before: 240, after: 120 },
        }),
      ];
    case "paragraph":
      return [new Paragraph({ children: inlineRuns(token.tokens), spacing: { after: 120 } })];
    case "list":
      return listParagraphs(token);
    case "code":
      return codeParagraphs(token);
    case "table":
      return [tableBlock(token), new Paragraph({ text: "", spacing: { after: 120 } })];
    case "blockquote":
      return (token.tokens ?? []).flatMap((child) =>
        blockParagraphs(child).map(
          (p) =>
            new Paragraph({
              children: child.tokens ? inlineRuns(child.tokens, { italics: true }) : [new TextRun("")],
              indent: { left: 360 },
              border: { left: { style: BorderStyle.SINGLE, size: 12, color: HEADING_COLOR, space: 8 } },
              spacing: { after: 120 },
            })
        )
      );
    case "hr":
      return [
        new Paragraph({
          border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "AAAAAA", space: 1 } },
          spacing: { after: 120 },
        }),
      ];
    case "space":
      return [];
    default:
      return token.text ? [new Paragraph({ text: token.text, spacing: { after: 120 } })] : [];
  }
}

function titlePage(meta) {
  const [title, subtitle] = (meta.title ?? "").split(/\s+[—–]\s+/);
  if (!title) return [];
  const lines = [
    new Paragraph({
      children: [new TextRun({ text: title, bold: true, size: 56, color: HEADING_COLOR })],
      alignment: AlignmentType.CENTER,
      spacing: { before: 2400, after: 240 },
    }),
  ];
  if (subtitle) {
    lines.push(
      new Paragraph({
        children: [new TextRun({ text: subtitle, size: 32, color: "444444" })],
        alignment: AlignmentType.CENTER,
        spacing: { after: 480 },
      })
    );
  }
  for (const key of ["date", "version", "audience"]) {
    if (!meta[key]) continue;
    lines.push(
      new Paragraph({
        children: [new TextRun({ text: `${key[0].toUpperCase()}${key.slice(1)}: ${meta[key]}`, size: 22 })],
        alignment: AlignmentType.CENTER,
        spacing: { after: 80 },
      })
    );
  }
  // A page break is only honoured inside a paragraph; as a direct section child
  // it is written to the file and then ignored by every renderer.
  lines.push(new Paragraph({ children: [new PageBreak()] }));
  return lines;
}

function contentsPage(tokens) {
  const entries = tokens.filter((t) => t.type === "heading" && t.depth <= 3);
  if (entries.length < 2) return [];
  const out = [
    new Paragraph({
      heading: HeadingLevel.HEADING_1,
      children: [new TextRun({ text: "Contents", color: HEADING_COLOR })],
      spacing: { after: 120 },
    }),
  ];
  for (const entry of entries) {
    out.push(
      new Paragraph({
        children: [new TextRun({ text: entry.text, size: 22 })],
        indent: { left: 360 * (entry.depth - 1) },
        spacing: { after: 40 },
      })
    );
  }
  out.push(new Paragraph({ children: [new PageBreak()] }));
  return out;
}

function main() {
  const [input, outputArg] = process.argv.slice(2);
  if (!input) fail("usage: node md_to_docx.mjs <input.md> [output.docx]");
  if (!fs.existsSync(input)) fail(`${input} does not exist.`);

  const output = outputArg ?? `${path.basename(input, path.extname(input))}.docx`;
  sourceDir = path.dirname(path.resolve(input));

  const { meta, body } = splitFrontMatter(fs.readFileSync(input, "utf8"));
  const tokens = marked.lexer(body);
  const children = [...titlePage(meta), ...contentsPage(tokens), ...tokens.flatMap(blockParagraphs)];

  const doc = new Document({
    creator: "HyperSkills office skill",
    title: meta.title ?? path.basename(input),
    styles: { default: { document: { run: { font: BODY_FONT, size: 22 } } } },
    numbering: {
      config: [
        {
          reference: "md-ordered",
          levels: [0, 1, 2].map((level) => ({
            level,
            format: "decimal",
            text: `%${level + 1}.`,
            alignment: AlignmentType.START,
          })),
        },
      ],
    },
    sections: [{ children }],
  });

  Packer.toBuffer(doc)
    .then((buffer) => {
      fs.writeFileSync(output, buffer);
      console.log(`wrote ${output} (${buffer.length} bytes)`);
      console.log("verify next: render it and read the page images");
    })
    .catch((error) => fail(error.message));
}

main();
