#!/usr/bin/env python3
"""
==============================================================================
 tmdb_top_lists.py — HOW TO RUN
==============================================================================

WHAT IT DOES
    For each year in a range, pulls the top X rated movies and/or TV shows,
    plus the top X most popular actors/actresses overall, plus each of those
    actors' top X rated movies and TV credits. Writes it all to one CSV.

SETUP (one-time)
    1. Get a free TMDb API key: https://www.themoviedb.org/settings/api
       (sign up for an account, then request an API key under Settings > API)
    2. pip install requests

BASIC USAGE
    python tmdb_top_lists.py --api-key YOUR_KEY \
        --start-year 2020 --end-year 2024 \
        --top-titles 10 --top-people 5 --top-people-titles 5 \
        --output results.csv

    You can set the key as an environment variable instead of passing it
    every time:
        export TMDB_API_KEY=YOUR_KEY
        python tmdb_top_lists.py --start-year 2023 --end-year 2023

LARGE OVERNIGHT RUN EXAMPLE (1970 to present, top 100 of everything)
    export TMDB_API_KEY=YOUR_KEY
    python tmdb_top_lists.py --start-year 1970 --end-year 2026 \
        --top-titles 100 --top-people 100 --top-people-titles 100 \
        --output tmdb_top_lists_1970_2026.csv

    Notes on a run this size:
      - This will take HOURS (likely several), mostly due to TMDb's rate
        limit and the sheer number of API calls (~57 years x 2 media types
        for titles, plus ~100 actors x 2 media types for credits).
      - Progress is printed to the console with timestamps as it goes —
        redirect to a log file if running in the background, e.g.:
            nohup python tmdb_top_lists.py --api-key YOUR_KEY \
                --start-year 1970 --end-year 2026 \
                --top-titles 100 --top-people 100 --top-people-titles 100 \
                --output tmdb_top_lists_1970_2026.csv > run.log 2>&1 &
      - The CSV is written incrementally (a row at a time, flushed to disk),
        so if the process is killed or crashes partway through, you keep
        everything gathered up to that point — just re-run for the rest
        if needed (see RESUMING below).
      - TMDb's discover endpoint returns 20 results per page; asking for
        100 top titles per year means 5 page-fetches per year/media type.

RESUMING AFTER AN INTERRUPTION (automatic)
    The script writes a checkpoint file alongside your CSV, named
    <output>.checkpoint.json (e.g. tmdb_top_lists_1970_2026.csv.checkpoint.json).
    It tracks which year/media-type combos and which people are fully done.

    If the script is killed, crashes, or your machine restarts, just re-run
    the EXACT SAME COMMAND. It will:
      - Skip any year/media-type combos already completed
      - Reuse the same list of top people (fetched once, saved in the
        checkpoint) rather than re-fetching a possibly-different popularity
        ranking
      - Skip any people whose credits were already fully written
      - Append new rows to the same CSV instead of overwriting it

    Force a completely fresh run (ignoring/deleting any existing checkpoint
    and output file) with:
        python tmdb_top_lists.py ... --restart

    Note: resuming matches on the run's settings (year range, top-N values,
    --media). If you change any of those, the script will detect the
    mismatch, warn you, and start fresh automatically.

MEDIA LIBRARY CHECK COLUMN
    Every row with a title gets an extra column, in_media_library, that
    checks whether that title (matched by name + year) appears in this
    public media list file:
        https://github.com/rbrock44/home-page-media-file/blob/master/media.txt
    (True / False / blank if the list couldn't be downloaded)

    The list (~13k lines) is downloaded once at the start of a run and
    parsed into an in-memory lookup dict, so every check afterward is an
    instant O(1) dictionary lookup — this adds essentially zero time to
    the run, even at the largest --top-titles/--top-people settings.

    Matching is done on normalized text (lowercased, punctuation stripped)
    of "Title (Year)", since that's the naming pattern most entries in the
    list follow. Entries in the list that don't follow that pattern (many
    TV episode files are named like "Show.S01E01.mkv") simply won't match
    anything — this is a limitation of the source file, not the script.

    Options:
        --skip-media-check           Don't fetch/check against the list at all
        --media-list-url URL         Use a different source list (same format)
        --media-list-cache PATH      Cache the downloaded list locally so a
                                      resumed run doesn't re-download it

OTHER OPTIONS
    --media movie      only movies (skip TV)
    --media tv         only TV (skip movies)
    --media both        (default) both movies and TV

==============================================================================
"""

import argparse
import csv
import datetime
import json
import os
import re
import sys
import time
import requests


def log(msg):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def checkpoint_path(output_path):
    return output_path + ".checkpoint.json"


