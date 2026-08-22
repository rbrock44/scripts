#!/bin/bash
# Shows the git status of every repo directly under c:/workspace that has
# something worth reporting: an unclean working tree, no upstream, or a
# branch that's ahead/behind its upstream. Repos that are clean and up to
# date are omitted entirely. Repos are checked in parallel.

workspace_dir="/c/workspace"
max_jobs=8

bold=$'\e[1m'
cyan=$'\e[36m'
green=$'\e[32m'
yellow=$'\e[33m'
red=$'\e[31m'
gray=$'\e[90m'
reset=$'\e[0m'

info()   { echo "  ${gray}$1${reset}"; }
ok()     { echo "  ${green}$1${reset}"; }
warn()   { echo "  ${yellow}$1${reset}"; }
error()  { echo "  ${red}$1${reset}"; }

tmp_dir=$(mktemp -d)
trap 'rm -rf "$tmp_dir"' EXIT

check_repo() {
    local repo="$1"
    local repo_name out_file
    repo_name=$(basename "$repo")
    out_file="$tmp_dir/$repo_name"
    cd "$repo" || return

    local branch upstream status_output
    branch=$(git rev-parse --abbrev-ref HEAD)
    upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null)
    status_output=$(git status --porcelain)

    local branch_line="" branch_line_fn=info noteworthy=0

    if [ -z "$upstream" ]; then
        branch_line="$branch (no upstream)"
        branch_line_fn=warn
        noteworthy=1
    else
        local ahead_behind behind ahead
        ahead_behind=$(git rev-list --left-right --count "$upstream...HEAD" 2>/dev/null)
        behind=$(echo "$ahead_behind" | awk '{print $1}')
        ahead=$(echo "$ahead_behind" | awk '{print $2}')

        if [ "$ahead" -eq 0 ] && [ "$behind" -eq 0 ]; then
            branch_line="$branch (up to date with $upstream)"
            branch_line_fn=info
        else
            noteworthy=1
            branch_line_fn=warn
            [ "$ahead" -gt 0 ] && [ "$behind" -gt 0 ] && branch_line="$branch (ahead $ahead, behind $behind)"
            [ "$ahead" -gt 0 ] && [ "$behind" -eq 0 ] && branch_line="$branch (ahead $ahead)"
            [ "$ahead" -eq 0 ] && [ "$behind" -gt 0 ] && branch_line="$branch (behind $behind)"
        fi
    fi

    local status_line status_line_fn
    if [ -z "$status_output" ]; then
        status_line="clean"
        status_line_fn=ok
    else
        local dirty_count
        dirty_count=$(echo "$status_output" | wc -l)
        status_line="dirty ($dirty_count file(s) changed)"
        status_line_fn=error
        noteworthy=1
    fi

    if [ "$noteworthy" -eq 1 ]; then
        {
            echo "${bold}${cyan}==> $repo_name${reset}"
            "$branch_line_fn" "$branch_line"
            "$status_line_fn" "$status_line"
        } > "$out_file"
    fi
}

for repo in "$workspace_dir"/*/; do
    repo="${repo%/}"
    [ -d "$repo/.git" ] || continue

    check_repo "$repo" &

    while [ "$(jobs -r -p | wc -l)" -ge "$max_jobs" ]; do
        wait -n
    done
done

wait

any_noteworthy=0
for repo in "$workspace_dir"/*/; do
    repo="${repo%/}"
    [ -d "$repo/.git" ] || continue
    repo_name=$(basename "$repo")
    if [ -s "$tmp_dir/$repo_name" ]; then
        any_noteworthy=1
        cat "$tmp_dir/$repo_name"
    fi
done

if [ "$any_noteworthy" -eq 0 ]; then
    ok "All repos are clean and up to date."
fi
