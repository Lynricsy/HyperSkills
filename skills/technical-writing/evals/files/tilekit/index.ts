import { readdir } from "node:fs/promises";
import { join } from "node:path";
import sharp from "sharp";

export interface PackOptions {
  /** Longest edge of the output atlas, in pixels. */
  maxSize?: number;
  /** Transparent gutter inserted between frames, in pixels. */
  padding?: number;
  /** Round the atlas dimensions up to the next power of two. */
  powerOfTwo?: boolean;
}

export interface Frame {
  name: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface Atlas {
  image: Buffer;
  frames: Frame[];
  width: number;
  height: number;
}

export class AtlasTooSmall extends Error {}

const DEFAULTS: Required<PackOptions> = {
  maxSize: 2048,
  padding: 2,
  powerOfTwo: false,
};

/** Reads every PNG in `dir` and returns them sorted by name. */
export async function loadSprites(dir: string): Promise<{ name: string; data: Buffer }[]> {
  const names = (await readdir(dir)).filter((n) => n.endsWith(".png")).sort();
  return Promise.all(
    names.map(async (name) => ({
      name: name.slice(0, -4),
      data: await sharp(join(dir, name)).toBuffer(),
    })),
  );
}

/**
 * Packs sprites into one atlas.
 *
 * Throws `AtlasTooSmall` when the sprites do not fit inside `maxSize`.
 */
export async function packTiles(
  sprites: { name: string; data: Buffer }[],
  options: PackOptions = {},
): Promise<Atlas> {
  const { maxSize, padding, powerOfTwo } = { ...DEFAULTS, ...options };
  const frames: Frame[] = [];
  let penX = 0;
  let penY = 0;
  let shelfHeight = 0;

  for (const sprite of sprites) {
    const { width = 0, height = 0 } = await sharp(sprite.data).metadata();
    if (penX + width > maxSize) {
      penX = 0;
      penY += shelfHeight + padding;
      shelfHeight = 0;
    }
    if (penY + height > maxSize) {
      throw new AtlasTooSmall(
        `sprites do not fit in ${maxSize}x${maxSize}; raise maxSize`,
      );
    }
    frames.push({ name: sprite.name, x: penX, y: penY, width, height });
    penX += width + padding;
    shelfHeight = Math.max(shelfHeight, height);
  }

  const used = Math.max(...frames.map((f) => Math.max(f.x + f.width, f.y + f.height)));
  const side = powerOfTwo ? 2 ** Math.ceil(Math.log2(used)) : used;
  const image = await sharp({
    create: { width: side, height: side, channels: 4, background: { r: 0, g: 0, b: 0, alpha: 0 } },
  })
    .composite(sprites.map((s, i) => ({ input: s.data, left: frames[i].x, top: frames[i].y })))
    .png()
    .toBuffer();

  return { image, frames, width: side, height: side };
}
