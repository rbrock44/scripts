#!/bin/bash
# Syncs every git repo directly under c:/workspace with its main/master branch,
# then restores whatever branch and uncommitted changes were there before.
# Only prints output for repos where something actually happened (a stash,
# a pull that updated the branch, or an error) - repos already up to date
# produce no output. Repos are synced in parallel.

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

pull_repo() {
    local repo="$1"
    local repo_name out_file
    repo_name=$(basename "$repo")
    out_file="$tmp_dir/$repo_name"
    cd "$repo" || return

    local noteworthy=0
    local lines=()

    local original_branch
    original_branch=$(git rev-parse --abbrev-ref HEAD)

    local stashed=0
    if [[ -n $(git status --porcelain) ]]; then
        if git stash push -u -m "pull-all-repos autostash" > /dev/null; then
            stashed=1
            noteworthy=1
            lines+=("$(warn "stashed local changes")")
        else
            noteworthy=1
            lines+=("$(error "stash failed (unresolved conflict?), leaving repo untouched")")
            {
                echo "${bold}${cyan}==> $repo_name${reset}"
                printf '%s\n' "${lines[@]}"
            } > "$out_file"
            return
        fi
    fi

    # Ask the remote which branch is actually its default, rather than
    # guessing from whichever of main/master happens to exist locally
    # (repos can have stray local branches for both after a rename).
    local main_branch
    main_branch=$(git ls-remote --symref origin HEAD 2>/dev/null | awk '/^ref:/ {sub("refs/heads/", "", $2); print $2}')

    if [ -z "$main_branch" ]; then
        if git show-ref --verify --quiet refs/heads/main; then
            main_branch="main"
        elif git show-ref --verify --quiet refs/heads/master; then
            main_branch="master"
        fi
    fi

    if [ -z "$main_branch" ]; then
        noteworthy=1
        lines+=("$(error "could not determine main/master branch, skipping pull")")
    else
        git checkout -q "$main_branch"
        local pull_output pull_status
        pull_output=$(git pull origin "$main_branch" 2>&1)
        pull_status=$?

        if [ $pull_status -ne 0 ]; then
            noteworthy=1
            lines+=("$(error "pull failed: $(echo "$pull_output" | tail -1)")")
        elif echo "$pull_output" | grep -q "Already up to date"; then
            : # nothing changed, nothing to report
        else
            noteworthy=1
            lines+=("$(ok "$main_branch updated")")
        fi

        if [ "$original_branch" != "$main_branch" ]; then
            git checkout -q "$original_branch"
        fi
    fi

    if [ "$stashed" -eq 1 ]; then
        if git stash pop > /dev/null 2>&1; then
            lines+=("$(warn "restored stashed changes")")
        else
            noteworthy=1
            lines+=("$(error "stash pop failed, changes remain stashed")")
        fi
    fi

    if [ "$noteworthy" -eq 1 ]; then
        {
            echo "${bold}${cyan}==> $repo_name${reset}"
            printf '%s\n' "${lines[@]}"
        } > "$out_file"
    fi
}

for repo in "$workspace_dir"/*/; do
    repo="${repo%/}"
    [ -d "$repo/.git" ] || continue

    pull_repo "$repo" &

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
    ok "All repos are up to date, nothing to pull."
fi
