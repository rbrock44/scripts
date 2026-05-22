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


def suggest_dir_name(dirname: str, separator: str) -> str:
    """
    TODO: Implement intelligent directory suggestion logic.

    For now: return the original directory name unchanged.
    """
    return dirname


# ─────────────────────────────────────────────
#  Load files from run directory
# ─────────────────────────────────────────────
def load_files(cfg: dict) -> list[dict]:
    """Recursively walk run_directory, skipping ignored dirs and files."""
    run_dir       = Path(cfg["run_directory"]).expanduser().resolve()
    ignored_files = set(cfg.get("ignored_files", []))
    ignored_dirs  = set(cfg.get("ignored_dirs",  []))

    entries = []
    try:
        for dirpath, dirs, filenames in os.walk(run_dir):
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
                    "action":    None,  # "rename" | "add" | "moveup"
                })

        entries.sort(key=lambda e: (e["directory"], e["name"]))
    except FileNotFoundError:
        print(c(f"[error] Directory not found: {run_dir}", RED))
    return entries


def load_directories(cfg: dict) -> list[dict]:
    """Recursively walk run_directory and return directories for rename actions."""
    run_dir      = Path(cfg["run_directory"]).expanduser().resolve()
    ignored_dirs = set(cfg.get("ignored_dirs", []))

    entries = []
    try:
        for dirpath, dirs, _ in os.walk(run_dir):
            dirs[:] = [
                d for d in dirs
                if d not in ignored_dirs
                and str(Path(dirpath, d).relative_to(run_dir)) not in ignored_dirs
            ]

            for dname in sorted(dirs):
                p = Path(dirpath) / dname
                rel_parent  = str(Path(dirpath).relative_to(run_dir))
                display_dir = "." if rel_parent == "." else rel_parent
                rel_path    = str(p.relative_to(run_dir))
                entries.append({
                    "path":      p,
                    "relative":  rel_path,
                    "directory": display_dir,
                    "name":      dname,
                    "suggested": suggest_dir_name(dname, cfg["separator"]),
                    "queued":    False,
                    "new_name":  None,
                    "action":    None,  # "rename" | "add"
                })

        entries.sort(key=lambda e: (e["directory"], e["name"]))
    except FileNotFoundError:
        print(c(f"[error] Directory not found: {run_dir}", RED))

    return entries


# ─────────────────────────────────────────────
#  Adaptive column layout + wrapping
# ─────────────────────────────────────────────
ID_W     = 5
STATUS_W = 12   # "● RENAME" / "● MOVE UP" / "● ADD"
GAP      = 2

def _col_widths(total_width: int) -> tuple[int, int, int]:
    """30% dir · 35% current · 35% suggested of the flexible space."""
    available = max(30, total_width - ID_W - STATUS_W - (GAP * 4))
    dir_w  = max(10, int(available * 0.30))
    name_w = max(10, int(available * 0.35))
    sug_w  = max(10, available - dir_w - name_w)
    return dir_w, name_w, sug_w


def _wrap(text: str, width: int) -> list[str]:
    """
    Break `text` into lines of at most `width` chars.
    Tries to split on path separators (/ or .) first, then hard-wraps.
    The first line is returned as-is (padded); continuation lines are
    prefixed with a small continuation marker.
    """
    if len(text) <= width:
        return [text.ljust(width)]

    lines = []
    remaining = text
    while remaining:
        if len(remaining) <= width:
            lines.append(remaining.ljust(width))
            break
        # Try to find a nice break point (/ . _ - space) within the width
        chunk = remaining[:width]
        break_at = max(
            chunk.rfind("/"),
            chunk.rfind("."),
            chunk.rfind("_"),
            chunk.rfind("-"),
            chunk.rfind(" "),
        )
        if break_at > width // 3:          # only use it if reasonably far in
            lines.append(remaining[:break_at + 1].ljust(width))
            remaining = remaining[break_at + 1:]
        else:
            lines.append(remaining[:width])
            remaining = remaining[width:]

    return lines


