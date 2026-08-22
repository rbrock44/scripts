<#
.SYNOPSIS
    Bootstraps a fresh Windows install with winget packages.

.DESCRIPTION
    Installs a curated set of applications via winget, grouped into categories.
    Toggle categories on/off using the switches below, or edit the package
    arrays directly to add/remove individual apps.

    Package IDs were derived from `winget list` on rbrock44's existing machine.
    Trim/expand the lists to taste.

.EXAMPLE
    .\Setup-NewPC.ps1
    Installs Core, Browsers, DevTools, and Utilities (the defaults).

.EXAMPLE
    .\Setup-NewPC.ps1 -IncludeGaming -IncludeCommunication
    Also installs gaming launchers and chat apps.

.EXAMPLE
    .\Setup-NewPC.ps1 -WhatIf
    Shows what would be installed without installing anything.

.EXAMPLE
    .\Setup-NewPC.ps1 -CloneRepos All
    Skips the interactive checklist and clones every repo under $GitHubUser
    into $WorkspaceDir. -CloneRepos None skips repo cloning entirely.

.EXAMPLE
    irm https://raw.githubusercontent.com/rbrock44/scripts/main/Setup-NewPC.ps1 | iex
    Downloads and runs the script directly on a brand-new PC that doesn't
    have this repo cloned yet, using every default. Run from an elevated
    PowerShell prompt. `irm | iex` can't take parameters - see below for
    passing switches without cloning first.

