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
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
CYAN    = "\033[36m"
WHITE   = "\033[97m"
MAGENTA = "\033[35m"

def c(text, *codes):
    return "".join(codes) + str(text) + RESET

def term_width() -> int:
    try:
        return os.get_terminal_size().columns
    except OSError:
        return 120


# ─────────────────────────────────────────────
#  Default config
# ─────────────────────────────────────────────
DEFAULT_CONFIG = {
    "run_directory":    ".",
    "separator":        "spaces",   # "spaces" or "periods"
    "ignored_files":    [],
    "ignored_dirs":     [],         # directory names (relative) to skip during walk
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
    """Recursively walk run_directory, skipping ignored dirs and files."""
    run_dir      = Path(cfg["run_directory"]).expanduser().resolve()
    ignored_files = set(cfg.get("ignored_files", []))
    ignored_dirs  = set(cfg.get("ignored_dirs",  []))

    entries = []
    try:
        for dirpath, dirs, filenames in os.walk(run_dir):
            # Prune ignored directories in-place so os.walk won't descend
            dirs[:] = [
                d for d in dirs
                if d not in ignored_dirs
                and str(Path(dirpath, d).relative_to(run_dir)) not in ignored_dirs
            ]

            for fname in sorted(filenames):
                if fname in ignored_files:
                    continue
                p = Path(dirpath) / fname
                rel_dir     = str(Path(dirpath).relative_to(run_dir))
                display_dir = "." if rel_dir == "." else rel_dir
                entries.append({
                    "path":      p,
                    "directory": display_dir,
                    "name":      fname,
                    "suggested": suggest_name(fname, cfg["separator"]),
                    "queued":    False,
                    "new_name":  None,
                    "action":    None,  # "rename" | "moveup"
                })

        entries.sort(key=lambda e: (e["directory"], e["name"]))
    except FileNotFoundError:
        print(c(f"[error] Directory not found: {run_dir}", RED))
    return entries


# ─────────────────────────────────────────────
#  Adaptive column layout
# ─────────────────────────────────────────────
# Fixed widths that don't scale
ID_W     = 5
STATUS_W = 12   # "● RENAME" or "● MOVE UP"
GAP      = 2    # spaces between every column

def _col_widths(total_width: int) -> tuple[int, int, int]:
    """
    Return (dir_w, name_w, suggested_w) that fill the available space.
    Remaining space after ID and STATUS is split: 30% dir, 35% name, 35% suggested.
    """
    available = total_width - ID_W - STATUS_W - (GAP * 4)
    available = max(available, 30)
    dir_w  = max(10, int(available * 0.30))
    name_w = max(10, int(available * 0.35))
    sug_w  = max(10, available - dir_w - name_w)
    return dir_w, name_w, sug_w


def _trunc(s: str, n: int) -> str:
    return s if len(s) <= n else s[:n - 1] + "…"

def _pad(s: str, n: int) -> str:
    """Pad or truncate plain string to exactly n chars (no ANSI)."""
    return _trunc(s, n).ljust(n)


# ─────────────────────────────────────────────
#  Display
# ─────────────────────────────────────────────
def print_table(entries: list[dict], run_dir: str = "—", config_path: str = "—"):
    os.system("clear")
    tw = term_width()

    print(c("\n  renamer", BOLD + CYAN)
          + c(f"  ·  dir: {run_dir}", DIM)
          + c(f"  ·  config: {config_path}\n", DIM))

    dir_w, name_w, sug_w = _col_widths(tw)

    # Header
    header = (
        f"{'ID':<{ID_W}}"
        f"{'DIRECTORY':<{dir_w + GAP}}"
        f"{'CURRENT NAME':<{name_w + GAP}}"
        f"{'SUGGESTED NAME':<{sug_w + GAP}}"
        f"STATUS"
    )
    print(c(f"  {header}", BOLD + DIM))
    print(c("  " + "─" * (tw - 4), DIM))

    for i, e in enumerate(entries, start=1):
        idx  = f"{i:<{ID_W}}"
        ddir = _pad(e["directory"], dir_w)
        cur  = _pad(e["name"], name_w)
        sug_raw = e["new_name"] if e["new_name"] else e["suggested"]
        sug  = _pad(sug_raw, sug_w)

        sp = " " * GAP

        if e["queued"] and e["action"] == "moveup":
            status = c("● MOVE UP", MAGENTA + BOLD)
            row = (c(idx, BOLD)
                   + c(ddir + sp, DIM)
                   + c(cur  + sp, WHITE)
                   + c(sug  + sp, MAGENTA + BOLD)
                   + status)
        elif e["queued"] and e["action"] == "rename":
            status = c("● RENAME", YELLOW + BOLD)
            row = (c(idx, BOLD)
                   + c(ddir + sp, DIM)
                   + c(cur  + sp, WHITE)
                   + c(sug  + sp, YELLOW + BOLD)
                   + status)
        else:
            status = c("○", DIM)
            row = (c(idx, BOLD)
                   + c(ddir + sp, DIM)
                   + c(cur  + sp, WHITE)
                   + c(sug  + sp, DIM)
                   + status)

        print(f"  {row}")

    print(c("\n  " + "─" * (tw - 4), DIM))
    _print_commands()


def _print_commands():
    cmds = [
        ("rn / rename <id>",           "Queue file for rename (opens suggested name to edit)"),
        ("mu / moveup <id|list|range>", "Move file(s) up one directory"),
        ("i  / ignore <id|list|range>", "Ignore file(s) — persists to config"),
        ("rm / remove <id|list|range>", "Remove file(s) from queue"),
        ("exe / execute",              "Execute all queued actions"),
        ("q  / quit / exit",           "Quit"),
    ]
    print(c("  COMMANDS\n", BOLD))
    for cmd, desc in cmds:
        print(f"  {c(f'{cmd:<30}', CYAN + BOLD)}{c(desc, DIM)}")
    print()


# ─────────────────────────────────────────────
#  ID / range parsing
# ─────────────────────────────────────────────
def parse_ids(token: str, max_id: int) -> list[int]:
    """Parse '3', '1,3,5', or '2..6' into a list of 0-based indices."""
    token = token.strip()

    range_match = re.fullmatch(r"(\d+)\.\.(\d+)", token)
    if range_match:
        lo, hi = int(range_match.group(1)), int(range_match.group(2))
        indices = list(range(lo, hi + 1))
    else:
        parts = [p.strip() for p in token.split(",")]
        indices = []
        for p in parts:
            if p.isdigit():
                indices.append(int(p))
            else:
                raise ValueError(f"Invalid id: '{p}'")

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
        input(c("  [Enter to continue]", DIM))
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
    e["action"]   = "rename"
    print(c(f"  ✓ Queued rename: {e['name']}  →  {final_name}", GREEN))
    input(c("  [Enter to continue]", DIM))


def cmd_moveup(args: str, entries: list[dict], run_dir: Path):
    """Queue file(s) to be moved up one directory."""
    try:
        indices = parse_ids(args, len(entries))
    except ValueError as exc:
        print(c(f"[error] {exc}", RED))
        input(c("  [Enter to continue]", DIM))
        return

    for idx in indices:
        e = entries[idx]
        current_path = e["path"]
        parent       = current_path.parent
        grandparent  = parent.parent

        # Safety: don't move above the run_directory
        try:
            grandparent.relative_to(run_dir)
            above_root = False
        except ValueError:
            above_root = grandparent == run_dir.parent or not str(grandparent).startswith(str(run_dir))

        if parent == run_dir:
            print(c(f"  [skip] {e['name']} is already at the root of the run directory.", YELLOW))
            continue

        dest = grandparent / e["name"]
        e["queued"]   = True
        e["action"]   = "moveup"
        e["new_name"] = str(dest)   # store full destination path for execute
        print(c(f"  ✓ Queued move up: {e['directory']}/{e['name']}  →  {grandparent.name}/", MAGENTA))

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
    """Remove file(s) from the queue (does not ignore)."""
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
        e["action"]   = None
        print(c(f"  Dequeued: {e['name']}", DIM))

    input(c("  [Enter to continue]", DIM))


def cmd_execute(entries: list[dict], run_dir: Path):
    """Execute all queued rename and move-up actions."""
    queued = [e for e in entries if e["queued"]]
    if not queued:
        print(c("  No actions queued.", YELLOW))
        input(c("  [Enter to continue]", DIM))
        return

    print(c(f"\n  About to execute {len(queued)} action(s):\n", BOLD))
    for e in queued:
        if e["action"] == "rename":
            dst_name = e["new_name"]
            print(f"    {c('RENAME',  YELLOW)}  {c(e['name'], WHITE)}  →  {c(dst_name, YELLOW)}")
        elif e["action"] == "moveup":
            dest = Path(e["new_name"])
            print(f"    {c('MOVE UP', MAGENTA)}  {c(e['directory'] + '/' + e['name'], WHITE)}  →  {c(str(dest.parent.name) + '/', MAGENTA)}")

    print()
    confirm = input(c("  Proceed? [y/N] > ", CYAN)).strip().lower()
    if confirm != "y":
        print(c("  Aborted.", RED))
        input(c("  [Enter to continue]", DIM))
        return

    errors = []
    for e in queued:
        try:
            if e["action"] == "rename":
                src = e["path"]
                dst = src.parent / e["new_name"]
                if dst.exists():
                    raise FileExistsError(f"Target already exists: {dst.name}")
                src.rename(dst)
                e["path"]     = dst
                e["name"]     = dst.name
                e["suggested"]= dst.name
                # Update display directory (stays same)
                rel = str(dst.parent.relative_to(run_dir))
                e["directory"] = "." if rel == "." else rel
                print(c(f"  ✓ Renamed: {src.name}  →  {dst.name}", GREEN))

            elif e["action"] == "moveup":
                src  = e["path"]
                dest = Path(e["new_name"])
                if dest.exists():
                    raise FileExistsError(f"Target already exists: {dest}")
                src.rename(dest)
                e["path"]     = dest
                rel = str(dest.parent.relative_to(run_dir))
                e["directory"] = "." if rel == "." else rel
                e["suggested"] = dest.name
                print(c(f"  ✓ Moved up: {src.name}  →  {dest.parent.name}/", GREEN))

            e["queued"]   = False
            e["new_name"] = None
            e["action"]   = None

        except Exception as exc:
            errors.append((e["name"], str(exc)))
            print(c(f"  ✗ {e['name']}: {exc}", RED))

    if errors:
        print(c(f"\n  {len(errors)} error(s) occurred.", RED))
    else:
        print(c("\n  All actions completed successfully.", GREEN + BOLD))

    input(c("  [Enter to continue]", DIM))


# ─────────────────────────────────────────────
#  Command alias map
# ─────────────────────────────────────────────
COMMAND_ALIASES: dict[str, str] = {
    "rn":      "rn",
    "rename":  "rn",
    "mu":      "mu",
    "moveup":  "mu",
    "i":       "i",
    "ignore":  "i",
    "rm":      "rm",
    "remove":  "rm",
    "exe":     "exe",
    "execute": "exe",
    "q":       "q",
    "quit":    "q",
    "exit":    "q",
}


# ─────────────────────────────────────────────
#  Main REPL
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Interactive file renaming tool")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH,
                        help="Path to JSON config file")
    args = parser.parse_args()

    config_path: Path = args.config.expanduser().resolve()
    cfg     = load_config(config_path)
    run_dir = Path(cfg["run_directory"]).expanduser().resolve()
    entries = load_files(cfg)

    # ── startup banner ────────────────────────
    print(c("\n  renamer", BOLD + CYAN))
    print(c(f"  config       : {config_path}", DIM))
    print(c(f"  dir          : {run_dir}", DIM))
    print(c(f"  ignored dirs : {', '.join(cfg['ignored_dirs']) or '(none)'}", DIM))
    print(c(f"  files found  : {len(entries)}\n", DIM))
    input(c("  [Enter to continue]", DIM))

    while True:
        print_table(entries, run_dir=str(run_dir), config_path=str(config_path))

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

        elif command == "mu":
            if not rest:
                print(c("[error] Usage: mu/moveup <id|list|range>", RED))
                input(c("  [Enter to continue]", DIM))
            else:
                cmd_moveup(rest, entries, run_dir)

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
            cmd_execute(entries, run_dir)

        else:
            print(c(f"[error] Unknown command '{raw_cmd}'. Try rn, mu, i, rm, exe, or q.", RED))
            input(c("  [Enter to continue]", DIM))

    print(c("\n  Goodbye.\n", DIM))


if __name__ == "__main__":
    main()
