/** Only allow same-site relative paths, so auth links cannot redirect off Keeplyn. */
export function safeNextPath(value: string | null | undefined, fallback = "/portal") {
  if (!value || !value.startsWith("/") || value.startsWith("//") || value.startsWith("/\\")) return fallback;
  return value;
}
