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
- `工作模式`
- `优先级`
- `匹配度`
- `风险信号`
- `投递日期`
- `下一步动作`
- `下一步日期`
- `简历版本`
- `联系人/HR`
- `JD 摘要`
- `JD 原文`
- `AI 备注`
- `面试准备`
- `结果原因`

Normalize status with:

```bash
python3 scripts/tracker.py normalize-status "腾讯那个产品实习进一面了"
```

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
