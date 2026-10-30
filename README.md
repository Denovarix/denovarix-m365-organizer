<p align="center">
  <img src="assets/banner.png" alt="Denovarix M365 Organizer" width="100%">
</p>

<p align="center">
  <a href="LICENSE"><img alt="MIT" src="https://img.shields.io/badge/licence-MIT-FE5804?style=flat-square&labelColor=212226"></a>
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-FA9500?style=flat-square&labelColor=212226">
  <img alt="MCP" src="https://img.shields.io/badge/MCP-server%20%2B%20CLI-FE5804?style=flat-square&labelColor=212226">
  <img alt="Graph" src="https://img.shields.io/badge/Microsoft%20Graph-personal%20accounts-FA9500?style=flat-square&labelColor=212226">
  <img alt="Made by" src="https://img.shields.io/badge/made%20by-Denovarix-F7F6F4?style=flat-square&labelColor=212226">
</p>

<p align="center"><b>Organise a personal Microsoft account from Claude Code.</b><br>
Outlook folder trees, sender statistics, bulk moves, inbox rules and OneDrive folders, all through Microsoft Graph.</p>

<br>

Built to turn an inbox of **52,000 unread notifications** into fourteen folders in one afternoon, and to give Claude Code (or any MCP client) the organising tools that mail-reading MCP servers leave out.

<br>

## 🟧 What it adds

| Tool | What it does |
|---|---|
| `mail_folder_tree` | Every folder with path, total and unread counts |
| `mail_create_folder` | Create nested paths like `Finance/Banking` in one call |
| `mail_sender_stats` | Top senders and domains in a folder, the input for a plan |
| `mail_move_from_senders` | Bulk-move existing mail from addresses or `@domains` (JSON batch, 20 per request) |
| `mail_list_rules` / `mail_add_sender_rule` / `mail_delete_rule` | Server-side inbox rules so future mail files itself |
| `drive_list` / `drive_create_folder` / `drive_move` | OneDrive listing, nested folders, moves |

> **Teams is not covered.** Graph refuses Teams endpoints for personal accounts ("requires a valid license").

<br>

## 🟧 Setup

**1 · Entra app registration** (free, three minutes)

In the Azure portal create an app with *Supported account types = Personal Microsoft accounts only*, no redirect URI, and under *Authentication → Advanced settings* set **Allow public client flows = Yes**.
Delegated Graph permissions are requested at runtime: `Mail.ReadWrite` `MailboxSettings.ReadWrite` `Files.ReadWrite.All` `User.Read`.

**2 · Install**

```bash
pip install git+https://github.com/Denovarix/denovarix-m365-organizer
```

On Windows, enable long paths first if pip fails on deep package paths (admin PowerShell):

```powershell
Set-ItemProperty HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem LongPathsEnabled 1
```

**3 · Configure** `~/.m365-organizer/config.json` (see [`examples/config.example.json`](examples/config.example.json))

```json
{ "client_id": "YOUR-ENTRA-APP-CLIENT-ID", "tenant_id": "consumers" }
```

**4 · Sign in once** with the device-code flow. Tokens are cached in `~/.m365-organizer/token_cache.bin`.

```bash
m365-organizer auth
```

**5 · Add to Claude Code**

```bash
claude mcp add --scope user m365-organizer -- m365-organizer serve
```

<br>

## 🟧 Organise a mailbox from the command line

```bash
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

<br>

## 🟧 Layout

```
m365_organizer/graph.py    MSAL device-code auth, retry/backoff, paging, $batch
m365_organizer/mail.py     folders, sender stats, bulk move, inbox rules
m365_organizer/drive.py    OneDrive list / mkdir -p / move
m365_organizer/server.py   MCP server + `auth` / `serve` CLI
examples/                  config and plan examples, apply_plan.py
assets/                    brand assets (banner, social preview, icons)
```

<br>

<p align="center">
  <img src="assets/icon-dark.png#gh-dark-mode-only" width="72" alt="">
  <img src="assets/icon-light.png#gh-light-mode-only" width="72" alt="">
  <br>
  <sub>MIT · Built by <b>Denovarix Technologies LLP</b> with <b>Sourav De</b></sub>
</p>