def _render_row(
    idx_str: str,
    ddir: str, dir_w: int,
    cur: str,  name_w: int,
    sug: str,  sug_w: int,
    status_str: str,
    *,
    color_idx, color_dir, color_cur, color_sug, color_status,
) -> str:
    """
    Render a multi-line table row.  Each cell is independently word-wrapped
    to its column width; all columns are padded to the same number of lines.
    """
    sp = " " * GAP

    dir_lines  = _wrap(ddir, dir_w)
    cur_lines  = _wrap(cur,  name_w)
    sug_lines  = _wrap(sug,  sug_w)
    n_lines    = max(len(dir_lines), len(cur_lines), len(sug_lines))

    # Pad all columns to the same height
    def _extend(lst, width):
        while len(lst) < n_lines:
            lst.append(" " * width)
        return lst

    dir_lines = _extend(dir_lines, dir_w)
    cur_lines = _extend(cur_lines, name_w)
    sug_lines = _extend(sug_lines, sug_w)

    out_lines = []
    for i in range(n_lines):
        if i == 0:
            id_part     = c(f"{idx_str:<{ID_W}}", color_idx)
            status_part = c(status_str, color_status)
        else:
            id_part     = " " * ID_W
            status_part = ""

        row = (
            id_part
            + c(dir_lines[i]  + sp, color_dir)
            + c(cur_lines[i]  + sp, color_cur)
            + c(sug_lines[i]  + sp, color_sug)
            + status_part
        )
        out_lines.append(f"  {row}")

    return "\n".join(out_lines)


# ─────────────────────────────────────────────
#  Display
# ─────────────────────────────────────────────
def print_table(
    entries: list[dict],
    run_dir: str = "—",
    config_path: str = "—",
    mode: str = "files",
):
    os.system("clear")
    tw = term_width()

    mode_label = "rename files" if mode == "files" else "rename directories"

    print(c("\n  renamer", BOLD + CYAN)
          + c(f"  ·  mode: {mode_label}", DIM)
          + c(f"  ·  dir: {run_dir}", DIM)
          + c(f"  ·  config: {config_path}\n", DIM))

    dir_w, name_w, sug_w = _col_widths(tw)

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
        sug_raw = e["new_name"] if e["new_name"] else e["suggested"]

        action = e["action"] if e["queued"] else None

        if action == "moveup":
            status_str   = "● MOVE UP"
            color_status = MAGENTA + BOLD
            color_idx    = BOLD
            color_dir    = DIM
            color_cur    = WHITE
            color_sug    = MAGENTA + BOLD
        elif action == "rename":
            status_str   = "● RENAME"
            color_status = YELLOW + BOLD
            color_idx    = BOLD
            color_dir    = DIM
            color_cur    = WHITE
            color_sug    = YELLOW + BOLD
        elif action == "add":
            status_str   = "● ADD"
            color_status = GREEN + BOLD
            color_idx    = BOLD
            color_dir    = DIM
            color_cur    = WHITE
            color_sug    = GREEN + BOLD
        else:
            status_str   = "○"
            color_status = DIM
            color_idx    = BOLD
            color_dir    = DIM
            color_cur    = WHITE
            color_sug    = DIM

        print(_render_row(
            str(i),
            e["directory"], dir_w,
            e["name"],      name_w,
            sug_raw,        sug_w,
            status_str,
            color_idx=color_idx, color_dir=color_dir,
            color_cur=color_cur, color_sug=color_sug,
            color_status=color_status,
        ))

    print(c("\n  " + "─" * (tw - 4), DIM))
    _print_commands(mode)


