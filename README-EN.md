# Feishu Job Tracker Skill

English | [中文](README.md)

Job seekers often apply to dozens of roles at once. Links are scattered across job boards, company sites, referrals, and chat messages; statuses live in a hand-maintained spreadsheet; a week later it is hard to remember what was submitted, what needs follow-up, and which roles are already in interview. This skill lets an AI agent turn the whole flow, from "I found a role" to "update my interview status" to "summarize this week", into a structured Feishu/Lark Base.

Users talk to their agent in natural language, and the agent calls `lark-cli` to create or update the user's job tracker. The default template is designed for Chinese internship and campus hiring workflows, but it can be adapted.

## Features

- 🧩 **One-command tracker setup**: creates a Feishu/Lark Base named `求职进度跟踪` with one clean `投递记录` table, so users do not need to design the schema from scratch.
- 📝 **Natural-language application logging**: users can say "I just applied to ByteDance AI Product Intern"; the agent extracts company, role, link, status, priority, and next action.
- 🔎 **Duplicate detection**: searches by job URL, company, and role title before writing, reducing confusion around whether a role was already saved.
- 🔄 **Status normalization**: maps phrases like "first interview", "OC", "offer", or "rejected" to standard statuses such as Applied, Written Test, AI Interview, First Interview, OC, Offer, Rejected.
- 📅 **Next-step tracking**: maintains next actions and next dates, such as "check feedback in 7 days" or "attend first interview next Wednesday".
- 📊 **Weekly review**: summarizes total applications, status distribution, active interviews, overdue tasks, and stale applications.
- 🛠️ **Preflight and repair**: checks `lark-cli`, user auth, Base permissions, and table fields, and can repair existing templates.
- 🤖 **Multi-agent compatibility**: Codex uses the standard skill entry; Claude Code, Gemini CLI, OpenClaw, Hermes, and generic shell-capable agents can read `SKILL.md`/`AGENTS.md`.

## How Users Talk To The Agent

Users can say things like:

```text
Use Feishu Job Tracker and initialize my job application tracker.
```

```text
I just applied to ByteDance AI Product Intern. The link is https://example.com/job/123. City is Shanghai. Mark it as applied. Note: referred by Alex.
```

```text
Check whether I already saved this role: Tencent Product Intern https://example.com/tencent-pm-intern
```

```text
Tencent Product Intern moved to first interview next Wednesday at 3pm. Please update it.
```

```text
Summarize my job search progress this week and tell me what needs follow-up.
```

## Agent Quickstart

If you are an AI coding agent reading this README, follow this sequence.

### 1. Identify The Runtime

- **Codex**: install the skill into `~/.codex/skills`.
- **Claude Code**: keep this folder available, read `CLAUDE.md`, then follow `SKILL.md`.
- **Gemini CLI / OpenClaw / Hermes / Generic agent**: keep this folder available and read `SKILL.md` plus `AGENTS.md`.

### 2. Install For Codex

From this repository root:

```bash
python3 scripts/install_skill.py --target codex
```

This symlinks the skill to:

```text
~/.codex/skills/feishu-job-tracker
```

Use copy mode if symlinks are not appropriate:

```bash
python3 scripts/install_skill.py --target codex --mode copy
```

After installing, ask the user to restart or refresh Codex so it discovers the skill.

### 3. Verify Dependencies

```bash
python3 scripts/tracker.py check
```

If `lark-cli` is missing or outdated, install/update it:

```bash
npm install -g @larksuite/cli
lark-cli auth login --recommend
```

### 4. Initialize The User's Tracker

When the user asks to initialize the tracker, run:

```bash
python3 scripts/tracker.py bootstrap --dry-run
python3 scripts/tracker.py bootstrap
```

`bootstrap` is idempotent: it creates a new tracker if none exists, or repairs/completes the configured template if one already exists.

### 5. Handle User Requests

Map natural language to deterministic commands:

| User intent | Agent action |
| --- | --- |
| "Set up my job tracker" | `python3 scripts/tracker.py bootstrap` |
| "I applied to this job" | Extract JSON -> `search-duplicates` -> `add-record` |
| "Did I already save this?" | `search-duplicates --from-json application.json` |
| "Tencent moved to first interview" | `normalize-status` -> find record -> `update-status` |
| "Summarize this week" | `list-records` -> `weekly-review` |
| "Remove this record" | `delete-record --record-id <record_id>` |

