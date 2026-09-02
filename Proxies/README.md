# Static ISP proxy bundle

This folder is a self-contained, portable bundle for the 50 Oxylabs Dedicated
ISP (static ISP) routes assigned to this account.

## Files

- `proxy-urls.txt` — one authenticated proxy URL per line, ports 8001–8050.
- `proxies.env` — a base `STATIC_ISP_PROXY_URL`, `PROXY_01_URL` through
  `PROXY_50_URL`, and a comma-separated `STATIC_ISP_PROXY_URLS` value.
- `proxies.json` — structured provider, authentication, and route details.
- `build-proxy-files.ps1` — rebuilds the three credential files from a source
  `.env` containing `STATIC_ISP_PROXY_URL`.
- `verify-proxies.ps1` — checks each route and reports its public IP without
  printing credentials.

## Use in another workspace

Copy this entire `Proxies` folder, including its hidden `.gitignore` file. The
generated files already contain the credentials, so rebuilding is optional.

For an application that accepts a conventional proxy URL, use any line from
`proxy-urls.txt`. For a dotenv-based application, copy the needed entries from
`proxies.env` into that project's private `.env` file or load `proxies.env`
directly.

Examples of conventional environment variables:

```powershell
$env:HTTP_PROXY = $env:PROXY_01_URL
$env:HTTPS_PROXY = $env:PROXY_01_URL
```

```bash
export HTTP_PROXY="$PROXY_01_URL"
export HTTPS_PROXY="$PROXY_01_URL"
```

To verify that the 50 ports currently resolve to 50 distinct public IPs:
```powershell
.\verify-proxies.ps1
```

To rebuild the generated files after credentials change:

```powershell
.\build-proxy-files.ps1 -SourceEnv C:\path\to\source\.env
```

## Security

The three generated files contain live usernames and passwords. Keep them out
of source control, cloud sync, tickets, chat, logs, and screenshots. The local
`.gitignore` protects them when the whole folder is copied, but some copy tools
omit hidden files; confirm `.gitignore` arrives in the destination. If the
bundle is exposed, rotate or revoke the credentials with the provider.