def load_checkpoint(output_path):
    path = checkpoint_path(output_path)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def save_checkpoint(output_path, data):
    """Atomic-ish write: write to a temp file then rename, so a crash mid-write
    can't corrupt the checkpoint."""
    path = checkpoint_path(output_path)
    tmp_path = path + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    os.replace(tmp_path, path)

BASE_URL = "https://api.themoviedb.org/3"
MIN_VOTE_COUNT_MOVIE = 100   # filters out titles with only a handful of ratings
MIN_VOTE_COUNT_TV = 50
REQUEST_PAUSE = 0.25         # be polite to the API / stay under rate limits

MEDIA_LIST_URL = "https://raw.githubusercontent.com/rbrock44/home-page-media-file/master/media.txt"
# Matches "Some Title (1999)..." — non-greedy title capture so it skips over
# any other parenthesized text (e.g. "(Extended)") that isn't a 4-digit year.
MEDIA_LIST_YEAR_RE = re.compile(r"^(.*?)\((\d{4})\)")


def normalize_title(title):
    """Lowercase, strip punctuation, collapse whitespace — so 'Spider-Man:
    Homecoming' and 'Spider Man Homecoming' compare equal."""
    if not title:
        return ""
    title = title.lower()
    title = re.sub(r"[^a-z0-9]+", " ", title)
    return " ".join(title.split())


