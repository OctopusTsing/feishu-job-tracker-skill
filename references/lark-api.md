# Lark CLI And Feishu Base Notes

## App and Workspace Model

lark-cli uses **separate config files per workspace**:

| Config file | Purpose |
| --- | --- |
| `~/.lark-cli/config.json` | Local (user's terminal) sessions |
| `~/.lark-cli/<workspace>/config.json` | Agent workspace (e.g. `hermes`) |

Each workspace has its own **appId**. Tables created by one app are NOT accessible by another (error 91403 Forbidden). Always use the app that's bound to the agent's workspace for all operations.

## User Authorization (Device Code Flow)

`lark-cli` supports two auth flows:

### Blocking mode (recommended for interactive terminals)

```bash
lark-cli auth login --recommend
```

Prints a verification URL and blocks until the user completes authorization in the browser.
Requires PTY/interactive terminal for the URL to appear on stdout.

### Non-blocking mode (for scripts / background agents)

```bash
# Step A: Get the device code without blocking
lark-cli auth login --no-wait --json
# Returns: {"device_code": "...", "verification_url": "...", ...}

# Step B: Give user the URL, then poll with the device code
lark-cli auth login --device-code "<device_code>"
```

IMPORTANT: Device codes are **single-use**. Every time you restart `auth login`, the previous code is invalidated. Never retry with a short timeout and re-launch — the user's URL becomes useless.

## Checking Auth Status

```bash
lark-cli auth status
```

Key fields in the output:

| Field | Meaning |
| --- | --- |
| `appId` | Which Feishu app is configured |
| `identity` | Current identity context (`user` or `bot`) |
| `userOpenId` | Logged-in user's Open ID (null = no user logged in) |
| `userName` | Display name of the logged-in user |
| `tokenStatus` | `valid` means the access token is usable |

## Document Permission Model

- **Bot-created tables**: The bot app is the owner. User accounts can read but not write until ownership is transferred.
- **User identity writes**: Require the user to be either the owner or a collaborator with edit permission.
- If the bot app created the table and the agent only has bot credentials, writes will fail with `91403 Forbidden`.
- The `transfer-owner-to-user` script command transfers ownership from the bot to the current logged-in user. If it fails with `1063002 Permission denied`, the bot app lacks document-scoped permissions — the fastest fix is to create a new table.

## Identity Resolution

The tracker script defaults `WRITE_IDENTITY` to `auto`:
1. Checks if a user is logged in (`lark-cli auth status` has `userOpenId`)
2. If yes, uses `--as user` for writes
3. If no, falls back to `--as bot`

Override with env vars: `FEISHU_JOB_TRACKER_WRITE_AS=user` or `FEISHU_JOB_TRACKER_WRITE_AS=bot`.

## API Endpoints And Commands

Use `lark-cli` as the execution layer when available. Prefer the modern `base` command group for record reads/searches:

```bash
lark-cli base +record-list --base-token <base_token> --table-id <table_id> --format json --as user
lark-cli base +record-search --base-token <base_token> --table-id <table_id> --json '{"keyword":"腾讯","search_fields":["公司"],"limit":20}' --format json --as user
```

The skill script still calls raw OpenAPI for operations that are stable there:

```bash
lark-cli api METHOD /open-apis/... --data '{"json":"body"}' --format json
```

Important concepts:

- A Feishu/Lark Base is called an `app` in older Bitable v1 APIs.
- `app_token` and `base_token` often refer to the token visible in `/base/<token>` or `/bitable/<token>` URLs.
- `table_id` identifies the data table inside the Base.
- Writing to an existing Base may require adding the app as a document application/collaborator with edit permission.

Common endpoints/commands used by the script:

| Operation | Endpoint |
| --- | --- |
| Create Base | `POST /open-apis/bitable/v1/apps` |
| Batch create tables | `POST /open-apis/bitable/v1/apps/{app_token}/tables/batch_create` |
| List tables | `GET /open-apis/bitable/v1/apps/{app_token}/tables` |
| List fields | `GET /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields` |
| Create field | `POST /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields` |
| Create record | `POST /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records` |
| List records | `lark-cli base +record-list` |
| Search records | `lark-cli base +record-search` |
| Update record | `PUT /open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}` |

If a shortcut command exists in the installed CLI, it is fine to use it. Prefer the script interface for repeatability.
