<#
.SYNOPSIS
    Keeps a GitHub repo's scheduled Actions alive by pushing an empty commit
    before it hits 2 months (60 days) of inactivity.

.DESCRIPTION
    GitHub disables scheduled workflows after ~60 days without any commits
    to the repo. This script checks the last commit date of a local git
    clone and, if it's approaching the inactivity threshold, creates and
    pushes an empty commit to reset the clock.

    Intended to be wired into Windows Task Scheduler to run once a day.
    The machine running this must already have git configured/authenticated
    (e.g. via credential manager or SSH) so `git push` works non-interactively.

.PARAMETER RepoPath
    Path to the local clone of the repo to check/keep alive.

.PARAMETER ThresholdDays
    Number of days of inactivity to allow before pushing an empty commit.
    Defaults to 55 (a 5 day safety buffer before GitHub's 60 day cutoff).

.PARAMETER Branch
    Branch to check out, pull, and push to. Defaults to the repo's current branch.

.EXAMPLE
    .\Keep-Repo-Active.ps1 -RepoPath 'C:\workspace\drive-status'

.EXAMPLE
    .\Keep-Repo-Active.ps1 -RepoPath 'C:\workspace\drive-status' -ThresholdDays 50 -Branch 'master'
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$RepoPath,

    [int]$ThresholdDays = 55,

    [string]$Branch
)

function Write-Log {
    param([string]$Message)
    Write-Output "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
}

if (-not (Test-Path -Path $RepoPath)) {
    Write-Log "Repo path '$RepoPath' does not exist. Exiting."
    exit 1
}

Set-Location -Path $RepoPath

git rev-parse --is-inside-work-tree *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Log "'$RepoPath' is not a git repository. Exiting."
    exit 1
}

try {
    if ($Branch) {
        Write-Log "Checking out branch '$Branch'..."
        git checkout $Branch
        if ($LASTEXITCODE -ne 0) {
            Write-Log "Failed to checkout branch '$Branch'. Exiting."
            exit 1
        }
    }
    else {
        $Branch = (git rev-parse --abbrev-ref HEAD).Trim()
        Write-Log "No branch specified, using current branch '$Branch'."
    }

    Write-Log "Pulling latest changes for '$Branch'..."
    git pull --ff-only
    if ($LASTEXITCODE -ne 0) {
        Write-Log "Failed to pull latest changes. Exiting."
        exit 1
    }

    $lastCommitDateRaw = git log -1 --format=%cI
    if (-not $lastCommitDateRaw) {
        Write-Log "Could not determine last commit date. Exiting."
        exit 1
    }

    $lastCommitDate = [DateTimeOffset]::Parse($lastCommitDateRaw)
    $daysSinceLastCommit = (Get-Date) - $lastCommitDate.LocalDateTime

    Write-Log "Last commit was on $($lastCommitDate.LocalDateTime) ($([math]::Floor($daysSinceLastCommit.TotalDays)) days ago)."

    if ($daysSinceLastCommit.TotalDays -ge $ThresholdDays) {
        Write-Log "Inactivity threshold of $ThresholdDays days reached. Pushing empty keep-alive commit..."

        $today = Get-Date -Format 'yyyy/MM/dd HH:mm'
        git commit --allow-empty -m "chore: keep-alive commit $today"
        if ($LASTEXITCODE -ne 0) {
            Write-Log "Failed to create empty commit. Exiting."
            exit 1
        }

        git push
        if ($LASTEXITCODE -ne 0) {
            Write-Log "Failed to push commit. Exiting."
            exit 1
        }

        Write-Log "Keep-alive commit pushed successfully."
    }
    else {
        Write-Log "Repo is within the activity window ($ThresholdDays day threshold). No action needed."
    }
}
catch {
    Write-Log "Error: $($_.Exception.Message)"
    exit 1
}
