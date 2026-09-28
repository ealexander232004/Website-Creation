import "server-only";

/** The DNS records customers add at their registrar to point a domain at Vercel. */
export const DNS_TARGETS = {
  apexA: "76.76.21.21",
  wwwCname: "cname.vercel-dns.com",
} as const;

type DnsAnswer = { type: number; data: string };

async function lookup(name: string, type: "A" | "CNAME" | "NS"): Promise<string[] | null> {
  try {
    const response = await fetch(
      `https://cloudflare-dns.com/dns-query?name=${encodeURIComponent(name)}&type=${type}`,
      { headers: { accept: "application/dns-json" }, cache: "no-store", signal: AbortSignal.timeout(5000) },
    );
    if (!response.ok) return null;
    const body = (await response.json()) as { Status: number; Answer?: DnsAnswer[] };
    // Status 3 = NXDOMAIN: the name doesn't exist at all.
    if (body.Status === 3) return [];
    return (body.Answer ?? []).map((answer) => answer.data.replace(/\.$/, "").toLowerCase());
  } catch {
    return null;
  }
}

// Vercel's documented apex IP plus its newer anycast ranges.
const isVercelIp = (ip: string) => ip === DNS_TARGETS.apexA || /^216\.(150|198)\./.test(ip);
const isVercelCname = (host: string) => /(^|\.)vercel-dns(-\d+)?\.com$/.test(host);
const isPorkbunParking = (value: string) => /(pixie|uixie)\.porkbun\.com$/.test(value);

export type DomainCheck = {
  domain: string;
  /** DNS lookup service unreachable; nothing could be concluded. */
  unavailable: boolean;
  registered: boolean;
  apexConnected: boolean;
  wwwConnected: boolean;
  parkingActive: boolean;
  apexValues: string[];
  wwwValues: string[];
  /** Ready for checkout: registered, and the root or www points at Keeplyn's host. */
  ready: boolean;
};

export async function checkDomain(domain: string): Promise<DomainCheck> {
  const [ns, apexA, wwwCname, wwwA] = await Promise.all([
    lookup(domain, "NS"),
    lookup(domain, "A"),
    lookup(`www.${domain}`, "CNAME"),
    lookup(`www.${domain}`, "A"),
  ]);
  const unavailable = ns === null && apexA === null;
  const apexValues = apexA ?? [];
  const wwwValues = [...new Set([...(wwwCname ?? []), ...(wwwA ?? [])])];
  const registered = (ns?.length ?? 0) > 0 || apexValues.length > 0;
  const apexConnected = apexValues.length > 0 && apexValues.every(isVercelIp);
  const wwwConnected =
    (wwwCname ?? []).some(isVercelCname) || ((wwwA ?? []).length > 0 && (wwwA ?? []).every(isVercelIp));
  const parkingActive = [...apexValues, ...wwwValues].some(isPorkbunParking);
  return {
    domain,
    unavailable,
    registered,
    apexConnected,
    wwwConnected,
    parkingActive,
    apexValues,
    wwwValues,
    ready: registered && (apexConnected || wwwConnected),
  };
}
