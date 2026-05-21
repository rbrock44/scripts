#!/usr/bin/env python3
"""
renamer.py — Interactive file renaming tool
Usage: python3 renamer.py [--config path/to/config.json]
"""

import os
import sys
import json
import re
import shutil
import argparse
from pathlib import Path
from typing import Optional

# ─────────────────────────────────────────────
#  ANSI color helpers
# ─────────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RED    = "\033[31m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
CYAN   = "\033[36m"
WHITE  = "\033[97m"
BG_DARK = "\033[48;5;235m"

def c(text, *codes):
    return "".join(codes) + str(text) + RESET


# ─────────────────────────────────────────────
#  Default config
# ─────────────────────────────────────────────
DEFAULT_CONFIG = {
    "run_directory": ".",
    "separator": "spaces",   # "spaces" or "periods"
    "ignored_files": []
}

DEFAULT_CONFIG_PATH = Path.home() / "renamer-settings.json"


# ─────────────────────────────────────────────
#  Settings helpers
# ─────────────────────────────────────────────
def load_config(path: Path) -> dict:
    if path.exists():
        try:
            with open(path) as f:
                data = json.load(f)
            # Fill in missing keys from defaults
            for k, v in DEFAULT_CONFIG.items():
                data.setdefault(k, v)
            return data
        except json.JSONDecodeError as e:
            print(c(f"[warn] Config parse error ({e}), using defaults.", YELLOW))
    return dict(DEFAULT_CONFIG)


def save_config(cfg: dict, path: Path):
    with open(path, "w") as f:
        json.dump(cfg, f, indent=2)


# ─────────────────────────────────────────────
#  Suggested-name logic  (TODO)
# ─────────────────────────────────────────────
def suggest_name(filename: str, separator: str) -> str:
    """
    TODO: Implement intelligent name suggestion logic.

    Ideas to implement:
      - Normalize separators (replace underscores/dots/dashes with the
        configured separator — spaces or periods)
      - Strip redundant tokens (e.g. "copy", "final", version numbers)
      - Title-case words for human-readable names
      - Date-pattern detection and reformatting (YYYYMMDD → YYYY-MM-DD)
      - Detect camera-roll patterns (IMG_1234, DSC_5678) and propose
        descriptive names based on EXIF metadata if available
      - Strip illegal filesystem characters

    For now: return the original filename unchanged.
    """
    return filename


# ─────────────────────────────────────────────
#  Load files from run directory
# ─────────────────────────────────────────────
def load_files(cfg: dict) -> list[dict]:
    """Return a sorted list of file-entry dicts, excluding ignored files."""
    run_dir = Path(cfg["run_directory"]).expanduser().resolve()
    ignored  = set(cfg.get("ignored_files", []))

    entries = []
    try:
        for p in sorted(run_dir.iterdir()):
            if p.is_file() and p.name not in ignored:
                entries.append({
                    "path":      p,
                    "directory": str(p.parent),
                    "name":      p.name,
                    "suggested": suggest_name(p.name, cfg["separator"]),
                    "queued":    False,
                    "new_name":  None,   # set when user edits the suggested name
                })
    except FileNotFoundError:
        print(c(f"[error] Directory not found: {run_dir}", RED))
    return entries


# ─────────────────────────────────────────────
#  Display
# ─────────────────────────────────────────────
HEADER_FMT = "{:<5} {:<35} {:<30} {:<30} {}"

def print_table(entries: list[dict]):
    os.system("clear")
    run_dir = entries[0]["directory"] if entries else "—"
    print(c(f"\n  renamer  ·  {run_dir}\n", BOLD + CYAN))

    # Column header
    print(c(HEADER_FMT.format("ID", "DIRECTORY", "CURRENT NAME", "SUGGESTED NAME", "STATUS"), BOLD + DIM))
    print(c("─" * 110, DIM))

    for i, e in enumerate(entries, start=1):
        idx   = c(f"{i:<5}", BOLD)
        dname = c(f"{_trunc(e['directory'], 33):<35}", DIM)
        cur   = f"{_trunc(e['name'], 28):<30}"
        sug_raw  = e["new_name"] if e["new_name"] else e["suggested"]
        sug   = f"{_trunc(sug_raw, 28):<30}"

        if e["queued"]:
            status = c("● QUEUED", YELLOW + BOLD)
            cur    = c(cur, WHITE)
            sug    = c(sug, YELLOW + BOLD)
        else:
            status = c("○", DIM)
            cur    = c(cur, WHITE)
            sug    = c(sug, DIM)

        print(f"  {idx}{dname}{cur}{sug}{status}")

    print(c("\n" + "─" * 110, DIM))
    _print_commands()