Always show a preview and ask for confirmation before writing records.

## First-Time Setup

Before initializing the tracker, lark-cli must be bound to the agent's workspace and authorized as a user.

### 1. Bind lark-cli to the agent workspace

lark-cli uses **separate config files per workspace** — the user's local terminal and the agent runtime each have their own app. **Do not copy config files between workspaces**; tables created by one app are inaccessible to the other (error 91403 Forbidden).

```bash
lark-cli config bind --source hermes --identity user-default
```

For other agent runtimes, replace `--source hermes` with the appropriate value.

### 2. Complete user authorization

```bash
lark-cli auth login --recommend
```

This uses device-code flow. It prints a verification URL and blocks until the user confirms in the browser.

**IMPORTANT:** The device code is **single-use**. Do NOT restart this command — each restart invalidates the previous code. If your runtime doesn't support long-blocking, use:

```bash
lark-cli auth login --no-wait --json                  # get device_code
lark-cli auth login --device-code <code_from_above>   # resume polling
```

Verify with `lark-cli auth status` — you should see `identity: user` with a non-empty `userOpenId`.

### 3. Verify and initialize

```bash
python3 scripts/tracker.py pre-check      # comprehensive pre-flight diagnostics
python3 scripts/tracker.py quickstart     # step-by-step setup guide
python3 scripts/tracker.py bootstrap --dry-run
python3 scripts/tracker.py bootstrap
```

Or ask the agent directly: "Use the Feishu Job Tracker skill and initialize my job application tracker."

## New Commands

| Command | Description |
| --- | --- |
| `pre-check` | Comprehensive pre-flight diagnostics before bootstrap or any write |
| `quickstart` | Prints a step-by-step setup guide with copy-paste commands |

## Table Template

Required fields:

- Company
- Role
- Application status
- Last updated: filled automatically by the script; users usually do not need to enter it manually

Default field order:

- Company
- Role
- Application status
- Job URL
- Source platform
- Job type
- Track
- City
- Priority
- Fit score
- Applied date
- Last updated
- Next action
- Next date
- Work mode
- Resume version
- Contact/HR
- JD summary
- JD text
- Risk signals
- AI notes
- Result reason
- Notes

See [`references/template-schema.json`](references/template-schema.json) for the canonical schema.

## Requirements

