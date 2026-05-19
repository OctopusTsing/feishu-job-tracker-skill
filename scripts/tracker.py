#!/usr/bin/env python3
import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import date, datetime, timedelta
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "references" / "template-schema.json"
DEFAULT_CONFIG = Path(os.environ.get("FEISHU_JOB_TRACKER_CONFIG", Path.home() / ".feishu-job-tracker.json"))
READ_IDENTITY = os.environ.get("FEISHU_JOB_TRACKER_READ_AS", os.environ.get("FEISHU_JOB_TRACKER_AS", "user"))
WRITE_IDENTITY = os.environ.get("FEISHU_JOB_TRACKER_WRITE_AS", os.environ.get("FEISHU_JOB_TRACKER_AS_WRITE", "auto"))

FIELD_TYPES = {
    "text": 1,
    "long_text": 1,
    "number": 2,
    "single_select": 3,
    "multi_select": 4,
    "date": 5,
    "url": 15,
}

ENDED_STATUSES = {"Offer", "拒绝", "放弃"}
ACTIVE_INTERVIEW_STATUSES = {"AI 面试", "一面", "二面", "HR 面"}

STATUS_ALIASES = [
    ("Offer", ["offer", "录了", "拿到offer", "拿到 offer"]),
    ("OC", ["oc", "口头offer", "口头 offer", "口头录用"]),
    ("拒绝", ["挂了", "拒了", "没过", "fail", "失败", "不通过"]),
    ("放弃", ["放弃", "不去了", "不投了", "撤回"]),
    ("HR 面", ["hr面", "hr 面", "谈薪", "hr"]),
    ("二面", ["二面", "复面", "第二轮"]),
    ("一面", ["一面", "初面", "第一轮", "业务面"]),
    ("AI 面试", ["ai面", "ai 面", "机器面", "视频测评"]),
    ("测评/笔试", ["笔试", "测评", "在线测试", "测验"]),
    ("已投递", ["投了", "已投", "提交", "投递了", "投递完成"]),
    ("准备投递", ["准备投", "待投", "想投"]),
    ("无响应", ["无响应", "没消息", "没反馈"]),
]

KEY_TO_FIELD = {}


def load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def load_config(path=DEFAULT_CONFIG):
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8").strip()
    if not text:
        return {}
    return json.loads(text)


