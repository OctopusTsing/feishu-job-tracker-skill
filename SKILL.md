---
name: feishu-job-tracker
description: Create and maintain a Feishu/Lark Base job application tracker for Chinese internship and job search workflows. Use when the user wants to initialize a Feishu job tracking table, add a job application from natural language or JD text, update application status, detect duplicates, generate weekly application reviews, or operate Lark CLI/Feishu Bitable records for job-search tracking. Compatible with Codex, Claude Code, Gemini CLI, OpenClaw, Hermes, and other agents that can read Markdown instructions and run shell commands.
---

# Feishu Job Tracker

## Core Rule

Use the bundled script as the stable interface:

```bash
python3 scripts/tracker.py <command> [options]
```

Prefer `--dry-run` before any write. Show the user the proposed fields before creating or updating Feishu records.

## First-Time Setup (Read This Before Bootstrapping)

Two prerequisites MUST be satisfied before `bootstrap` or any write command will work.

### Step 1: Bind lark-cli to the agent workspace

lark-cli uses **separate config files per workspace**. The user's local terminal and the agent runtime each have their own app:

| Config file | Purpose |
| --- | --- |
| `~/.lark-cli/config.json` | User's local terminal sessions |
| `~/.lark-cli/<workspace>/config.json` | Agent (e.g. `hermes` workspace) |

**These are different apps with different credentials.** Do NOT copy `config.json` from one to the other — tables created by one app are inaccessible to the other (error 91403 Forbidden).

Bind the agent:

```bash
lark-cli config bind --source hermes --identity user-default
```

`user-default` is recommended over `bot-only` because bitable record writes require user identity. If using another agent runtime, replace `--source hermes` with the appropriate source label for that runtime.

### Step 2: Complete user authorization (single-shot, do not restart)

```bash
lark-cli auth login --recommend
```

This uses device-code flow. It prints a verification URL and blocks waiting for the user.

IMPORTANT: The device code is **single-use**. Every time you restart this command, the previous code is invalidated. Do NOT retry with a short timeout and re-launch. If your runtime doesn't support long-blocking, use:

```bash
lark-cli auth login --no-wait --json      # get device_code first
lark-cli auth login --device-code <code>   # resume polling
```

If the verification URL doesn't appear on stdout/stderr, your runtime probably needs PTY mode. Run with `pty=true` or in an interactive terminal.

Verify success:

```bash
lark-cli auth status
```

You should see `identity: user` with a non-empty `userOpenId` and `userName`.

### Step 3: Bootstrap the tracker

Only after step 2 succeeds:

```bash
python3 scripts/tracker.py bootstrap --dry-run
python3 scripts/tracker.py bootstrap
```

## Workflow

1. Check prerequisites:

```bash
python3 scripts/tracker.py check
```

2. Initialize a tracker:

```bash
python3 scripts/tracker.py bootstrap --dry-run
python3 scripts/tracker.py bootstrap
```

Lower-level initialization commands:

```bash
python3 scripts/tracker.py init-template --dry-run
python3 scripts/tracker.py init-template
```

Or attach an existing Feishu Base table:

```bash
python3 scripts/tracker.py configure --base-token <base_token> --table-id <table_id> --dry-run
python3 scripts/tracker.py configure --base-token <base_token> --table-id <table_id>
```

Repair/complete template fields when an existing table is missing columns:

```bash
python3 scripts/tracker.py repair-template --dry-run
python3 scripts/tracker.py repair-template
```

Check or fix document ownership/permissions:

```bash
python3 scripts/tracker.py check-permissions
python3 scripts/tracker.py transfer-owner-to-user --dry-run
python3 scripts/tracker.py transfer-owner-to-user
```

Use `transfer-owner-to-user` only after explicit user confirmation. It transfers the Base owner to the current Lark CLI user and keeps the previous owner with edit permission by default.

3. Add an application:

```bash
python3 scripts/tracker.py search-duplicates --from-json /path/to/application.json --dry-run
python3 scripts/tracker.py add-record --from-json /path/to/application.json --dry-run
python3 scripts/tracker.py add-record --from-json /path/to/application.json
python3 scripts/tracker.py delete-record --record-id <record_id>
```

4. Update a status:

