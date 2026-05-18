#!/usr/bin/env python3
import argparse
import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "feishu-job-tracker"


def default_codex_dir():
    return Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")) / "skills"


def install_codex(target_dir, mode, force):
    target_dir.mkdir(parents=True, exist_ok=True)
    dest = target_dir / SKILL_NAME
    if dest.exists() or dest.is_symlink():
        if not force:
            raise SystemExit(f"{dest} already exists. Re-run with --force to replace it.")
        if dest.is_symlink() or dest.is_file():
            dest.unlink()
        else:
            shutil.rmtree(dest)

    if mode == "copy":
        shutil.copytree(ROOT, dest, ignore=shutil.ignore_patterns("__pycache__", ".git"))
        action = "copied"
    else:
        dest.symlink_to(ROOT, target_is_directory=True)
        action = "symlinked"

    print(f"[ok] {action} {ROOT} -> {dest}")
    print("[next] Restart or refresh Codex so it discovers the skill.")


def main():
    parser = argparse.ArgumentParser(description="Install Feishu Job Tracker skill for AI agent runtimes.")
    parser.add_argument("--target", choices=["codex"], default="codex")
    parser.add_argument("--target-dir", type=Path, default=None)
    parser.add_argument("--mode", choices=["symlink", "copy"], default="symlink")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    if args.target == "codex":
        install_codex(args.target_dir or default_codex_dir(), args.mode, args.force)


if __name__ == "__main__":
    main()