def _trunc(s: str, n: int) -> str:
    return s if len(s) <= n else s[:n - 1] + "…"


def _print_commands():
    cmds = [
        ("rn / rename <id>",          "Queue file for rename (opens suggested name to edit)"),
        ("i  / ignore <id|list|range>","Ignore file(s) — persists to config"),
        ("rm / remove <id|list|range>","Remove file(s) from rename queue"),
        ("exe / execute",             "Execute all queued renames"),
        ("q  / quit / exit",          "Quit"),
    ]
    print(c("  COMMANDS\n", BOLD))
    for cmd, desc in cmds:
        print(f"  {c(f'{cmd:<22}', CYAN + BOLD)}{c(desc, DIM)}")
    print()


# ─────────────────────────────────────────────
#  ID / range parsing
# ─────────────────────────────────────────────
def parse_ids(token: str, max_id: int) -> list[int]:
    """Parse '3', '1,3,5', or '2..6' into a list of 0-based indices."""
    token = token.strip()
    indices = []

    # Range: 1..5
    range_match = re.fullmatch(r"(\d+)\.\.(\d+)", token)
    if range_match:
        lo, hi = int(range_match.group(1)), int(range_match.group(2))
        indices = list(range(lo, hi + 1))
    else:
        # Comma-separated or single
        parts = [p.strip() for p in token.split(",")]
        for p in parts:
            if p.isdigit():
                indices.append(int(p))
            else:
                raise ValueError(f"Invalid id: '{p}'")

    # Convert to 0-based and validate
    result = []
    for n in indices:
        if 1 <= n <= max_id:
            result.append(n - 1)
        else:
            print(c(f"[warn] ID {n} out of range (1–{max_id}), skipped.", YELLOW))
    return result


# ─────────────────────────────────────────────
#  Command handlers
# ─────────────────────────────────────────────
def cmd_rn(args: str, entries: list[dict]):
    """Queue a file for rename, letting the user edit the suggested name."""
    if not args.strip().isdigit():
        print(c("[error] rn expects a single numeric ID.", RED))
        return

    idx_list = parse_ids(args.strip(), len(entries))
    if not idx_list:
        return
    idx = idx_list[0]
    e   = entries[idx]

    current_suggestion = e["new_name"] if e["new_name"] else e["suggested"]
    print(c(f"\n  Editing: {e['name']}", BOLD))
    print(c(f"  (Press Enter to keep: {current_suggestion})", DIM))
    try:
        user_input = input(c("  New name > ", CYAN)).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return

    final_name = user_input if user_input else current_suggestion
    e["new_name"] = final_name
    e["queued"]   = True
    print(c(f"  ✓ Queued: {e['name']}  →  {final_name}", GREEN))
    input(c("  [Enter to continue]", DIM))


def cmd_ignore(args: str, entries: list[dict], cfg: dict, config_path: Path):
    """Add file(s) to the ignore list and remove from current entries."""
    try:
        indices = parse_ids(args, len(entries))
    except ValueError as exc:
        print(c(f"[error] {exc}", RED))
        input(c("  [Enter to continue]", DIM))
        return

    ignored = cfg.setdefault("ignored_files", [])
    for idx in sorted(indices, reverse=True):
        name = entries[idx]["name"]
        if name not in ignored:
            ignored.append(name)
            print(c(f"  Ignored: {name}", YELLOW))
        entries.pop(idx)

    save_config(cfg, config_path)
    input(c("  [Enter to continue]", DIM))