def fetch_media_library_text(url, local_path=None, timeout=20):
    """Fetch the media list, from a local cached copy if given and present,
    otherwise from the URL. Returns the raw text, or None on failure."""
    if local_path and os.path.exists(local_path):
        log(f"Loading media library list from local cache: {local_path}")
        with open(local_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    log(f"Downloading media library list from {url} ...")
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        text = resp.text
        if local_path:
            with open(local_path, "w", encoding="utf-8") as f:
                f.write(text)
        return text
    except requests.RequestException as e:
        log(f"Warning: couldn't download media library list ({e}). "
            f"The 'in_media_library' column will be left blank.")
        return None


def build_media_library_lookup(text):
    """
    Parses lines like 'Movie Title (1999) [1080p].mkv' into a dict:
        normalized_title -> set of years (as strings) seen for that title
    Lines without a '(YYYY)' pattern (most TV episode files) are skipped —
    they simply won't be matchable, which is fine since our TV rows are
    checked the same way and will just come back as not found.
    This is built once and used for fast in-memory O(1) lookups afterward.
    """
    lookup = {}
    if not text:
        return lookup
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        match = MEDIA_LIST_YEAR_RE.match(line)
        if not match:
            continue
        raw_title, year = match.group(1), match.group(2)
        norm = normalize_title(raw_title)
        if not norm:
            continue
        lookup.setdefault(norm, set()).add(year)
    return lookup


def is_in_media_library(lookup, title, year):
    """True/False if (title, year) matches an entry in the parsed media list.
    Returns '' (unknown) if the lookup itself failed to load."""
    if lookup is None:
        return ""
    if not title or not year:
        return False
    norm = normalize_title(title)
    years_for_title = lookup.get(norm)
    if not years_for_title:
        return False
    return str(year) in years_for_title


def api_get(path, api_key, params=None, retries=3):
    """GET wrapper with basic retry/backoff and error surfacing."""
    params = dict(params or {})
    params["api_key"] = api_key
    url = f"{BASE_URL}{path}"

    for attempt in range(retries):
        resp = requests.get(url, params=params, timeout=15)
        if resp.status_code == 200:
            time.sleep(REQUEST_PAUSE)
            return resp.json()
        if resp.status_code == 429:
            # Rate limited — wait for the amount of time TMDb tells us to.
            wait = int(resp.headers.get("Retry-After", 2))
            time.sleep(wait)
            continue
        if resp.status_code == 401:
            sys.exit("TMDb rejected the API key (401). Double-check --api-key / TMDB_API_KEY.")
        # Other errors: back off a little and retry
        time.sleep(1 + attempt)

    print(f"Warning: giving up on {url} with params {params} after {retries} retries", file=sys.stderr)
    return None


def top_titles_for_year(api_key, year, media_type, top_n, min_votes):
    """
    media_type: 'movie' or 'tv'
    Uses /discover to sort by rating for a given year, filtered by a minimum
    vote count so we get genuinely well-regarded titles, not obscure ones
    with a single 10/10 vote.

    TMDb returns 20 results per page, so this pages through as many times
    as needed to gather top_n results (e.g. top_n=100 -> up to 5 pages).
    """
    date_field = "primary_release_year" if media_type == "movie" else "first_air_date_year"
    path = f"/discover/{media_type}"
    results = []
    page = 1
    total_pages = 1

    while len(results) < top_n and page <= total_pages:
        params = {
            date_field: year,
            "sort_by": "vote_average.desc",
            "vote_count.gte": min_votes,
            "page": page,
        }
        data = api_get(path, api_key, params)
        if not data:
            break
        results.extend(data.get("results", []))
        total_pages = data.get("total_pages", 1)
        page += 1

    return results[:top_n]


def top_people(api_key, top_n):
    """Popular people list (actors/actresses/directors etc., we filter to acting dept below)."""
    people = []
    page = 1
    while len(people) < top_n:
        data = api_get("/person/popular", api_key, {"page": page})
        if not data or not data.get("results"):
            break
        for person in data["results"]:
            if person.get("known_for_department") == "Acting":
                people.append(person)
            if len(people) >= top_n:
                break
        page += 1
        if page > data.get("total_pages", 1):
            break
    return people[:top_n]


def top_credits_for_person(api_key, person_id, media_type, top_n, min_votes):
    """Pull a person's combined credits and return their top-rated ones for the given media_type."""
    data = api_get(f"/person/{person_id}/combined_credits", api_key)
    if not data:
        return []
    cast = [c for c in data.get("cast", []) if c.get("media_type") == media_type]
    cast = [c for c in cast if (c.get("vote_count") or 0) >= min_votes]
    cast.sort(key=lambda c: c.get("vote_average", 0), reverse=True)
    return cast[:top_n]


def get_year_of_credit(credit, media_type):
    date_str = credit.get("release_date") if media_type == "movie" else credit.get("first_air_date")
    return date_str[:4] if date_str else ""


def main():
    parser = argparse.ArgumentParser(description="Pull top movies/TV shows per year and top actors' top titles from TMDb.")
    parser.add_argument("--api-key", default=os.environ.get("TMDB_API_KEY"),
                         help="TMDb API key (or set TMDB_API_KEY env var)")
    parser.add_argument("--start-year", type=int, required=True)
    parser.add_argument("--end-year", type=int, required=True)
    parser.add_argument("--top-titles", type=int, default=10,
                         help="How many top movies/TV shows to pull per year (default 10)")
    parser.add_argument("--top-people", type=int, default=10,
                         help="How many top actors/actresses to pull overall (default 10)")
    parser.add_argument("--top-people-titles", type=int, default=5,
                         help="How many top movies/TV shows to pull per actor (default 5)")
    parser.add_argument("--media", choices=["movie", "tv", "both"], default="both",
                         help="Which media type(s) to include (default both)")
    parser.add_argument("--output", default="tmdb_top_lists.csv")
    parser.add_argument("--restart", action="store_true",
                         help="Ignore any existing checkpoint/output and start completely fresh.")
    parser.add_argument("--skip-media-check", action="store_true",
                         help="Skip the media-library lookup column entirely.")
    parser.add_argument("--media-list-url", default=MEDIA_LIST_URL,
                         help="URL of the media list file to check titles against.")
    parser.add_argument("--media-list-cache",
                         help="Optional local file path to cache the media list, "
                              "so repeated/resumed runs don't need to re-download it.")
    args = parser.parse_args()

    if not args.api_key:
        sys.exit("No API key provided. Use --api-key or set the TMDB_API_KEY environment variable.")

    media_types = ["movie", "tv"] if args.media == "both" else [args.media]
    num_years = args.end_year - args.start_year + 1
    fieldnames = ["section", "year", "person", "rank", "title", "media_type", "rating", "vote_count", "in_media_library"]

    run_settings = {
        "start_year": args.start_year, "end_year": args.end_year,
        "top_titles": args.top_titles, "top_people": args.top_people,
        "top_people_titles": args.top_people_titles, "media": args.media,
    }

    # --- Load or initialize checkpoint ---
    checkpoint = None if args.restart else load_checkpoint(args.output)

    if checkpoint and checkpoint.get("settings") != run_settings:
        log("Warning: existing checkpoint was made with different settings than this run.")
        log(f"  checkpoint settings: {checkpoint.get('settings')}")
        log(f"  this run's settings: {run_settings}")
        log("Ignoring the mismatched checkpoint and starting fresh (use --restart to skip this check).")
        checkpoint = None

    if args.restart:
        # Wipe any existing checkpoint/output so we truly start clean.
        cp_path = checkpoint_path(args.output)
        if os.path.exists(cp_path):
            os.remove(cp_path)
        if os.path.exists(args.output):
            os.remove(args.output)

    if checkpoint is None:
        checkpoint = {
            "settings": run_settings,
            "titles_done": [],   # list of "movie:1970" style keys already fully written
            "people": None,      # fixed list of {id, name, rank, popularity} once fetched
            "people_done": [],   # ids of people whose "top actor" row + all credits are written
        }
        resuming = False
    else:
        resuming = True
        log(f"Resuming from checkpoint: {len(checkpoint['titles_done'])} year/media combos already done, "
            f"{len(checkpoint['people_done'])} people already done.")

    titles_done = set(checkpoint["titles_done"])
    people_done = set(checkpoint["people_done"])

    # --- Build the media-library lookup once (fast in-memory dict, O(1) lookups) ---
    media_lookup = None
    if not args.skip_media_check:
        media_text = fetch_media_library_text(args.media_list_url, args.media_list_cache)
        media_lookup = build_media_library_lookup(media_text)
        if media_text is not None:
            log(f"Media library list parsed: {len(media_lookup)} unique titled entries with a year "
                f"(out of {len(media_text.splitlines())} total lines in the file).")

    # CSV: append if resuming into an existing file, otherwise start fresh with a header.
    file_mode = "a" if (resuming and os.path.exists(args.output)) else "w"
    write_header = file_mode == "w"

    with open(args.output, file_mode, newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
            f.flush()

        row_count = 0

        def write_row(row):
            nonlocal row_count
            writer.writerow(row)
            f.flush()
            row_count += 1

        # --- Section 1: Top titles per year ---
        for media_type in media_types:
            min_votes = MIN_VOTE_COUNT_MOVIE if media_type == "movie" else MIN_VOTE_COUNT_TV
            for i, year in enumerate(range(args.start_year, args.end_year + 1), start=1):
                key = f"{media_type}:{year}"
                if key in titles_done:
                    log(f"[{media_type}] year {year} ({i}/{num_years}) — already done, skipping.")
                    continue

                log(f"[{media_type}] year {year} ({i}/{num_years}) — fetching top {args.top_titles} titles...")
                titles = top_titles_for_year(args.api_key, year, media_type, args.top_titles, min_votes)
                for rank, t in enumerate(titles, start=1):
                    title = t.get("title") if media_type == "movie" else t.get("name")
                    write_row({
                        "section": f"Top {media_type.upper()} by Year",
                        "year": year,
                        "person": "",
                        "rank": rank,
                        "title": title,
                        "media_type": media_type,
                        "rating": t.get("vote_average"),
                        "vote_count": t.get("vote_count"),
                        "in_media_library": is_in_media_library(media_lookup, title, year),
                    })

                titles_done.add(key)
                checkpoint["titles_done"] = sorted(titles_done)
                save_checkpoint(args.output, checkpoint)
                log(f"[{media_type}] year {year} done — got {len(titles)} titles (running total rows: {row_count})")

        # --- Section 2: Top actors/actresses, and each one's top titles ---
        if checkpoint["people"] is None:
            log(f"Fetching top {args.top_people} popular actors/actresses...")
            fetched = top_people(args.api_key, args.top_people)
            checkpoint["people"] = [
                {"id": p["id"], "name": p.get("name"), "popularity": p.get("popularity")}
                for p in fetched
            ]
            save_checkpoint(args.output, checkpoint)
        else:
            log(f"Using {len(checkpoint['people'])} people already fetched from checkpoint.")

        people = checkpoint["people"]
        log(f"Now fetching each person's top credits ({len(people_done)}/{len(people)} already done)...")

        for rank, person in enumerate(people, start=1):
            person_id = person["id"]
            if person_id in people_done:
                log(f"({rank}/{len(people)}) {person['name']} — already done, skipping.")
                continue

            write_row({
                "section": "Top Actors/Actresses",
                "year": "",
                "person": person["name"],
                "rank": rank,
                "title": "",
                "media_type": "",
                "rating": "",
                "vote_count": person.get("popularity"),
                "in_media_library": "",
            })

            log(f"({rank}/{len(people)}) {person['name']} — fetching top credits...")
            for media_type in media_types:
                min_votes = MIN_VOTE_COUNT_MOVIE if media_type == "movie" else MIN_VOTE_COUNT_TV
                credits = top_credits_for_person(args.api_key, person_id, media_type,
                                                  args.top_people_titles, min_votes)
                for c_rank, c in enumerate(credits, start=1):
                    title = c.get("title") if media_type == "movie" else c.get("name")
                    credit_year = get_year_of_credit(c, media_type)
                    write_row({
                        "section": f"{person['name']}'s Top {media_type.upper()}",
                        "year": credit_year,
                        "person": person["name"],
                        "rank": c_rank,
                        "title": title,
                        "media_type": media_type,
                        "rating": c.get("vote_average"),
                        "vote_count": c.get("vote_count"),
                        "in_media_library": is_in_media_library(media_lookup, title, credit_year),
                    })

            people_done.add(person_id)
            checkpoint["people_done"] = sorted(people_done)
            save_checkpoint(args.output, checkpoint)

    log(f"Done. Wrote {row_count} new rows to {args.output} this run.")
    log(f"Checkpoint saved at {checkpoint_path(args.output)} "
        f"(delete it, or use --restart, if you ever want a completely fresh run).")


if __name__ == "__main__":
    main()