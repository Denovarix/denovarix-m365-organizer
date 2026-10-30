# Denovarix M365 Organizer

An MCP server and CLI that organises a **personal Microsoft account** (Outlook.com / Hotmail / Live) through Microsoft Graph:
mail folder trees, sender statistics, bulk moves, inbox rules and OneDrive folders.

It was built to tidy an inbox of 52,000 unread notifications into a dozen folders in one afternoon, and to give Claude Code
(or any MCP client) the organising tools that mail-reading MCP servers usually leave out.

## What it adds

| Tool | What it does |
|---|---|
| `mail_folder_tree` | Every folder with path, total and unread counts |
| `mail_create_folder` | Create nested paths like `Finance/Banking` in one call |
| `mail_sender_stats` | Top senders and domains in a folder, the input for a plan |
| `mail_move_from_senders` | Bulk-move existing mail from addresses or `@domains` (JSON batch, 20 per request) |
| `mail_list_rules` / `mail_add_sender_rule` / `mail_delete_rule` | Server-side inbox rules so future mail files itself |
| `drive_list` / `drive_create_folder` / `drive_move` | OneDrive listing, nested folders, moves |

Teams is **not** covered: Graph refuses Teams endpoints for personal accounts ("requires a valid license").

## Setup

1. **Entra app registration** (free, 3 minutes). In the Azure portal create an app with
   *Supported account types = Personal Microsoft accounts only*, no redirect URI, and under
   *Authentication → Advanced settings* set **Allow public client flows = Yes**.
   Delegated Graph permissions requested at runtime: `Mail.ReadWrite`, `MailboxSettings.ReadWrite`, `Files.ReadWrite.All`, `User.Read`.
2. **Install**
   ```
   pip install git+https://github.com/Denovarix/denovarix-m365-organizer
   ```
   On Windows enable long paths first if pip fails on deep package paths:
   `Set-ItemProperty HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem LongPathsEnabled 1` (admin).
3. **Configure** `~/.m365-organizer/config.json` (see `examples/config.example.json`):
   ```json
   { "client_id": "YOUR-ENTRA-APP-CLIENT-ID", "tenant_id": "consumers" }
   ```
4. **Sign in once** with the device-code flow. Tokens are cached in `~/.m365-organizer/token_cache.bin`.
   ```
   m365-organizer auth
   ```
5. **Add to Claude Code**
   ```
   claude mcp add --scope user m365-organizer -- m365-organizer serve
   ```

## Organise a mailbox from the command line

```
python examples/apply_plan.py examples/plan.example.json            # folders + rules + move backlog
python examples/apply_plan.py examples/plan.example.json --no-move  # folders + rules only
```

A plan is a JSON map of folder path to senders. Domains start with `@`, addresses do not:

```json
{
  "Jobs & Freelance/LinkedIn": ["@linkedin.com"],
  "Finance/Banking": ["@axisbank.com", "@icicibank.com"],
  "Personal": ["someone@example.com"]
}
```

The script is idempotent: existing folders and rules are reused, and moves only touch what is still in the Inbox.

## Layout

```
m365_organizer/graph.py    MSAL device-code auth, retry/backoff, paging, $batch
m365_organizer/mail.py     folders, sender stats, bulk move, inbox rules
m365_organizer/drive.py    OneDrive list / mkdir -p / move
m365_organizer/server.py   FastMCP server + `auth` / `serve` CLI
examples/                  config and plan examples, apply_plan.py
```

## Licence

MIT. Built by Denovarix with Sourav De.
