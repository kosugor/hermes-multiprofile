#!/usr/bin/env python3
"""Acquire, inspect, or release the single shared Hermes wiki writer lock."""
from __future__ import annotations

import argparse
import json
import os
import secrets
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path


def lock_paths(root: Path) -> tuple[Path, Path]:
    lock_dir = root.expanduser().resolve() / ".hermes-maintenance" / "wiki-writer.lock"
    return lock_dir, lock_dir / "owner.json"


def read_owner(owner_file: Path) -> dict[str, object] | None:
    try:
        value = json.loads(owner_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def emit(value: dict[str, object]) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))


def public_owner(owner: dict[str, object] | None) -> dict[str, object] | None:
    if owner is None:
        return None
    return {key: value for key, value in owner.items() if key != "token"}


def acquire(root: Path, owner_name: str) -> int:
    lock_dir, owner_file = lock_paths(root)
    lock_dir.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
    try:
        lock_dir.mkdir(mode=0o700)
    except FileExistsError:
        emit({"acquired": False, "owner": public_owner(read_owner(owner_file)), "lock": str(lock_dir)})
        return 3

    record: dict[str, object] = {
        "owner": owner_name,
        "pid": os.getpid(),
        "host": socket.gethostname(),
        "acquired_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "token": secrets.token_urlsafe(32),
    }
    try:
        with owner_file.open("x", encoding="utf-8") as stream:
            json.dump(record, stream, ensure_ascii=False, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except OSError:
        try:
            lock_dir.rmdir()
        except OSError:
            pass
        raise
    emit({"acquired": True, "lock": str(lock_dir), "owner": record})
    return 0


def inspect(root: Path) -> int:
    lock_dir, owner_file = lock_paths(root)
    if not lock_dir.exists():
        emit({"locked": False, "lock": str(lock_dir)})
    else:
        emit({"locked": True, "lock": str(lock_dir), "owner": public_owner(read_owner(owner_file))})
    return 0


def release(root: Path, token: str) -> int:
    lock_dir, owner_file = lock_paths(root)
    record = read_owner(owner_file)
    if record is None or not secrets.compare_digest(str(record.get("token", "")), token):
        emit({"released": False, "lock": str(lock_dir), "reason": "lock token does not match"})
        return 4
    owner_file.unlink()
    try:
        lock_dir.rmdir()
    except OSError as exc:
        emit({"released": False, "lock": str(lock_dir), "reason": str(exc)})
        return 4
    emit({"released": True, "lock": str(lock_dir), "owner": record.get("owner")})
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wiki-root", type=Path, default=Path(__file__).resolve().parent.parent)
    commands = parser.add_subparsers(dest="command", required=True)
    acquire_parser = commands.add_parser("acquire")
    acquire_parser.add_argument("--owner", required=True)
    commands.add_parser("inspect")
    release_parser = commands.add_parser("release")
    release_parser.add_argument("--token", required=True)
    args = parser.parse_args(argv)
    if args.command == "acquire":
        return acquire(args.wiki_root, args.owner)
    if args.command == "inspect":
        return inspect(args.wiki_root)
    return release(args.wiki_root, args.token)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except OSError as exc:
        print(f"wiki writer lock error: {exc}", file=sys.stderr)
        sys.exit(1)
