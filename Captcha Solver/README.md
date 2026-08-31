# CapSolver API bundle

This folder is a portable, self-contained bundle for the CapSolver account used
by the original Dropshipping project. It contains the live API credential,
machine-readable configuration, reusable clients, known task formats, and a
non-destructive account check.

## Contents

- `capsolver.env` — dotenv configuration with the live API key and base URL.
- `capsolver.json` — structured account, endpoint, task-type, and module data.
- `api-reference.md` — request formats used by the existing integration.
- `capsolver_client.py` — dependency-free Python client.
- `capsolver-client.mjs` — dependency-free Node.js client (Node 18+).
- `verify-capsolver.ps1` — validates the key with `getBalance`; it does not
  create a paid CAPTCHA task.
- `build-config.ps1` — rebuilds the two credential files from another dotenv
  file containing `CAPSOLVER_API_KEY`.

## Quick start

PowerShell:

```powershell
Get-Content .\capsolver.env | ForEach-Object {
    if ($_ -match '^(?<name>[^#=]+)=(?<value>.*)$') {
        Set-Item -Path "Env:$($Matches.name)" -Value $Matches.value
    }
}
.\verify-capsolver.ps1
```

Python:

```python
from capsolver_client import CapSolverClient

client = CapSolverClient.from_env_file("capsolver.env")
print(client.get_balance())
```

Node.js:

```javascript
import { CapSolverClient, loadEnvFile } from "./capsolver-client.mjs";

loadEnvFile("capsolver.env");
const client = CapSolverClient.fromEnvironment();
console.log(await client.getBalance());
```

See `api-reference.md` for task payloads matching the Google scraping
integration.

## Security

`capsolver.env` and `capsolver.json` contain the live API key. Keep both files
out of source control, cloud sync, tickets, chat, logs, and screenshots. Copy
the hidden `.gitignore` with this folder. Some copy tools omit hidden files, so
confirm it arrives in the destination. Rotate the key in CapSolver if the
bundle is exposed.