def save_config(config, path=DEFAULT_CONFIG):
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_json(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def die(message, code=1):
    print(message, file=sys.stderr)
    raise SystemExit(code)


def today_iso():
    return date.today().isoformat()


def date_to_ms(value):
    if not value:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            dt = datetime.fromisoformat(value[:10])
        return int(dt.timestamp() * 1000)
    return value


def normalize_status_text(text):
    lowered = text.lower()
    for status, aliases in STATUS_ALIASES:
        if any(alias.lower() in lowered for alias in aliases):
            return status
    return "待评估"


def field_name_map(schema):
    return {field["key"]: field["name"] for field in schema["fields"]}


def field_def_for_api(field):
    api = {
        "field_name": field["name"],
        "type": FIELD_TYPES[field["type"]],
    }
    if field["type"] in {"single_select", "multi_select"}:
        api["property"] = {
            "options": [{"name": option} for option in field.get("options", [])]
        }
    return api


def coerce_record(input_record, schema):
    names = field_name_map(schema)
    status = input_record.get("status") or input_record.get("投递状态")
    if not status:
        status = normalize_status_text(json.dumps(input_record, ensure_ascii=False))

    record = dict(input_record)
    record.setdefault("status", status)
    record.setdefault("updated_at", today_iso())

    if record["status"] not in {"待评估", "准备投递"}:
        record.setdefault("applied_date", today_iso())
    if not record.get("next_action") and record["status"] == "已投递":
        days = int(schema.get("default_followup_days", 7))
        record["next_action"] = f"{days} 天后检查是否有反馈"
        record.setdefault("next_date", (date.today() + timedelta(days=days)).isoformat())

    fields = {}
    for field in schema["fields"]:
        key = field["key"]
        name = names[key]
        value = record.get(key, record.get(name))
        if value in (None, ""):
            continue
        if field["type"] == "date":
            value = date_to_ms(value)
        if field["type"] == "url" and isinstance(value, str):
            value = {"link": value, "text": value}
        fields[name] = value

    missing = []
    for field in schema["fields"]:
        if field.get("required") and field["name"] not in fields:
            missing.append(field["name"])

    return fields, missing


def base_cell_value(value):
    if isinstance(value, dict) and "link" in value:
        return value["link"]
    return value


def base_row_body(fields):
    names = list(fields.keys())
    values = [base_cell_value(fields[name]) for name in names]
    return {"fields": names, "rows": [values]}


def lark_cli_available():
    return shutil.which("lark-cli") or shutil.which("feishu-cli")


def lark_bin():
    return shutil.which("lark-cli") or shutil.which("feishu-cli") or "lark-cli"


def resolve_write_identity():
    """Resolve 'auto' identity: try user first, fall back to bot."""
    identity = WRITE_IDENTITY
    if identity != "auto":
        return identity
    try:
        completed = subprocess.run([lark_bin(), "auth", "status"], text=True, capture_output=True, timeout=15)
        if completed.returncode == 0:
            status = json.loads(completed.stdout)
            if status.get("userOpenId"):
                return "user"
    except Exception:
        pass
    return "bot"


def run_lark_api(method, endpoint, data=None, dry_run=False, identity=None):
    cmd = [lark_bin(), "api", method, endpoint, "--format", "json"]
    if identity is None and method == "GET":
        identity = READ_IDENTITY
    elif not identity:
        identity = resolve_write_identity()
    if identity:
        cmd += ["--as", identity]
    if data is not None:
        cmd += ["--data", json.dumps(data, ensure_ascii=False)]
    if dry_run:
        return {"dry_run": True, "command": cmd, "data": data}
    completed = subprocess.run(cmd, text=True, capture_output=True)
    if completed.returncode != 0:
        die(completed.stderr.strip() or completed.stdout.strip() or f"lark-cli failed: {' '.join(cmd)}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"raw": completed.stdout}


def run_lark_base(args, dry_run=False, identity=None, output_format=True):
    cmd = [lark_bin(), "base"] + args
    if output_format:
        cmd += ["--format", "json"]
    if identity:
        if identity == "auto":
            identity = resolve_write_identity()
        cmd += ["--as", identity]
    if dry_run:
        cmd.append("--dry-run")
        return {"dry_run": True, "command": cmd}
    completed = subprocess.run(cmd, text=True, capture_output=True)
    if completed.returncode != 0:
        die(completed.stderr.strip() or completed.stdout.strip() or f"lark-cli failed: {' '.join(cmd)}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"raw": completed.stdout}


def run_lark_command(args, dry_run=False):
    cmd = [lark_bin()] + args
    if dry_run:
        cmd.append("--dry-run")
        return {"dry_run": True, "command": cmd}
    completed = subprocess.run(cmd, text=True, capture_output=True)
    if completed.returncode != 0:
        die(completed.stderr.strip() or completed.stdout.strip() or f"lark-cli failed: {' '.join(cmd)}")
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"raw": completed.stdout}


def current_user_open_id():
    completed = subprocess.run([lark_bin(), "auth", "status"], text=True, capture_output=True)
    if completed.returncode != 0:
        die(completed.stderr.strip() or completed.stdout.strip() or "Could not read lark-cli auth status.")
    status = json.loads(completed.stdout)
    open_id = status.get("userOpenId")
    if not open_id:
        die("No userOpenId found. Run `lark-cli auth login --recommend` first.")
    return open_id


def response_items(result):
    data = result.get("data", {}) if isinstance(result, dict) else {}
    return data.get("items") or data.get("fields") or []


def ensure_fields(app_token, table_id, schema, dry_run=False):
    list_result = run_lark_api(
        "GET",
        f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
        dry_run=dry_run,
    )
    existing = response_items(list_result) if not dry_run else []
    existing_by_name = {field.get("field_name"): field for field in existing}
    operations = []

    company_field = next(field for field in schema["fields"] if field["key"] == "company")
    if "公司" not in existing_by_name:
        primary = next((field for field in existing if field.get("is_primary")), None)
        if primary:
            operations.append(run_lark_api(
                "PUT",
                f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields/{primary['field_id']}",
                field_def_for_api(company_field),
                dry_run=dry_run,
            ))
            existing_by_name["公司"] = {"field_name": "公司"}
        else:
            operations.append(run_lark_api(
                "POST",
                f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
                field_def_for_api(company_field),
                dry_run=dry_run,
            ))
            existing_by_name["公司"] = {"field_name": "公司"}

    for field in schema["fields"]:
        if field["name"] in existing_by_name:
            continue
        operations.append(run_lark_api(
            "POST",
            f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
            field_def_for_api(field),
            dry_run=dry_run,
        ))
        existing_by_name[field["name"]] = {"field_name": field["name"]}

    final_list = run_lark_api(
        "GET",
        f"/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/fields",
        dry_run=dry_run,
    )
    return {
        "initial_fields": existing,
        "operations": operations,
        "final_fields": response_items(final_list) if not dry_run else final_list,
    }


def list_tables(app_token, dry_run=False):
    return run_lark_base(
        ["+table-list", "--base-token", app_token],
        dry_run=dry_run,
        identity=READ_IDENTITY,
        output_format=False,
    )


def cleanup_default_tables(app_token, keep_table_id, keep_table_name, dry_run=False):
    table_result = list_tables(app_token, dry_run=dry_run)
    tables = table_result.get("data", {}).get("tables", []) if not dry_run else []
    operations = []
    if dry_run:
        operations.append(run_lark_base(
            [
                "+table-delete",
                "--base-token", app_token,
                "--table-id", "<default_table_id_not_named_" + keep_table_name + ">",
                "--yes",
            ],
            dry_run=True,
            identity=WRITE_IDENTITY,
            output_format=False,
        ))
        return {"tables": table_result, "operations": operations}

    for table in tables:
        table_id = table.get("id") or table.get("table_id")
        table_name = table.get("name")
        if table_id == keep_table_id or table_name == keep_table_name:
            continue
        if table_name in {"数据表", "Table", "Table 1", "Grid"}:
            operations.append(run_lark_base(
                [
                    "+table-delete",
                    "--base-token", app_token,
                    "--table-id", table_id,
                    "--yes",
                ],
                dry_run=False,
                identity=WRITE_IDENTITY,
                output_format=False,
            ))
    return {"tables": table_result, "operations": operations}


def cmd_pre_check(_args):
    """Comprehensive pre-flight check before bootstrap or any write operation."""
    issues = []
    warnings = []
    result = {
        "steps": {},
        "ready": True,
        "issues": [],
        "warnings": [],
    }

    # 1. lark-cli available
    cli_path = lark_cli_available()
    result["steps"]["lark_cli"] = {"available": bool(cli_path), "path": cli_path}
    if not cli_path:
        issues.append("lark-cli not found in PATH. Install it first.")
        write_json(result)
        return

    # 2. Auth status — check app_id, identity, user login
    try:
        auth = subprocess.run([lark_bin(), "auth", "status"], text=True, capture_output=True, timeout=15)
        if auth.returncode != 0:
            issues.append(f"lark-cli auth status failed (exit {auth.returncode}): {auth.stderr.strip()}")
            write_json(result)
            return
        auth_data = json.loads(auth.stdout)
    except Exception as exc:
        issues.append(f"Cannot read auth status: {exc}")
        write_json(result)
        return

    result["steps"]["auth"] = {
        "app_id": auth_data.get("appId"),
        "identity": auth_data.get("identity"),
        "user_name": auth_data.get("userName"),
        "user_open_id": auth_data.get("userOpenId"),
        "token_status": auth_data.get("tokenStatus"),
    }

    if auth_data.get("identity") == "bot" and not auth_data.get("userOpenId"):
        issues.append(
            "Only bot identity available, no user logged in. "
            "Run: lark-cli auth login --recommend (requires PTY/interactive terminal) — see SKILL.md Step 2."
        )

    # 3. Config file consistency (if exists)
    config = load_config()
    if config.get("base_token"):
        result["steps"]["config"] = {"exists": True, "base_token": config["base_token"], "table_id": config.get("table_id")}

        # Test write access with a minimal record
        try:
            test_result = subprocess.run(
                [
                    lark_bin(), "api", "GET",
                    f"/open-apis/bitable/v1/apps/{config['base_token']}/tables/{config.get('table_id', '')}/fields",
                    "--format", "json", "--as", "user",
                ],
                text=True, capture_output=True, timeout=30,
            )
            if test_result.returncode != 0 or "Forbidden" in test_result.stdout:
                issues.append(
                    f"User cannot access table {config.get('base_token')}/{config.get('table_id')}. "
                    "The table was likely created by a different lark-cli app. "
                    "Fix: delete ~/.feishu-job-tracker.json and run `tracker.py bootstrap` again."
                )
            else:
                result["steps"]["write_access"] = "OK (user can read table fields)"
        except Exception as exc:
            warnings.append(f"Could not test write access: {exc}")

    result["ready"] = len(issues) == 0
    result["issues"] = issues
    result["warnings"] = warnings
    write_json(result)
    if issues:
        raise SystemExit(1)


def cmd_check(_args):
    config = load_config()
    result = {
        "skill_root": str(ROOT),
        "schema": str(SCHEMA_PATH),
        "config_path": str(DEFAULT_CONFIG),
        "config_exists": DEFAULT_CONFIG.exists(),
        "lark_cli": lark_cli_available(),
        "configured_base": bool(config.get("base_token") and config.get("table_id")),
    }
    if result["lark_cli"]:
        try:
            status = subprocess.run([lark_bin(), "auth", "status"], text=True, capture_output=True, timeout=15)
            result["auth_status_code"] = status.returncode
            result["auth_status"] = (status.stdout or status.stderr).strip()
        except Exception as exc:
            result["auth_status_error"] = str(exc)
    write_json(result)


def cmd_bootstrap(args):
    config = load_config()
    if config.get("base_token") and config.get("table_id"):
        result = {
            "mode": "repair-template",
            "message": "Existing tracker config found; ensuring template fields are present.",
            "result": ensure_fields(config["base_token"], config["table_id"], load_schema(), dry_run=args.dry_run),
            "config_path": str(DEFAULT_CONFIG),
        }
        write_json(result)
        return

    init_args = argparse.Namespace(
        name=args.name,
        timezone=args.timezone,
        dry_run=args.dry_run,
    )
    cmd_init_template(init_args)


def cmd_schema(args):
    schema = load_schema()
    if args.api_fields:
        write_json([field_def_for_api(field) for field in schema["fields"]])
    else:
        write_json(schema)


def cmd_normalize_status(args):
    write_json({"input": args.text, "status": normalize_status_text(args.text)})


def cmd_init_template(args):
    schema = load_schema()
    dry_run = args.dry_run
    config = load_config()
    base_name = args.name or schema["base_name"]

    base_result = run_lark_base(
        [
            "+base-create",
            "--name", base_name,
            "--time-zone", args.timezone or schema["timezone"],
        ],
        dry_run=dry_run,
        identity=WRITE_IDENTITY,
        output_format=False,
    )

    if dry_run:
        app_token = "<app_token_from_create_base>"
        default_table_id = "<default_table_id_from_create_base>"
    else:
        data = base_result.get("data", {})
        app = data.get("app", {}) or data.get("base", {})
        app_token = app.get("app_token") or app.get("base_token") or data.get("app_token") or data.get("base_token")
        default_table_id = app.get("default_table_id") or data.get("default_table_id")
        if not app_token:
            die(f"Could not find app_token in response: {json.dumps(base_result, ensure_ascii=False)}")

    table_body = {
        "tables": [
            {
                "name": schema["table_name"],
                "default_view_name": "全部投递",
                "fields": [field_def_for_api(field) for field in schema["fields"]],
            }
        ]
    }
    table_endpoint = f"/open-apis/bitable/v1/apps/{app_token}/tables/batch_create"
    table_result = run_lark_api("POST", table_endpoint, table_body, dry_run=dry_run)

    table_id = "<table_id_from_batch_create>"
    if not dry_run:
        data = table_result.get("data", {})
        tables = data.get("tables") or data.get("table_ids") or []
        first = tables[0] if tables else {}
        table_id = first.get("table_id") if isinstance(first, dict) else first
        if not table_id:
            die(f"Could not find table_id in response: {json.dumps(table_result, ensure_ascii=False)}")

    fields_result = ensure_fields(app_token, table_id, schema, dry_run=dry_run)
    cleanup_result = cleanup_default_tables(app_token, table_id, schema["table_name"], dry_run=dry_run)

    new_config = {
        **config,
        "tracker_name": base_name,
        "base_token": app_token,
        "app_token": app_token,
        "table_id": table_id,
        "template_version": schema["template_version"],
        "field_map": field_name_map(schema),
        "timezone": args.timezone or schema["timezone"],
        "default_followup_days": schema.get("default_followup_days", 7),
    }
    if not dry_run:
        save_config(new_config)

    write_json({
        "base": base_result,
        "table": table_result,
        "fields": fields_result,
        "cleanup_default_table": cleanup_result,
        "config": new_config,
        "saved": not dry_run,
        "config_path": str(DEFAULT_CONFIG),
    })


def cmd_add_record(args):
    schema = load_schema()
    config = load_config()
    if not args.dry_run and not (config.get("base_token") and config.get("table_id")):
        die("Tracker is not configured. Run init-template first or create config with base_token and table_id.")
    input_record = json.loads(Path(args.from_json).read_text(encoding="utf-8"))
    fields, missing = coerce_record(input_record, schema)
    if missing:
        die("Missing required fields: " + ", ".join(missing))

    app_token = config.get("base_token", "<base_token>")
    table_id = config.get("table_id", "<table_id>")
    body = base_row_body(fields)
    result = run_lark_base(
        [
            "+record-batch-create",
            "--base-token", app_token,
            "--table-id", table_id,
            "--json", json.dumps(body, ensure_ascii=False),
        ],
        dry_run=args.dry_run,
        identity=WRITE_IDENTITY,
        output_format=False,
    )
    write_json({"record": body, "result": result})


def cmd_configure(args):
    schema = load_schema()
    config = load_config()
    config.update({
        "tracker_name": args.name or config.get("tracker_name") or schema["base_name"],
        "base_token": args.base_token,
        "app_token": args.base_token,
        "table_id": args.table_id,
        "template_version": schema["template_version"],
        "field_map": field_name_map(schema),
        "timezone": args.timezone or config.get("timezone") or schema["timezone"],
        "default_followup_days": schema.get("default_followup_days", 7),
    })
    if not args.dry_run:
        save_config(config)
    write_json({"config": config, "saved": not args.dry_run, "config_path": str(DEFAULT_CONFIG)})


def cmd_repair_template(args):
    schema = load_schema()
    config = load_config()
    app_token = args.base_token or config.get("base_token")
    table_id = args.table_id or config.get("table_id")
    if not app_token or not table_id:
        die("Missing base_token/table_id. Pass --base-token and --table-id or run configure/init-template first.")
    result = ensure_fields(app_token, table_id, schema, dry_run=args.dry_run)
    write_json(result)


def cmd_check_permissions(args):
    config = load_config()
    app_token = args.base_token or config.get("base_token")
    if not app_token:
        die("Missing base_token. Pass --base-token or run configure/init-template first.")
    checks = {}
    for action in ["view", "edit", "share", "manage_public"]:
        result = run_lark_command([
            "drive", "permission.members", "auth",
            "--params", json.dumps({"token": app_token, "type": "bitable", "action": action}, ensure_ascii=False),
            "--as", args.identity,
        ], dry_run=args.dry_run)
        checks[action] = result
    write_json({"base_token": app_token, "identity": args.identity, "checks": checks})


def cmd_transfer_owner_to_user(args):
    config = load_config()
    app_token = args.base_token or config.get("base_token")
    if not app_token:
        die("Missing base_token. Pass --base-token or run configure/init-template first.")
    open_id = args.user_open_id or current_user_open_id()
    params = {
        "token": app_token,
        "type": "bitable",
        "need_notification": args.need_notification,
        "remove_old_owner": False,
        "old_owner_perm": args.old_owner_perm,
        "stay_put": True,
    }
    data = {
        "member_id": open_id,
        "member_type": "openid",
    }
    result = run_lark_command([
        "drive", "permission.members", "transfer_owner",
        "--params", json.dumps(params, ensure_ascii=False),
        "--data", json.dumps(data, ensure_ascii=False),
        "--as", WRITE_IDENTITY,
        "--yes",
    ], dry_run=args.dry_run)
    write_json({"base_token": app_token, "new_owner_open_id": open_id, "result": result})


def cmd_search_duplicates(args):
    schema = load_schema()
    config = load_config()
    input_record = json.loads(Path(args.from_json).read_text(encoding="utf-8"))
    company = input_record.get("company") or input_record.get("公司")
    role = input_record.get("role") or input_record.get("岗位名称")
    job_url = input_record.get("job_url") or input_record.get("岗位链接")
    searches = []
    if job_url:
        searches.append({"keyword": job_url, "search_fields": ["岗位链接"], "limit": args.page_size})
    if company:
        searches.append({"keyword": company, "search_fields": ["公司"], "limit": args.page_size})
    if role:
        searches.append({"keyword": role, "search_fields": ["岗位名称"], "limit": args.page_size})
    app_token = config.get("base_token", "<base_token>")
    table_id = config.get("table_id", "<table_id>")
    results = []
    for search in searches:
        results.append(run_lark_base(
            [
                "+record-search",
                "--base-token", app_token,
                "--table-id", table_id,
                "--json", json.dumps(search, ensure_ascii=False),
            ],
            dry_run=args.dry_run or not (config.get("base_token") and config.get("table_id")),
            identity=READ_IDENTITY,
        ))
    write_json({"queries": searches, "results": results})


def cmd_delete_record(args):
    config = load_config()
    app_token = args.base_token or config.get("base_token")
    table_id = args.table_id or config.get("table_id")
    if not app_token or not table_id:
        die("Missing base_token/table_id. Pass --base-token and --table-id or run configure/init-template first.")
    result = run_lark_base(
        [
            "+record-delete",
            "--base-token", app_token,
            "--table-id", table_id,
            "--record-id", args.record_id,
            "--yes",
        ],
        dry_run=args.dry_run,
        identity=WRITE_IDENTITY,
        output_format=False,
    )
    write_json({"record_id": args.record_id, "result": result})


def cmd_list_records(args):
    config = load_config()
    app_token = args.base_token or config.get("base_token")
    table_id = args.table_id or config.get("table_id")
    if not app_token or not table_id:
        die("Missing base_token/table_id. Pass --base-token and --table-id or run configure/init-template first.")
    result = run_lark_base(
        [
            "+record-list",
            "--base-token", app_token,
            "--table-id", table_id,
            "--limit", str(args.limit),
        ],
        dry_run=args.dry_run,
        identity=READ_IDENTITY,
    )
    write_json(result)


def cmd_update_status(args):
    schema = load_schema()
    config = load_config()
    status = normalize_status_text(args.status)
    if args.status in [field for field, _aliases in STATUS_ALIASES] or args.status in {"待评估", "准备投递"}:
        status = args.status
    updates = {
        "status": status,
        "updated_at": today_iso(),
        "next_date": args.next_date,
        "next_action": args.next_action,
        "ai_notes": args.note,
    }
    fields, _missing = coerce_record(updates, schema)
    fields.pop("投递日期", None)
    preview = {
        "match_hint": {
            "company": args.company,
            "role_keyword": args.role_keyword,
            "record_id": args.record_id,
        },
        "fields": fields,
    }
    if args.dry_run or not args.record_id:
        write_json({
            "dry_run": True,
            "needs_record_selection": not bool(args.record_id),
            "preview": preview,
            "message": "Provide --record-id after selecting the matching Feishu record.",
        })
        return
    app_token = config.get("base_token")
    table_id = config.get("table_id")
    if not (app_token and table_id):
        die("Tracker is not configured. Run init-template first or create config with base_token and table_id.")
    result = run_lark_base(
        [
            "+record-batch-update",
            "--base-token", app_token,
            "--table-id", table_id,
            "--json", json.dumps({"record_id_list": [args.record_id], "patch": fields}, ensure_ascii=False),
        ],
        dry_run=False,
        identity=WRITE_IDENTITY,
        output_format=False,
    )
    write_json({"updated": preview, "result": result})


def extract_fields(record):
    if "fields" in record:
        return normalize_row(record["fields"])
    return normalize_row(record)


def normalize_cell(value):
    if isinstance(value, list):
        if len(value) == 1:
            return value[0]
        return value
    return value


def normalize_row(row):
    return {key: normalize_cell(value) for key, value in row.items()}


def cmd_weekly_review(args):
    raw = json.loads(Path(args.records_json).read_text(encoding="utf-8"))
    if isinstance(raw, dict) and isinstance(raw.get("data"), dict) and "fields" in raw["data"] and "data" in raw["data"]:
        fields = raw["data"]["fields"]
        records = [normalize_row(dict(zip(fields, row))) for row in raw["data"]["data"]]
    elif isinstance(raw, dict):
        records = raw.get("records") or raw.get("items") or raw.get("data", {}).get("items") or []
    else:
        records = raw
    rows = [extract_fields(record) for record in records]
    status_counts = {}
    interviews = []
    stale = []
    todos = []
    today = date.today()
    for row in rows:
        status = row.get("投递状态", "未知")
        status_counts[status] = status_counts.get(status, 0) + 1
        if status in ACTIVE_INTERVIEW_STATUSES:
            interviews.append(row)
        next_date_value = row.get("下一步日期")
        if next_date_value:
            try:
                next_day = datetime.fromisoformat(str(next_date_value)[:10]).date()
                if next_day <= today:
                    todos.append(row)
            except ValueError:
                pass
        updated = row.get("最近更新时间")
        if status not in ENDED_STATUSES and updated:
            try:
                updated_day = datetime.fromisoformat(str(updated)[:10]).date()
                if (today - updated_day).days >= 7:
                    stale.append(row)
            except ValueError:
                pass
    write_json({
        "total": len(rows),
        "status_counts": status_counts,
        "active_interviews": summarize_rows(interviews),
        "due_todos": summarize_rows(todos),
        "stale_records": summarize_rows(stale),
    })


def summarize_rows(rows):
    return [
        {
            "公司": row.get("公司"),
            "岗位名称": row.get("岗位名称"),
            "投递状态": row.get("投递状态"),
            "下一步日期": row.get("下一步日期"),
            "下一步动作": row.get("下一步动作"),
        }
        for row in rows
    ]


def cmd_quickstart(args):
    """Print an interactive step-by-step setup guide with copy-paste commands."""
    source = getattr(args, "source", None) or os.environ.get("HERMES_HOME", "").partition("/")[2] or "hermes"
    steps = [
        "=== Feishu Job Tracker Quickstart ===",
        "",
        f"Step 1 — Bind lark-cli to your agent workspace:",
        f"  lark-cli config bind --source {source} --identity user-default",
        "",
        "Step 2 — Log in as a user (requires interactive terminal / PTY):",
        "  lark-cli auth login --recommend",
        "",
        "  IMPORTANT: The device code is single-use. Do NOT restart this command.",
        "  It will print a verification URL — open it in your browser and click confirm.",
        "  If the URL doesn't appear, use PTY mode or:",
        "    lark-cli auth login --no-wait --json",
        "    lark-cli auth login --device-code <code_from_above>",
        "",
        "Step 3 — Verify your identity:",
        "  lark-cli auth status",
        "  (Make sure 'identity' is 'user' and 'userOpenId' is present)",
        "",
        "Step 4 — Create the tracker:",
        f"  python3 {sys.argv[0].replace(os.sep, '/')} bootstrap --dry-run",
        f"  python3 {sys.argv[0].replace(os.sep, '/')} bootstrap",
        "",
        "Step 5 — Verify by listing records:",
        f"  python3 {sys.argv[0].replace(os.sep, '/')} list-records",
        "",
        "If you hit any issues, run pre-check for diagnostics:",
        f"  python3 {sys.argv[0].replace(os.sep, '/')} pre-check",
    ]
    print("\n".join(steps))
    raise SystemExit(0)


def build_parser():
    parser = argparse.ArgumentParser(description="Feishu/Lark job tracker helper")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("pre-check")
    p.set_defaults(func=cmd_pre_check)

    p = sub.add_parser("quickstart")
    p.add_argument("--source")
    p.set_defaults(func=cmd_quickstart)

    p = sub.add_parser("check")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("bootstrap")
    p.add_argument("--name")
    p.add_argument("--timezone")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_bootstrap)

    p = sub.add_parser("schema")
    p.add_argument("--api-fields", action="store_true")
    p.set_defaults(func=cmd_schema)

    p = sub.add_parser("normalize-status")
    p.add_argument("text")
    p.set_defaults(func=cmd_normalize_status)

    p = sub.add_parser("init-template")
    p.add_argument("--name")
    p.add_argument("--timezone")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_init_template)

    p = sub.add_parser("add-record")
    p.add_argument("--from-json", required=True)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_add_record)

    p = sub.add_parser("configure")
    p.add_argument("--base-token", required=True)
    p.add_argument("--table-id", required=True)
    p.add_argument("--name")
    p.add_argument("--timezone")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_configure)

    p = sub.add_parser("repair-template")
    p.add_argument("--base-token")
    p.add_argument("--table-id")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_repair_template)

    p = sub.add_parser("check-permissions")
    p.add_argument("--base-token")
    p.add_argument("--identity", choices=["user", "bot"], default="user")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_check_permissions)

    p = sub.add_parser("transfer-owner-to-user")
    p.add_argument("--base-token")
    p.add_argument("--user-open-id")
    p.add_argument("--old-owner-perm", choices=["view", "edit", "full_access"], default="edit")
    p.add_argument("--need-notification", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_transfer_owner_to_user)

    p = sub.add_parser("search-duplicates")
    p.add_argument("--from-json", required=True)
    p.add_argument("--page-size", type=int, default=20)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_search_duplicates)

    p = sub.add_parser("delete-record")
    p.add_argument("--record-id", required=True)
    p.add_argument("--base-token")
    p.add_argument("--table-id")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_delete_record)

    p = sub.add_parser("list-records")
    p.add_argument("--base-token")
    p.add_argument("--table-id")
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_list_records)

    p = sub.add_parser("update-status")
    p.add_argument("--company")
    p.add_argument("--role-keyword")
    p.add_argument("--record-id")
    p.add_argument("--status", required=True)
    p.add_argument("--next-date")
    p.add_argument("--next-action")
    p.add_argument("--note")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_update_status)

    p = sub.add_parser("weekly-review")
    p.add_argument("--records-json", required=True)
    p.set_defaults(func=cmd_weekly_review)

    return parser


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
