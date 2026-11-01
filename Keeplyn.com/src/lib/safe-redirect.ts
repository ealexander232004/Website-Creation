/** Only allow same-site relative paths, so auth links cannot redirect off Keeplyn. */
export function safeNextPath(value: string | null | undefined, fallback = "/portal") {
  if (!value || !value.startsWith("/") || value.startsWith("//") || value.startsWith("/\\")) return fallback;
  return value;
}

/** Sign-in URL that brings the visitor back to `next` afterwards. */
export function signInPath(next: string) {
  return `/start?mode=signin&next=${encodeURIComponent(safeNextPath(next))}`;
}