def _print_commands(mode: str):
    if mode == "files":
        cmds = [
            ("rd",                          "Switch to directory rename screen"),
            ("rn / rename <id>",            "Queue a file for rename — opens suggested name to edit"),
            ("a / add <id|list|range>",     "Queue file(s) using the suggested name as-is"),
            ("mu / moveup <id|list|range>", "Move file(s) up one directory"),
            ("i  / ignore <id|list|range>", "Ignore file(s) — persists to config"),
            ("rm / remove <id|list|range>", "Remove file(s) from queue"),
            ("exe / execute",               "Execute all queued actions"),
            ("q  / quit / exit",            "Quit"),
        ]
    else:
        cmds = [
            ("rf",                          "Switch back to file rename screen"),
            ("rn / rename <id>",            "Queue a directory for rename — opens suggested name to edit"),
            ("a / add <id|list|range>",     "Queue directory rename(s) using suggested name"),
            ("i  / ignore <id|list|range>", "Ignore director(ies) — persists to config"),
            ("rm / remove <id|list|range>", "Remove directory rename(s) from queue"),
            ("exe / execute",               "Execute all queued directory rename actions"),
            ("q  / quit / exit",            "Quit"),
        ]

    print(c("  COMMANDS\n", BOLD))
    for cmd, desc in cmds:
        print(f"  {c(f'{cmd:<32}', CYAN + BOLD)}{c(desc, DIM)}")
    print(c("\n  ARGUMENT HELP", BOLD))
    print(f"  {c('id', CYAN + BOLD):<32}{c('Single item number. Example: 7', DIM)}")
    print(f"  {c('list', CYAN + BOLD):<32}{c('Comma-separated IDs. Example: 1,4,9', DIM)}")
    print(f"  {c('range', CYAN + BOLD):<32}{c('Inclusive range with .. Example: 3..6', DIM)}")
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
    """Queue a single file for rename with user editing."""
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


def cmd_add(args: str, entries: list[dict]):
    """Queue file(s) using their suggested name without prompting."""
    try:
        indices = parse_ids(args, len(entries))
    except ValueError as exc:
        print(c(f"[error] {exc}", RED))
        input(c("  [Enter to continue]", DIM))
        return

    for idx in indices:
        e = entries[idx]
        e["new_name"] = e["suggested"]
        e["queued"]   = True
        e["action"]   = "add"
        print(c(f"  ✓ Queued add: {e['name']}  →  {e['suggested']}", GREEN))

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
        e            = entries[idx]
        current_path = e["path"]
        parent       = current_path.parent
        grandparent  = parent.parent

        if parent == run_dir:
            print(c(f"  [skip] {e['name']} is already at the root of the run directory.", YELLOW))
            continue

        dest = grandparent / e["name"]
        e["queued"]   = True
        e["action"]   = "moveup"
        e["new_name"] = str(dest)
        print(c(f"  ✓ Queued move up: {e['directory']}/{e['name']}  →  {grandparent.name}/", MAGENTA))

    input(c("  [Enter to continue]", DIM))


def cmd_ignore(
    args: str,
    entries: list[dict],
    cfg: dict,
    config_path: Path,
    ignore_key: str,
    ignore_value_key: str,
):
    """Add item(s) to an ignore list and remove from current entries."""
    try:
        indices = parse_ids(args, len(entries))
    except ValueError as exc:
        print(c(f"[error] {exc}", RED))
        input(c("  [Enter to continue]", DIM))
        return

    ignored = cfg.setdefault(ignore_key, [])
    for idx in sorted(indices, reverse=True):
        value = entries[idx][ignore_value_key]
        if value not in ignored:
            ignored.append(value)
            print(c(f"  Ignored: {value}", YELLOW))
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


def cmd_execute(entries: list[dict], run_dir: Path, entry_kind: str = "files") -> bool:
    """Execute all queued actions for files or directories."""
    queued = [e for e in entries if e["queued"]]
    if not queued:
        print(c("  No actions queued.", YELLOW))
        input(c("  [Enter to continue]", DIM))
        return False

    if entry_kind == "directories":
        # Rename deepest directories first to avoid breaking child paths.
        queued = sorted(queued, key=lambda e: len(Path(e["relative"]).parts), reverse=True)

    print(c(f"\n  About to execute {len(queued)} action(s):\n", BOLD))
    for e in queued:
        if e["action"] in ("rename", "add"):
            label = c("RENAME", YELLOW) if e["action"] == "rename" else c("ADD", GREEN)
            print(f"    {label}    {c(e['name'], WHITE)}  →  {c(e['new_name'], YELLOW if e['action'] == 'rename' else GREEN)}")
        elif e["action"] == "moveup":
            dest = Path(e["new_name"])
            print(f"    {c('MOVE UP', MAGENTA)}  {c(e['directory'] + '/' + e['name'], WHITE)}  →  {c(dest.parent.name + '/', MAGENTA)}")

    print()
    confirm = input(c("  Proceed? [y/N] > ", CYAN)).strip().lower()
    if confirm != "y":
        print(c("  Aborted.", RED))
        input(c("  [Enter to continue]", DIM))
        return False

    errors = []
    for e in queued:
        try:
            if e["action"] in ("rename", "add"):
                src = e["path"]
                dst = src.parent / e["new_name"]
                if dst.exists():
                    raise FileExistsError(f"Target already exists: {dst.name}")
                src.rename(dst)
                e["path"]      = dst
                e["name"]      = dst.name
                e["suggested"] = dst.name
                rel = str(dst.parent.relative_to(run_dir))
                e["directory"] = "." if rel == "." else rel
                print(c(f"  ✓ {e['action'].capitalize()}: {src.name}  →  {dst.name}", GREEN))

            elif e["action"] == "moveup":
                src  = e["path"]
                dest = Path(e["new_name"])
                if dest.exists():
                    raise FileExistsError(f"Target already exists: {dest}")
                src.rename(dest)
                e["path"] = dest
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
    return True