def cmd_rm(args: str, entries: list[dict]):
    """Remove file(s) from the rename queue (does not ignore)."""
    try:
        indices = parse_ids(args, len(entries))
    except ValueError as exc:
        print(c(f"[error] {exc}", RED))
        input(c("  [Enter to continue]", DIM))
        return

    for idx in indices:
        e = entries[idx]
        e["queued"]   = False
        e["new_name"] = None
        print(c(f"  Dequeued: {e['name']}", DIM))

    input(c("  [Enter to continue]", DIM))


def cmd_execute(entries: list[dict]):
    """Rename all queued files."""
    queued = [e for e in entries if e["queued"]]
    if not queued:
        print(c("  No files queued.", YELLOW))
        input(c("  [Enter to continue]", DIM))
        return

    print(c(f"\n  About to rename {len(queued)} file(s):\n", BOLD))
    for e in queued:
        src = e["path"]
        dst = src.parent / e["new_name"]
        print(f"    {c(e['name'], WHITE)}  →  {c(e['new_name'], GREEN)}")

    print()
    confirm = input(c("  Proceed? [y/N] > ", CYAN)).strip().lower()
    if confirm != "y":
        print(c("  Aborted.", RED))
        input(c("  [Enter to continue]", DIM))
        return

    errors = []
    for e in queued:
        src = e["path"]
        dst = src.parent / e["new_name"]
        try:
            if dst.exists():
                raise FileExistsError(f"Target already exists: {dst.name}")
            src.rename(dst)
            e["path"]     = dst
            e["name"]     = dst.name
            e["queued"]   = False
            e["new_name"] = None
            print(c(f"  ✓ {src.name}  →  {dst.name}", GREEN))
        except Exception as exc:
            errors.append((e["name"], str(exc)))
            print(c(f"  ✗ {e['name']}: {exc}", RED))

    if errors:
        print(c(f"\n  {len(errors)} error(s) occurred.", RED))
    else:
        print(c("\n  All renames completed successfully.", GREEN + BOLD))

    input(c("  [Enter to continue]", DIM))


# ─────────────────────────────────────────────
#  Command alias map
# ─────────────────────────────────────────────
COMMAND_ALIASES: dict[str, str] = {
    "rn":     "rn",
    "rename": "rn",
    "i":      "i",
    "ignore": "i",
    "rm":     "rm",
    "remove": "rm",
    "exe":    "exe",
    "execute":"exe",
    "q":      "q",
    "quit":   "q",
    "exit":   "q",
}


# ─────────────────────────────────────────────
#  Main REPL
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Interactive file renaming tool")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH,
                        help="Path to JSON config file")
    args = parser.parse_args()

    config_path: Path = args.config
    cfg   = load_config(config_path)
    entries = load_files(cfg)

    while True:
        print_table(entries)

        try:
            raw = input(c("  > ", BOLD + CYAN)).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not raw:
            continue

        parts   = raw.split(None, 1)
        raw_cmd = parts[0].lower()
        rest    = parts[1] if len(parts) > 1 else ""
        command = COMMAND_ALIASES.get(raw_cmd)

        if command == "q":
            break

        elif command == "rn":
            if not rest:
                print(c("[error] Usage: rn/rename <id>", RED))
                input(c("  [Enter to continue]", DIM))
            else:
                cmd_rn(rest, entries)

        elif command == "i":
            if not rest:
                print(c("[error] Usage: i/ignore <id|list|range>", RED))
                input(c("  [Enter to continue]", DIM))
            else:
                cmd_ignore(rest, entries, cfg, config_path)

        elif command == "rm":
            if not rest:
                print(c("[error] Usage: rm/remove <id|list|range>", RED))
                input(c("  [Enter to continue]", DIM))
            else:
                cmd_rm(rest, entries)

        elif command == "exe":
            cmd_execute(entries)

        else:
            print(c(f"[error] Unknown command '{raw_cmd}'. Try rn/rename, i/ignore, rm/remove, exe/execute, or q/quit.", RED))
            input(c("  [Enter to continue]", DIM))

    print(c("\n  Goodbye.\n", DIM))


if __name__ == "__main__":
    main()
