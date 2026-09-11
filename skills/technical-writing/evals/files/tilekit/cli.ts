#!/usr/bin/env node
import { writeFile } from "node:fs/promises";
import { parseArgs } from "node:util";
import { AtlasTooSmall, loadSprites, packTiles } from "./index.js";

const USAGE = `tilekit pack <sprite-dir> [options]

Options:
  --out <path>       Atlas PNG to write            (default: atlas.png)
  --map <path>       Frame map JSON to write       (default: atlas.json)
  --max-size <px>    Longest edge of the atlas     (default: 2048)
  --padding <px>     Gutter between frames         (default: 2)
  --power-of-two     Round the atlas up to a power of two
`;

const { values, positionals } = parseArgs({
  allowPositionals: true,
  options: {
    out: { type: "string", default: "atlas.png" },
    map: { type: "string", default: "atlas.json" },
    "max-size": { type: "string", default: "2048" },
    padding: { type: "string", default: "2" },
    "power-of-two": { type: "boolean", default: false },
  },
});

if (positionals[0] !== "pack" || !positionals[1]) {
  process.stdout.write(USAGE);
  process.exit(positionals.length === 0 ? 0 : 2);
}

try {
  const sprites = await loadSprites(positionals[1]);
  const atlas = await packTiles(sprites, {
    maxSize: Number(values["max-size"]),
    padding: Number(values.padding),
    powerOfTwo: values["power-of-two"],
  });
  await writeFile(values.out!, atlas.image);
  await writeFile(values.map!, JSON.stringify({ frames: atlas.frames }, null, 2));
  process.stdout.write(
    `packed ${atlas.frames.length} sprites into ${atlas.width}x${atlas.height} -> ${values.out}\n`,
  );
} catch (error) {
  if (error instanceof AtlasTooSmall) {
    process.stderr.write(`tilekit: ${error.message}\n`);
    process.exit(1);
  }
  throw error;
}
