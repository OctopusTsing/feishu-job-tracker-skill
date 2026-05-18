# Feishu Job Tracker Skill

An AI-agent-friendly skill and CLI helper for tracking job applications in Feishu/Lark Base.

It helps users create a structured job-search tracker, add applications from natural language or JD text, detect duplicates, update statuses, and generate weekly reviews. It is designed for Chinese internship and campus hiring workflows, but the schema is easy to adapt.

## Agent Quickstart

If you are an AI coding agent reading this README, follow this sequence.

### 1. Identify The Runtime

- **Codex**: install the skill into `~/.codex/skills`.
- **Claude Code**: keep this folder available and read `CLAUDE.md`.
- **Gemini CLI**: keep this folder available and read `GEMINI.md`.
- **OpenClaw**: keep this folder available and read `OPENCLAW.md`.
- **Hermes**: keep this folder available and read `HERMES.md`.
- **Generic agent**: read `AGENTS.md` and `SKILL.md`.

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

## What It Does

- Creates a Feishu/Lark Base named `求职进度跟踪`.
- Creates a `投递记录` table with practical job-search fields.
- Adds job applications from structured JSON extracted by an AI agent.
- Searches for likely duplicate applications.
- Updates application status, next action, and next date.
- Lists records and produces a weekly review.
- Works with Codex, Claude Code, Gemini CLI, OpenClaw, Hermes, and generic shell-capable agents.

## Table Template

The built-in template includes:

- Company
- Role
- Job URL
- Source platform
- Job type
- Track
- City
- Work mode
- Application status
- Priority
- Fit score
- Risk signals
- Applied date
- Last updated
- Next action
- Next date
- Resume version
- Contact/HR
- JD summary
- JD text
- AI notes
- Interview prep
- Result reason

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

For Claude Code, Gemini CLI, OpenClaw, Hermes, or generic agents, point the agent at this folder and its runtime-specific entry file:

- `CLAUDE.md`
- `GEMINI.md`
- `OPENCLAW.md`
- `HERMES.md`
- `AGENTS.md`

The deterministic implementation is always:

```bash
python3 scripts/tracker.py <command>
```

## First-Time Initialization

The intended user experience is natural language:

```text
Use the Feishu Job Tracker skill and initialize my job application tracker.
```

The agent should run:

```bash
python3 scripts/tracker.py bootstrap --dry-run
python3 scripts/tracker.py bootstrap
```

`bootstrap` creates a new tracker if no local config exists. If a tracker is already configured, it repairs/completes the table template instead.

The user normally does not need to type the lower-level commands below. They are listed for transparency and debugging.

## Manual Quick Start

From this folder:

```bash
python3 scripts/tracker.py check
python3 scripts/tracker.py init-template --dry-run
python3 scripts/tracker.py init-template
```

The command creates a new Base and saves local config to:

```text
~/.feishu-job-tracker.json
```

If you already have a Base table:

```bash
python3 scripts/tracker.py configure --base-token <base_token> --table-id <table_id>
python3 scripts/tracker.py repair-template
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
  "risk_signals": ["实习时长过长"],
  "resume_version": "product_ai_v1.pdf",
  "jd_summary": "Work on AI product requirements, user feedback, and evaluation.",
  "ai_notes": "Prepare examples about AI product metrics and user feedback loops."
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
- `CLAUDE.md` for Claude Code
- `GEMINI.md` for Gemini CLI
- `OPENCLAW.md` for OpenClaw
- `HERMES.md` for Hermes
- `AGENTS.md` for generic agents

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
- Writes: `bot`

This matches the tested Lark CLI behavior for a Base created by the CLI app. You can override it:

```bash
FEISHU_JOB_TRACKER_READ_AS=user python3 scripts/tracker.py list-records
FEISHU_JOB_TRACKER_WRITE_AS=bot python3 scripts/tracker.py add-record --from-json application.json
```

Legacy override:

```bash
FEISHU_JOB_TRACKER_AS=user python3 scripts/tracker.py ...
```

### Ownership And Permissions

When a Base is created by a bot/app identity, the Feishu client may show the bot as the owner. The helper now uses the modern `lark-cli base +base-create` command for initialization, because bot-mode creation attempts to grant the current CLI user full access.

If a Base was created by an older version of this tool or by raw Bitable APIs, check the current user's permissions:

```bash
python3 scripts/tracker.py check-permissions
```

If the user only has view access, transfer ownership to the current Lark CLI user while keeping the bot/old owner with edit permission:

```bash
python3 scripts/tracker.py transfer-owner-to-user --dry-run
python3 scripts/tracker.py transfer-owner-to-user
```

Run the real transfer only after explicit user confirmation.

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
