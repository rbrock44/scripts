#!/bin/bash
# Syncs every git repo directly under c:/workspace with its main/master branch,
# then restores whatever branch and uncommitted changes were there before.

workspace_dir="/c/workspace"

for repo in "$workspace_dir"/*/; do
    repo="${repo%/}"
    [ -d "$repo/.git" ] || continue

    repo_name=$(basename "$repo")
    echo "==> $repo_name"
    cd "$repo" || continue

    original_branch=$(git rev-parse --abbrev-ref HEAD)

    stashed=0
    if [[ -n $(git status --porcelain) ]]; then
        git stash push -u -m "sync-all-repos autostash" || { echo "    stash failed, skipping"; continue; }
        stashed=1
    fi

    main_branch=""
    if git show-ref --verify --quiet refs/heads/main; then
        main_branch="main"
    elif git show-ref --verify --quiet refs/heads/master; then
        main_branch="master"
    fi

    if [ -z "$main_branch" ]; then
        echo "    no main or master branch found, skipping pull"
    else
        git checkout "$main_branch"
        git pull

        if [ "$original_branch" != "$main_branch" ]; then
            git checkout "$original_branch"
        fi
    fi

    if [ "$stashed" -eq 1 ]; then
        git stash pop
    fi
done
