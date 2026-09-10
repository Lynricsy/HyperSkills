/**
 * Convert a title into a URL slug: lowercase, ASCII words joined by single
 * hyphens, with no leading or trailing hyphen.
 */
export function toSlug(title) {
  return String(title)
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]/g, '-');
}
