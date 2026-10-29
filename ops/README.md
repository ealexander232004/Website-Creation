# Keeplyn operations

Work is prepared on the always-on Ubuntu PC and approved by a person at
**keeplyn.com/admin/approvals** (works on phone, laptop or PC). Nothing reaches a
customer or a lead without an approval click.

| Trigger | Worker (this PC) | You approve | Then |
|---|---|---|---|
| New website request | Claude Code (Opus, your subscription) builds a demo from `site-starter/`; Codex (via `omp --profile keeplyn-img`) makes missing photos; deploys to `<request>.demo.keeplyn.com` | **Publish & email customer** | Customer gets the demo-ready email |
| Customer update ticket | Claude applies the change; deploys a preview | **Approve & email customer** (edit the message) | Ticket completed, customer emailed, preview promoted to their demo/site |
| You send a demo back with a note | Rebuilds with your note | Same as above | — |
| Reply to a cold email (Instantly) | Opus drafts a reply; opt-outs are blocklisted automatically, auto-replies ignored | **Send reply** (edit first if you like) | Sent from the original mailbox |

You're alerted by email at support@keeplyn.com (and on your phone if
`~/.config/keeplyn-worker/ntfy-topic` holds an [ntfy](https://ntfy.sh) topic).

## Pieces

- `worker/keeplyn_worker.py` — the worker. `doctor` checks setup; `run --lane fast` (replies, sending, promotions, every 30 s) and `run --lane build` (demos/revisions, one at a time) run as user services via `worker/install.sh`.
- `site-starter/` — the Next.js scaffold every customer site starts from. The Moss/Northline/Sera templates are copied in fresh from `Keeplyn.com/` for each new site. `site-starter/CLAUDE.md` is the builder's playbook.
- Customer sites live in `~/keeplyn-sites/kl-r<request>-<name>/`, one Vercel project each. Customer briefs (`job/`) never leave the PC.
- Database: `Keeplyn.com/supabase/migrations/20261029120000_ops_approval_queue.sql` (`ops_items`).

## Safety

- Customer briefs and lead replies are treated as data. Models run with no secrets in their environment, no MCP servers, no web tools; the builder can only edit its site folder and run `npm run typecheck|build`. Image generation runs in an isolated omp profile with only the image tool.
- Secrets stay in `~/.config/keeplyn-worker/` and `~/.config/claude-mcp/` (mode 600) and are only used by the worker script itself.

## Setup checklist

1. Supabase secret key → `~/.config/keeplyn-worker/supabase.key` (`chmod 600`).
2. Claude Code CLI login (`claude` → `/login`), extra usage enabled with a spending cap on claude.ai.
3. `omp --profile keeplyn-img` → `/login` → OpenAI Codex.
4. DNS: `CNAME *.demo → cname.vercel-dns.com` on keeplyn.com (Porkbun).
5. `ops/worker/install.sh` (runs `doctor` first).