.EXAMPLE
    & ([scriptblock]::Create((irm https://raw.githubusercontent.com/rbrock44/scripts/main/Setup-NewPC.ps1))) -IncludeGaming -IncludeCommunication
    Same download-and-run, but with parameters. Wrapping the downloaded
    script in a scriptblock and invoking it with & lets you pass any of
    this script's switches without saving it to disk first.

.EXAMPLE
    & ([scriptblock]::Create((irm https://raw.githubusercontent.com/rbrock44/scripts/main/Setup-NewPC.ps1))) -CloneRepos All
    Download-and-run that also clones every repo under $GitHubUser into
    $WorkspaceDir, skipping the interactive checklist.

.EXAMPLE
    & ([scriptblock]::Create((irm https://raw.githubusercontent.com/rbrock44/scripts/main/Setup-NewPC.ps1))) -WhatIf
    Download-and-run in preview mode - shows what would be installed/cloned
    without doing it.
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [switch]$IncludeCore = $true,
    [switch]$IncludeBrowsers = $true,
    [switch]$IncludeDevTools = $true,
    [switch]$IncludeUtilities = $true,
    [switch]$IncludeCommunication,
    [switch]$IncludeGaming,

    [switch]$IncludeRepoSetup = $true,
    [string]$GitHubUser = 'rbrock44',
    [string]$WorkspaceDir = 'C:\workspace',
    [ValidateSet('Prompt', 'All', 'None')]
    [string]$CloneRepos = 'Prompt'
)

$ErrorActionPreference = 'Stop'

# ---------------------------------------------------------------------------
# Package catalog (Name = winget Id)
# ---------------------------------------------------------------------------

$Categories = [ordered]@{
    Core = [ordered]@{
        Enabled  = $IncludeCore
        Packages = [ordered]@{
            '7-Zip'              = '7zip.7zip'
            'PowerShell 7'       = 'Microsoft.PowerShell'
            'Windows Terminal'   = 'Microsoft.WindowsTerminal'
            'PowerToys'          = 'Microsoft.PowerToys'
            'Oh My Posh'         = 'JanDeDobbeleer.OhMyPosh'
            'VLC media player'   = 'VideoLAN.VLC'
            'Obsidian'           = 'Obsidian.Obsidian'
            'Kodi'               = 'XBMCFoundation.Kodi'
        }
    }

    Browsers = [ordered]@{
        Enabled  = $IncludeBrowsers
        Packages = [ordered]@{
            'Google Chrome' = 'Google.Chrome'
            'Mozilla Firefox' = 'Mozilla.Firefox'
        }
    }

    DevTools = [ordered]@{
        Enabled  = $IncludeDevTools
        Packages = [ordered]@{
            'Git'                  = 'Git.Git'
            'GitHub CLI'           = 'GitHub.cli'
            'Visual Studio Code'   = 'Microsoft.VisualStudioCode'
            'Windows Subsystem for Linux' = 'Microsoft.WSL'
            'NVM for Windows'      = 'CoreyButler.NVMforWindows'
            'Python 3.12'          = 'Python.Python.3.12'
            'Docker Desktop'       = 'Docker.DockerDesktop'
            'DBeaver Community'    = 'DBeaver.DBeaver.Community'
        }
    }

    Utilities = [ordered]@{
        Enabled  = $IncludeUtilities
        Packages = [ordered]@{
            'Notepad++'            = 'Notepad++.Notepad++'
            'PuTTY'                = 'PuTTY.PuTTY'
        }
    }

    Communication = [ordered]@{
        Enabled  = $IncludeCommunication
        Packages = [ordered]@{
            'Discord'         = 'Discord.Discord'
        }
    }

    Gaming = [ordered]@{
        Enabled  = $IncludeGaming
        Packages = [ordered]@{
            'Steam'                = 'Valve.Steam'
            'Epic Games Launcher'  = 'EpicGames.EpicGamesLauncher'
        }
    }
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

function Test-WingetAvailable {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw "winget was not found. Install 'App Installer' from the Microsoft Store, then re-run this script."
    }
}

function Test-PackageInstalled {
    param([Parameter(Mandatory)][string]$Id)
    $result = winget list --id $Id --exact --accept-source-agreements 2>$null
    return ($LASTEXITCODE -eq 0) -and ($result -match [regex]::Escape($Id))
}

function Install-WingetPackage {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$Id
    )

    if (Test-PackageInstalled -Id $Id) {
        Write-Host "  [skip]    $Name ($Id) already installed" -ForegroundColor DarkGray
        return
    }

    if ($PSCmdlet.ShouldProcess("$Name ($Id)", "winget install")) {
        Write-Host "  [install] $Name ($Id)" -ForegroundColor Cyan
        winget install --id $Id --exact --silent `
            --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "  Failed to install $Name ($Id) - exit code $LASTEXITCODE"
        }
    }
}

function Test-GhAvailable {
    if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
        Write-Warning "  GitHub CLI (gh) not found - skipping repo checklist. Install it via the DevTools category and re-run."
        return $false
    }
    $null = gh auth status 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "  gh is not authenticated - run 'gh auth login' then re-run to select repos to clone."
        return $false
    }
    return $true
}

function Invoke-GitClone {
    param(
        [Parameter(Mandatory)][string]$RepoUrl,
        [Parameter(Mandatory)][string]$Destination
    )

    $repoName = Split-Path $Destination -Leaf

    if (Test-Path $Destination) {
        Write-Host "  [skip]    $repoName already cloned" -ForegroundColor DarkGray
        return
    }

    if ($PSCmdlet.ShouldProcess($repoName, "git clone")) {
        Write-Host "  [clone]   $repoName" -ForegroundColor Cyan
        git clone --quiet $RepoUrl $Destination
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "  Failed to clone $repoName - exit code $LASTEXITCODE"
        }
    }
}

# Interactive terminal checklist: Up/Down to move, Space to toggle the repo
# under the cursor, A/N as shortcuts for select-all/select-none, Enter to
# continue. -CloneRepos All/None bypass this entirely for non-interactive runs.
function Show-RepoChecklist {
    param(
        [Parameter(Mandatory)][string[]]$Items,
        [string]$Title = 'Select repos to clone'
    )

    if ($Items.Count -eq 0) { return @() }

    $selected = [System.Collections.Generic.HashSet[int]]::new()
    0..($Items.Count - 1) | ForEach-Object { [void]$selected.Add($_) }
    $cursor = 0
    $originalCursorVisible = [Console]::CursorVisible
    [Console]::CursorVisible = $false

    try {
        :selectionLoop while ($true) {
            Clear-Host
            Write-Host $Title -ForegroundColor Yellow
            Write-Host "  Up/Down move   Space toggle   A select all   N select none   Enter continue`n" -ForegroundColor DarkGray

            for ($i = 0; $i -lt $Items.Count; $i++) {
                $box = if ($selected.Contains($i)) { '[x]' } else { '[ ]' }
                $prefix = if ($i -eq $cursor) { '>' } else { ' ' }
                $color = if ($i -eq $cursor) { 'Cyan' } else { 'White' }
                Write-Host ("$prefix $box $($Items[$i])") -ForegroundColor $color
            }

            $key = [Console]::ReadKey($true)
            switch ($key.Key) {
                'UpArrow'   { $cursor = [Math]::Max(0, $cursor - 1) }
                'DownArrow' { $cursor = [Math]::Min($Items.Count - 1, $cursor + 1) }
                'Spacebar'  {
                    if ($selected.Contains($cursor)) { [void]$selected.Remove($cursor) }
                    else { [void]$selected.Add($cursor) }
                }
                'A' { 0..($Items.Count - 1) | ForEach-Object { [void]$selected.Add($_) } }
                'N' { $selected.Clear() }
                'Enter' { break selectionLoop }
            }
        }
    } finally {
        [Console]::CursorVisible = $originalCursorVisible
        Clear-Host
    }

    $result = @()
    for ($i = 0; $i -lt $Items.Count; $i++) {
        if ($selected.Contains($i)) { $result += $Items[$i] }
    }
    return $result
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

Test-WingetAvailable

Write-Host "`nWinget New-PC Setup" -ForegroundColor Green
Write-Host "====================`n"

foreach ($categoryName in $Categories.Keys) {
    $category = $Categories[$categoryName]
    if (-not $category.Enabled) {
        Write-Host "Skipping category: $categoryName (disabled)" -ForegroundColor DarkGray
        continue
    }

    Write-Host "Category: $categoryName" -ForegroundColor Yellow
    foreach ($name in $category.Packages.Keys) {
        Install-WingetPackage -Name $name -Id $category.Packages[$name]
    }
    Write-Host ""
}

# ---------------------------------------------------------------------------
# Workspace repo setup
# ---------------------------------------------------------------------------

if ($IncludeRepoSetup) {
    Write-Host "Workspace repo setup" -ForegroundColor Yellow

    if (-not (Test-Path $WorkspaceDir)) {
        New-Item -ItemType Directory -Path $WorkspaceDir -Force | Out-Null
    }

    Invoke-GitClone -RepoUrl "https://github.com/$GitHubUser/scripts.git" -Destination (Join-Path $WorkspaceDir 'scripts')

    if (Test-GhAvailable) {
        $repoNames = gh repo list $GitHubUser --limit 500 --json name --jq '.[].name' 2>$null |
            Where-Object { $_ -ne 'scripts' } | Sort-Object

        if (-not $repoNames) {
            Write-Warning "  No repos found for $GitHubUser (or the request failed) - skipping."
        } else {
            $toClone = switch ($CloneRepos) {
                'All'    { $repoNames }
                'None'   { @() }
                default  { Show-RepoChecklist -Items $repoNames -Title "Select repos to clone into $WorkspaceDir" }
            }

            if ($toClone.Count -eq 0) {
                Write-Host "  No repos selected." -ForegroundColor DarkGray
            } else {
                foreach ($repoName in $toClone) {
                    Invoke-GitClone -RepoUrl "https://github.com/$GitHubUser/$repoName.git" -Destination (Join-Path $WorkspaceDir $repoName)
                }
            }
        }
    }

    Write-Host ""
}

Write-Host "Done. Some apps may need a sign-in or reboot to finish setup." -ForegroundColor Green
