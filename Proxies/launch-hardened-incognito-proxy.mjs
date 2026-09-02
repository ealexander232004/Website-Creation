import fs from "node:fs";
import net from "node:net";
import os from "node:os";
import path from "node:path";
import tls from "node:tls";
import { spawn } from "node:child_process";

const [proxyFile, routeText = "1"] = process.argv.slice(2);
const route = Number.parseInt(routeText, 10);

if (!proxyFile || !Number.isInteger(route) || route < 1) process.exit(2);

const proxyLines = fs
  .readFileSync(proxyFile, "utf8")
  .split(/\r?\n/)
  .map((line) => line.trim())
  .filter(Boolean);
const upstream = new URL(proxyLines[route - 1]);
if (!upstream.hostname || !upstream.username || !upstream.password) process.exit(3);

const upstreamPort = Number(upstream.port || 443);
const credentials = `${decodeURIComponent(upstream.username)}:${decodeURIComponent(upstream.password)}`;
const proxyAuthorization = `Basic ${Buffer.from(credentials).toString("base64")}`;
const headerLimit = 64 * 1024;

function injectAuthentication(headerBuffer) {
  const headerText = headerBuffer.toString("latin1");
  const lines = headerText.split("\r\n");
  const requestLine = lines.shift();
  if (!requestLine) throw new Error("Missing proxy request line");

  const isConnect = /^CONNECT\s/i.test(requestLine);
  const retainedHeaders = lines.filter(
    (line) => !/^Proxy-Authorization\s*:/i.test(line) && line !== "",
  );

  retainedHeaders.push(`Proxy-Authorization: ${proxyAuthorization}`);
  if (!isConnect) {
    for (let index = retainedHeaders.length - 1; index >= 0; index -= 1) {
      if (/^(Proxy-)?Connection\s*:/i.test(retainedHeaders[index])) {
        retainedHeaders.splice(index, 1);
      }
    }
    retainedHeaders.push("Connection: close", "Proxy-Connection: close");
  }

  return Buffer.from(`${requestLine}\r\n${retainedHeaders.join("\r\n")}\r\n\r\n`, "latin1");
}

// Chrome connects only to this loopback server. Each browser connection is
// forwarded over a certificate-verified TLS connection to Oxylabs. The relay
// modifies only the initial proxy request to add authentication, then streams
// bytes in both directions without parsing or synthesizing proxy responses.
const relay = net.createServer((clientSocket) => {
  let pending = Buffer.alloc(0);
  let connected = false;

  const rejectClient = () => {
    if (!clientSocket.destroyed) {
      clientSocket.end("HTTP/1.1 502 Bad Gateway\r\nConnection: close\r\n\r\n");
    }
  };

  const receiveInitialRequest = (chunk) => {
    pending = Buffer.concat([pending, chunk]);
    if (pending.length > headerLimit) {
      rejectClient();
      return;
    }

    const headerEnd = pending.indexOf("\r\n\r\n");
    if (headerEnd < 0) return;

    clientSocket.pause();
    clientSocket.removeListener("data", receiveInitialRequest);

    let authenticatedHeader;
    try {
      authenticatedHeader = injectAuthentication(pending.subarray(0, headerEnd + 4));
    } catch {
      rejectClient();
      return;
    }
    const remainingData = pending.subarray(headerEnd + 4);

    const upstreamSocket = tls.connect({
      host: upstream.hostname,
      port: upstreamPort,
      family: 4,
      servername: upstream.hostname,
      rejectUnauthorized: true,
      ALPNProtocols: ["http/1.1"],
    });

    upstreamSocket.setKeepAlive(true, 30_000);
    upstreamSocket.once("secureConnect", () => {
      connected = true;
      upstreamSocket.write(authenticatedHeader);
      if (remainingData.length) upstreamSocket.write(remainingData);
      upstreamSocket.pipe(clientSocket);
      clientSocket.pipe(upstreamSocket);
      clientSocket.resume();
    });

    upstreamSocket.on("error", () => {
      if (!connected) rejectClient();
      clientSocket.destroy();
    });
    clientSocket.on("error", () => upstreamSocket.destroy());
    clientSocket.on("close", () => upstreamSocket.destroy());
  };

  clientSocket.setKeepAlive(true, 30_000);
  clientSocket.on("data", receiveInitialRequest);
  clientSocket.on("error", () => {});
});

relay.listen(0, "127.0.0.1", () => {
  const address = relay.address();
  if (!address || typeof address === "string") process.exit(4);

  const chromePath = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
  const profile = path.join(os.tmpdir(), `CodexHardenedProxy${route}-${process.pid}`);
  const chrome = spawn(
    chromePath,
    [
      `--user-data-dir=${profile}`,
      "--incognito",
      `--proxy-server=http://127.0.0.1:${address.port}`,
      "--force-webrtc-ip-handling-policy=disable_non_proxied_udp",
      "--disable-quic",
      "--no-first-run",
      "--no-default-browser-check",
      "about:blank",
    ],
    { stdio: "ignore", windowsHide: false },
  );

  chrome.on("error", () => relay.close(() => process.exit(5)));
  chrome.on("exit", () => {
    relay.close(() => {
      const safePrefix = path.join(os.tmpdir(), `CodexHardenedProxy${route}-`);
      if (profile.startsWith(safePrefix)) {
        fs.rmSync(profile, { recursive: true, force: true, maxRetries: 3, retryDelay: 200 });
      }
      process.exit(0);
    });
  });
});