- Python 3.9+
- [`lark-cli`](https://github.com/larksuite/cli) 1.0.32 or newer
- A Feishu/Lark account authorized in `lark-cli`

Install/update Lark CLI:

```bash
npm install -g @larksuite/cli
lark-cli auth login --recommend
```

Verify:

```bash
lark-cli --version
lark-cli auth status
```

## Install The Skill

For Codex, install the skill with:

```bash
python3 scripts/install_skill.py --target codex
```

This creates a symlink at:

```text
~/.codex/skills/feishu-job-tracker
```

Use `--mode copy` if you prefer copying instead of symlinking:

```bash
python3 scripts/install_skill.py --target codex --mode copy
```

For Claude Code, Gemini CLI, OpenClaw, Hermes, or generic agents, point the agent at this folder and the shared entry files:

- `CLAUDE.md`
- `AGENTS.md`
- `SKILL.md`

The deterministic implementation is always:

```bash
python3 scripts/tracker.py <command>
```

## Common Usage

### Add an application

Create `application.json`:

```json
{
  "company": "ByteDance",
  "role": "AI Product Intern",
  "job_url": "https://example.com/job/123",
  "source": "公司官网",
  "job_type": "日常实习",
  "track": "产品",
  "city": "上海",
  "status": "已投递",
  "priority": "高",
  "fit_score": 86,
  "work_mode": "混合",
  "risk_signals": ["实习时长过长"],
  "resume_version": "product_ai_v1.pdf",
  "jd_summary": "Work on AI product requirements, user feedback, and evaluation.",
  "ai_notes": "Prepare examples about AI product metrics and user feedback loops.",
  "user_notes": "User-owned freeform notes, such as referral info or personal thoughts."
}
```

Preview duplicate search:

```bash
python3 scripts/tracker.py search-duplicates --from-json application.json
```

Add the record:

```bash
python3 scripts/tracker.py add-record --from-json application.json
```

### Update a status

When an AI agent hears:

```text
Tencent product intern moved to first interview next Wednesday.
```

It should normalize the status and update the selected record:

```bash
python3 scripts/tracker.py normalize-status "Tencent product intern moved to first interview"
python3 scripts/tracker.py update-status \
  --record-id <record_id> \
  --company 腾讯 \
  --role-keyword 产品 \
  --status 一面 \
  --next-date 2026-05-20 \
  --next-action "参加一面"
```

If the record is not selected yet, run a dry-run first and ask the user to choose:

```bash
python3 scripts/tracker.py update-status --company 腾讯 --role-keyword 产品 --status 一面 --dry-run
```

### Weekly review

```bash
python3 scripts/tracker.py list-records > /tmp/job-records.json
python3 scripts/tracker.py weekly-review --records-json /tmp/job-records.json
```

### Delete a record

```bash
python3 scripts/tracker.py delete-record --record-id <record_id>
```

## AI Agent Integration

This repository is intentionally runtime-neutral.

Agent entry files:

- `SKILL.md` for Codex and general skill loaders
- `CLAUDE.md` as a thin Claude Code entrypoint that points back to `SKILL.md`
- `AGENTS.md` for generic agent rules; use it with `SKILL.md` for Gemini CLI, OpenClaw, Hermes, and other shell-capable agents

All agents should delegate deterministic operations to:

```bash
python3 scripts/tracker.py <command>
```

Recommended interaction pattern:

1. Extract structured fields from user text or JD.
2. Search for duplicates.
3. Show a write preview.
4. Ask the user to confirm.
5. Write to Feishu/Lark Base.

## Identity Model

The helper defaults to:

- Reads: `user`
- Writes: `auto` (tries `user` first, falls back to `bot` if no user is logged in)

The `auto` mode checks `lark-cli auth status` at runtime and picks the appropriate identity automatically. You can override it with environment variables:

```bash
FEISHU_JOB_TRACKER_WRITE_AS=user python3 scripts/tracker.py add-record --from-json application.json
FEISHU_JOB_TRACKER_WRITE_AS=bot python3 scripts/tracker.py add-record --from-json application.json
```

Legacy override:

```bash
FEISHU_JOB_TRACKER_AS=user python3 scripts/tracker.py ...
```

### Workspace-Scoped lark-cli Config

lark-cli uses **separate config files per workspace** — the user's local terminal and the agent runtime each have their own app with different credentials. **Tables created by one app are inaccessible to the other** (error 91403 Forbidden).

Do NOT copy `config.json` between workspaces. Always use the app bound to the agent's workspace. If you hit permission errors, run:

```bash
python3 scripts/tracker.py pre-check
```

to diagnose app ID mismatches and auth issues.

## Tested Flow

The following full flow has been tested against a real Feishu Base:

- `check`
- `init-template`
- default table cleanup
- `repair-template`
- `add-record`
- `search-duplicates`
- `normalize-status`
- `update-status`
- `list-records`
- `weekly-review`
- `delete-record`

The test record was deleted after verification.

## Privacy And Safety

- This tool does not scrape job boards.
- It only writes data the user or agent explicitly provides.
- It does not store resume files by default.
- It stores only local Base configuration in `~/.feishu-job-tracker.json`.
- Agents should ask for confirmation before writes.

## License

MIT. See [`LICENSE`](LICENSE).

## Troubleshooting

Check auth:

```bash
lark-cli auth status
lark-cli auth scopes | rg 'base:record|bitable:app'
```

Update CLI:

```bash
npm install -g @larksuite/cli
lark-cli auth login --recommend
```

If record reads fail on old `bitable/v1` APIs, use the modern Base commands:

```bash
lark-cli base +record-list --base-token <base_token> --table-id <table_id> --format json --as user
lark-cli base +record-search --base-token <base_token> --table-id <table_id> --json '{"keyword":"腾讯","search_fields":["公司"],"limit":20}' --format json --as user
```

If writes fail as `user`, use the default `bot` write identity or set:

```bash
FEISHU_JOB_TRACKER_WRITE_AS=bot
```
