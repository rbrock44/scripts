#!/bin/bash
# Syncs every git repo directly under c:/workspace with its main/master branch,
# then restores whatever branch and uncommitted changes were there before.

workspace_dir="/c/workspace"

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

for repo in "$workspace_dir"/*/; do
    repo="${repo%/}"
    [ -d "$repo/.git" ] || continue

    repo_name=$(basename "$repo")
    echo "${bold}${cyan}==> $repo_name${reset}"
    cd "$repo" || continue

    original_branch=$(git rev-parse --abbrev-ref HEAD)

    stashed=0
    if [[ -n $(git status --porcelain) ]]; then
        if git stash push -u -m "sync-all-repos autostash" > /dev/null; then
            stashed=1
            warn "stashed local changes"
        else
            error "stash failed (unresolved conflict?), leaving repo untouched"
            continue
        fi
    fi

    # Ask the remote which branch is actually its default, rather than
    # guessing from whichever of main/master happens to exist locally
    # (repos can have stray local branches for both after a rename).
    main_branch=$(git ls-remote --symref origin HEAD 2>/dev/null | awk '/^ref:/ {sub("refs/heads/", "", $2); print $2}')

    if [ -z "$main_branch" ]; then
        if git show-ref --verify --quiet refs/heads/main; then
            main_branch="main"
        elif git show-ref --verify --quiet refs/heads/master; then
            main_branch="master"
        fi
    fi

    if [ -z "$main_branch" ]; then
        error "could not determine main/master branch, skipping pull"
    else
        git checkout -q "$main_branch"
        pull_output=$(git pull origin "$main_branch" 2>&1)
        pull_status=$?

        if [ $pull_status -ne 0 ]; then
            error "pull failed: $(echo "$pull_output" | tail -1)"
        elif echo "$pull_output" | grep -q "Already up to date"; then
            info "$main_branch up to date"
        else
            ok "$main_branch updated"
        fi

        if [ "$original_branch" != "$main_branch" ]; then
            git checkout -q "$original_branch"
        fi
    fi

    if [ "$stashed" -eq 1 ]; then
        if git stash pop > /dev/null 2>&1; then
            warn "restored stashed changes"
        else
            error "stash pop failed, changes remain stashed"
        fi
    fi
done
