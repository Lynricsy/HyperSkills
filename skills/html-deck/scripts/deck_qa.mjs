#!/usr/bin/env node
// Render-time gate for an HTML deck: per-slide geometry measurement, per-slide
// PNG, and an optional PDF. Reading the source cannot find overflow, because
// overflow is a property of the rendered box tree, not of the markup.
//
//   node scripts/deck_qa.mjs deck.html --out qa
//   node scripts/deck_qa.mjs deck.html --out qa --pdf
//   node scripts/deck_qa.mjs http://127.0.0.1:8000/deck.html --slides 12
//
// Exit code 1 means at least one error-level finding. Warnings alone exit 0.
//
// Install the one dependency next to the deck (`npm install playwright`), not
// next to this script: playwright-core ships its own SKILL.md files, and a
// node_modules inside a skill directory registers them as extra skills in any
// recursive skill scanner.

import { mkdir, writeFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { resolve, join } from 'node:path';
import { createRequire } from 'node:module';

// Bare ESM imports resolve from this file's directory, which is inside the
// skill; the dependency lives wherever the deck is. Resolve from the working
// directory first, then fall back to anything installed beside the script.
const chromium = (() => {
  for (const from of [resolve(process.cwd(), 'package.json'), import.meta.url]) {
    try {
      return createRequire(from)('playwright').chromium;
    } catch { /* try the next resolution root */ }
  }
  console.error(
    'deck_qa: playwright not found. Run `npm install playwright` in this directory, '
    + 'then `npx playwright install chromium`.',
  );
  process.exit(2);
})();

// 1280x720 is the smallest 16:9 viewport that still renders a 1920-wide design
// faithfully after the stage scales; 2x device pixels keep 24px text legible in
// the PNG a human reviews.
const DEFAULT_VIEWPORT = { width: 1280, height: 720 };
const DEVICE_SCALE = 2;
// Author-facing canvas. Every measured px is normalised to this height so the
// thresholds below hold whatever viewport the QA run used.
const CANVAS_HEIGHT = 1080;
// Smallest legible size on a projector, normalised to the 1080p canvas: 12pt on
// a 540pt-tall slide, doubled (1080px / 540pt = 2px per pt).
const TYPE_FLOOR_PX = 24;
// A whitespace check was tried here and removed: measured against this skill's
// own shell it fired on a centred cover and on a bottom-pinned source line,
// both deliberate. Composition is judged by reading the PNGs; this script only
// reports failures a renderer can prove.
// Sub-pixel layout rounding is not an overflow; anything past this is real.
const OVERFLOW_TOLERANCE_PX = 1;
// Covers a typical 200ms slide transition plus one frame of settle.
const TRANSITION_SETTLE_MS = 250;
// Hard stop for key-driven navigation on a deck that never reports its length.
const MAX_SLIDES = 200;
// Console keeps the worst few findings per slide and kind; three is enough to
// see whether one element or the whole block overflows.
const WORST_PER_GROUP = 3;

function parseArgs(argv) {
  const args = {
    deck: null, out: 'deck-qa', pdf: false, slides: 0, json: null,
    viewport: { ...DEFAULT_VIEWPORT },
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--pdf') args.pdf = true;
    else if (arg === '--out') args.out = argv[++i];
    else if (arg === '--json') args.json = argv[++i];
    else if (arg === '--slides') args.slides = Number(argv[++i]);
    else if (arg === '--viewport') {
      // Findings are normalised to the author canvas, so a different viewport
      // must produce the same report. Use it to check that, or to render at
      // the resolution the venue will actually use.
      const [w, h] = String(argv[++i]).split('x').map(Number);
      if (!w || !h) fail('--viewport expects WIDTHxHEIGHT, e.g. 1920x1080');
      args.viewport = { width: w, height: h };
    }
    else if (arg.startsWith('--')) fail(`unknown option ${arg}`);
    else if (!args.deck) args.deck = arg;
    else fail(`unexpected argument ${arg}`);
  }
  if (!args.deck) fail('usage: deck_qa.mjs <deck.html|url> [--out dir] [--slides N] [--viewport WxH] [--pdf] [--json file]');
  if (args.slides && !Number.isInteger(args.slides)) fail('--slides expects an integer');
  return args;
}

function fail(message) {
  console.error(`deck_qa: ${message}`);
  process.exit(2);
}

function toUrl(deck) {
  if (/^https?:\/\//.test(deck) || deck.startsWith('file://')) return deck;
  const path = resolve(deck);
  if (!existsSync(path)) fail(`deck not found: ${path}`);
  return pathToFileURL(path).href;
}

// Runs in the page. Returns the visible slide's geometry findings, normalised to
// CANVAS_HEIGHT so thresholds are viewport-independent.
function measureInPage({ canvasHeight, typeFloor, tolerance }) {
  const selectors = ['[data-slide]', '.slide', '.slides > section', 'section'];
  let slides = [];
  for (const selector of selectors) {
    slides = [...document.querySelectorAll(selector)];
    if (slides.length) break;
  }
  const visible = slides.find((el) => {
    const style = getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') return false;
    if (Number(style.opacity) === 0) return false;
    const box = el.getBoundingClientRect();
    return box.width > 0 && box.height > 0;
  });
  const slide = visible || document.body;
  const frame = slide.getBoundingClientRect();
  // Two different units meet here and mixing them hides small type.
  // getBoundingClientRect() reports post-transform device-ish px, while
  // getComputedStyle().fontSize and scrollHeight/clientHeight report the
  // untransformed layout px the author wrote. A 1920x1080 stage scaled into a
  // 1280x720 viewport has scale 0.667: normalising a 16px font by the rect
  // factor (1.5) reports 24px and passes the floor it should fail.
  const layoutHeight = slide.offsetHeight || frame.height;   // untransformed
  const kRect = frame.height > 0 ? canvasHeight / frame.height : 1;
  const kCss = layoutHeight > 0 ? canvasHeight / layoutHeight : 1;

  const findings = [];
  const label = (el) => {
    const text = (el.textContent || '').trim().replace(/\s+/g, ' ');
    return text ? text.slice(0, 60) : `<${el.tagName.toLowerCase()}>`;
  };

  const descendants = [...slide.querySelectorAll('*')].filter((el) => {
    const style = getComputedStyle(el);
    if (style.display === 'none' || style.visibility === 'hidden') return false;
    return Number(style.opacity) !== 0;
  });

  for (const el of descendants) {
    const box = el.getBoundingClientRect();
    if (box.width === 0 && box.height === 0) continue;
    const over = {
      bottom: box.bottom - frame.bottom,
      right: box.right - frame.right,
      top: frame.top - box.top,
      left: frame.left - box.left,
    };
    for (const [side, amount] of Object.entries(over)) {
      if (amount > tolerance) {
        findings.push({
          level: 'error',
          kind: 'overflow',
          side,
          px: Math.round(amount * kRect),
          element: label(el),
        });
      }
    }

    const style = getComputedStyle(el);
    const clips = /hidden|clip|auto|scroll/.test(style.overflowY);
    if (clips && el.scrollHeight - el.clientHeight > tolerance) {
      findings.push({
        level: 'error',
        kind: 'clipped',
        px: Math.round((el.scrollHeight - el.clientHeight) * kCss),
        element: label(el),
      });
    }

    const own = [...el.childNodes].some(
      (node) => node.nodeType === Node.TEXT_NODE && node.textContent.trim(),
    );
    if (own) {
      const size = parseFloat(style.fontSize) * kCss;
      if (size < typeFloor) {
        findings.push({
          level: 'error',
          kind: 'type-floor',
          px: Math.round(size),
          floor: typeFloor,
          element: label(el),
        });
      }
    }
  }

  return {
    slideCount: slides.length,
    canvas: { width: Math.round(frame.width), height: Math.round(frame.height) },
    layoutHeight: Math.round(layoutHeight),
    findings,
  };
}

async function slideCount(page, override) {
  if (override) return override;
  const reported = await page.evaluate(() => {
    const deck = globalThis.deck;
    if (deck && Number.isInteger(deck.count)) return deck.count;
    for (const selector of ['[data-slide]', '.slide', '.slides > section', 'section']) {
      const found = document.querySelectorAll(selector);
      if (found.length) return found.length;
    }
    return 1;
  });
  return Math.min(reported, MAX_SLIDES);
}

async function gotoSlide(page, index) {
  // A deck that exposes an API is navigated exactly; anything else gets the
  // arrow key every deck runtime binds. Key navigation is why --slides exists:
  // a deck with no API and no end state would otherwise be walked blindly.
  const usedApi = await page.evaluate((n) => {
    const deck = globalThis.deck;
    if (deck && typeof deck.goto === 'function') {
      deck.goto(n);
      return true;
    }
    return false;
  }, index);
  if (!usedApi && index > 0) await page.keyboard.press('ArrowRight');
  await page.waitForTimeout(TRANSITION_SETTLE_MS);
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const url = toUrl(args.deck);
  const outDir = resolve(args.out);
  await mkdir(outDir, { recursive: true });

  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: args.viewport,
    deviceScaleFactor: DEVICE_SCALE,
  });
  const page = await context.newPage();
  const consoleErrors = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text());
  });

  await page.goto(url, { waitUntil: 'load' });
  // Screenshots taken before this show fallback metrics, so every line break in
  // the PNG is a lie. `fonts.ready` alone is not enough for a font injected
  // after load: check the family the deck actually renders with.
  await page.evaluate(async () => {
    await document.fonts.ready;
  });
  const fontReady = await page.evaluate(() => {
    const body = getComputedStyle(document.body);
    const spec = `${body.fontWeight} ${body.fontSize} ${body.fontFamily}`;
    return { spec, loaded: document.fonts.check(spec) };
  });

  const total = await slideCount(page, args.slides);
  const slides = [];
  for (let i = 0; i < total; i += 1) {
    await gotoSlide(page, i);
    const measured = await page.evaluate(measureInPage, {
      canvasHeight: CANVAS_HEIGHT,
      typeFloor: TYPE_FLOOR_PX,
      tolerance: OVERFLOW_TOLERANCE_PX,
    });
    const shot = join(outDir, `slide.${String(i + 1).padStart(3, '0')}.png`);
    await page.screenshot({ path: shot });
    slides.push({ index: i + 1, screenshot: shot, ...measured });
  }

  let pdf = null;
  if (args.pdf) {
    const exact = await page.evaluate(() => {
      const value = getComputedStyle(document.body).printColorAdjust;
      return value === 'exact';
    });
    pdf = join(outDir, 'deck.pdf');
    // printBackground defaults to false and the page is rendered with the
    // `print` media type: both halves have to be right or the PDF comes out
    // white. preferCSSPageSize hands the paper size to the deck's `@page`.
    await page.pdf({ path: pdf, printBackground: true, preferCSSPageSize: true });
    if (!exact) {
      slides.push({
        index: 0,
        findings: [
          {
            level: 'warn',
            kind: 'print-color-adjust',
            detail: 'body lacks print-color-adjust: exact; colours may be optimised away in print media',
          },
        ],
      });
    }
  }

  const findings = slides.flatMap((slide) =>
    (slide.findings || []).map((finding) => ({ slide: slide.index, ...finding })),
  );
  const errors = findings.filter((f) => f.level === 'error');
  const warnings = findings.filter((f) => f.level === 'warn');

  const report = {
    deck: url,
    viewport: args.viewport,
    canvasHeight: CANVAS_HEIGHT,
    slides: total,
    font: fontReady,
    consoleErrors,
    findings,
  };
  if (args.json) await writeFile(resolve(args.json), JSON.stringify(report, null, 2));

  console.log(`deck: ${url}`);
  console.log(`slides: ${total}   screenshots: ${outDir}${pdf ? `   pdf: ${pdf}` : ''}`);
  if (!fontReady.loaded) {
    console.log(`font:  NOT READY for ${fontReady.spec} — the render used a fallback face`);
  }
  for (const error of consoleErrors) console.log(`console: ${error}`);
  // One overflowing list produces a finding per row. Printing all of them
  // buries the other slides, so the console keeps the worst few per slide and
  // kind and counts the rest; the JSON report keeps everything.
  const groups = new Map();
  for (const finding of findings) {
    const key = `${finding.slide}/${finding.kind}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(finding);
  }
  for (const group of groups.values()) {
    group.sort((a, b) => (b.px || 0) - (a.px || 0));
    for (const finding of group.slice(0, WORST_PER_GROUP)) {
      const where = finding.slide ? `slide ${finding.slide}` : 'deck';
      const detail = finding.detail
        || `${finding.px}px${finding.side ? ` past ${finding.side}` : ''}${finding.element ? ` — ${finding.element}` : ''}`;
      console.log(`${finding.level === 'error' ? 'FAIL' : 'warn'}  ${where}  ${finding.kind}: ${detail}`);
    }
    const hidden = group.length - WORST_PER_GROUP;
    if (hidden > 0) {
      console.log(`      … ${hidden} more ${group[0].kind} on slide ${group[0].slide}`);
    }
  }
  console.log(`${errors.length} error(s), ${warnings.length} warning(s)`);

  await browser.close();
  process.exit(errors.length ? 1 : 0);
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    console.error(`deck_qa: ${error.message}`);
    process.exit(2);
  });
}