```bash
python3 scripts/tracker.py update-status --company 腾讯 --role-keyword 产品 --status 一面 --next-date 2026-05-20 --next-action "参加一面" --dry-run
```

5. Generate a weekly review from exported/search results:

```bash
python3 scripts/tracker.py list-records > /tmp/records.json
python3 scripts/tracker.py weekly-review --records-json /path/to/records.json
```

## Natural Language Handling

When the user provides natural language, extract structured fields first. Do not write directly.

Minimum fields for a new record:

- `公司`
- `岗位名称`
- `投递状态`
- `最近更新时间`

Useful optional fields:

- `岗位链接`
- `平台来源`
- `岗位类型`
- `方向`
- `城市`
- `优先级`
- `匹配度`
- `投递日期`
- `下一步动作`
- `下一步日期`
- `工作模式`
- `简历版本`
- `联系人/HR`
- `JD 摘要`
- `JD 原文`
- `风险信号`
- `AI 备注`
- `结果原因`
- `备注`

Normalize status with:

```bash
python3 scripts/tracker.py normalize-status "腾讯那个产品实习进一面了"
```

## Troubleshooting

### "lark-cli is not bound to hermes" / auth_status shows binding error

Run:

```bash
lark-cli config bind --source hermes --identity user-default
```

Then complete user auth before proceeding.

### "need_user_authorization" after lark-cli config bind

User login hasn't been completed yet. Run `lark-cli auth login --recommend` (requires PTY or long timeout — see Step 2 above). Verify with `lark-cli auth status`.

### "API error: 91403 Forbidden" on write operations

Most common cause: **wrong app_id**. The user may be logged in under a different app (local `config.json`) than the one that created this table. Check:

```bash
lark-cli auth status          # shows current appId
cat ~/.feishu-job-tracker.json | python3 -c "import json,sys; c=json.load(sys.stdin); print(c.get('base_token'))"
```

If the app IDs differ, the table was created by a different app and the current one has no access. Fix by deleting `~/.feishu-job-tracker.json` and running `bootstrap` again to create a fresh table with the current app.

### "API error: 1063002 Permission denied" during transfer-owner-to-user

The bot app lacks `drive:permission.members.transfer_owner` scope or document management permission. Fastest fix: delete `~/.feishu-job-tracker.json` and re-run `bootstrap` to create a new table where the bot owns it and can manage it from the start.

### Auth URL doesn't appear / stuck waiting

Your runtime likely requires PTY mode. Try: `lark-cli auth login --recommend` in a PTY-enabled terminal. As an alternative: `lark-cli auth login --no-wait --json` to get a device code, then resume with `lark-cli auth login --device-code <code>`.

NEVER kill and re-launch `auth login --recommend` — each restart invalidates the previous device code, making the user's authorization URL useless.

### "No userOpenId found" after auth login

The auth login didn't complete. Check `lark-cli auth status` — if `identity` is still `bot` and `users` is `null`/empty, the user hasn't clicked confirm in the browser. Re-run auth login in a fresh long-running or PTY session.

### Diagnosing dual lark-cli configs

The most common root cause is two different apps. Compare the app used by the user's local CLI with the app used by the agent runtime:

```bash
python3 - <<'PY'
import json
from pathlib import Path

for label, path in [
    ("local", Path.home() / ".lark-cli" / "config.json"),
    ("agent", Path.home() / ".lark-cli" / "hermes" / "config.json"),
]:
    if path.exists():
        data = json.loads(path.read_text())
        print(label, data["apps"][0]["appId"])
    else:
        print(label, "missing", path)
PY
```

If they differ, that explains permission errors. The agent runtime app must be the one completing both bind and auth login.

## Safety

- Never invent company, role, interview time, salary, or HR contact details.
- Mark uncertain values as empty or `不确定`.
- Confirm before writing records.
- Search for likely duplicates before adding when the tracker is configured.
- If more than one existing record may match a status update, ask the user to choose.
- Do not store resume files or sensitive contact details unless the user explicitly asks.

## References

- Read `references/template-schema.json` for the canonical Feishu Base template.
- Read `references/lark-api.md` when debugging Lark CLI/OpenAPI calls.
- Read `references/compatibility.md` when adapting this skill to another AI agent runtime.