# ─────────────────────────────────────────────
#  Command alias map
# ─────────────────────────────────────────────
COMMAND_ALIASES: dict[str, str] = {
    "rf":      "rf",
    "rd":      "rd",
    "a":       "add",
    "rn":      "rn",
    "rename":  "rn",
    "add":     "add",
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
    file_entries = load_files(cfg)
    dir_entries  = load_directories(cfg)
    mode         = "files"

    # ── startup banner ────────────────────────
    print(c("\n  renamer", BOLD + CYAN))
    print(c(f"  config       : {config_path}", DIM))
    print(c(f"  dir          : {run_dir}", DIM))
    print(c(f"  ignored dirs : {', '.join(cfg['ignored_dirs']) or '(none)'}", DIM))
    print(c(f"  files found  : {len(file_entries)}", DIM))
    print(c(f"  dirs found   : {len(dir_entries)}\n", DIM))
    input(c("  [Enter to continue]", DIM))

    while True:
        entries = file_entries if mode == "files" else dir_entries
        print_table(entries, run_dir=str(run_dir), config_path=str(config_path), mode=mode)

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

        elif command == "rd":
            mode = "directories"

        elif command == "rf":
            mode = "files"

        elif command == "rn":
            if not rest:
                print(c("[error] Usage: rn/rename <id>", RED))
                input(c("  [Enter to continue]", DIM))
            else:
                cmd_rn(rest, entries)

        elif command == "add":
            if not rest:
                print(c("[error] Usage: add <id|list|range>", RED))
                input(c("  [Enter to continue]", DIM))
            else:
                cmd_add(rest, entries)

        elif command == "mu":
            if mode != "files":
                print(c("[error] moveup is only available in file mode. Use rf first.", RED))
                input(c("  [Enter to continue]", DIM))
            elif not rest:
                print(c("[error] Usage: mu/moveup <id|list|range>", RED))
                input(c("  [Enter to continue]", DIM))
            else:
                cmd_moveup(rest, entries, run_dir)

        elif command == "i":
            if not rest:
                print(c("[error] Usage: i/ignore <id|list|range>", RED))
                input(c("  [Enter to continue]", DIM))
            else:
                if mode == "files":
                    cmd_ignore(rest, entries, cfg, config_path, "ignored_files", "name")
                else:
                    cmd_ignore(rest, entries, cfg, config_path, "ignored_dirs", "relative")

        elif command == "rm":
            if not rest:
                print(c("[error] Usage: rm/remove <id|list|range>", RED))
                input(c("  [Enter to continue]", DIM))
            else:
                cmd_rm(rest, entries)

        elif command == "exe":
            if mode == "files":
                if cmd_execute(entries, run_dir, entry_kind="files"):
                    file_entries = load_files(cfg)
            else:
                if cmd_execute(entries, run_dir, entry_kind="directories"):
                    dir_entries  = load_directories(cfg)
                    file_entries = load_files(cfg)

        else:
            print(c(f"[error] Unknown command '{raw_cmd}'. Try rf/rd, rn, add, mu, i, rm, exe, or q.", RED))
            input(c("  [Enter to continue]", DIM))

    print(c("\n  Goodbye.\n", DIM))


if __name__ == "__main__":
    main()
