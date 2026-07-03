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
    irm https://raw.githubusercontent.com/rbrock44/scripts/main/Setup-NewPC.ps1 | iex
    Downloads and runs the script directly on a brand-new PC that doesn't
    have this repo cloned yet. Run from an elevated PowerShell prompt.
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [switch]$IncludeCore = $true,
    [switch]$IncludeBrowsers = $true,
    [switch]$IncludeDevTools = $true,
    [switch]$IncludeUtilities = $true,
    [switch]$IncludeCommunication,
    [switch]$IncludeMedia,
    [switch]$IncludeGaming,
    [switch]$IncludeCloudStorage
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

    Media = [ordered]@{
        Enabled  = $IncludeMedia
        Packages = [ordered]@{
            'VLC media player' = 'VideoLAN.VLC'
        }
    }

    Gaming = [ordered]@{
        Enabled  = $IncludeGaming
        Packages = [ordered]@{
            'Steam'                = 'Valve.Steam'
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

Write-Host "Done. Some apps may need a sign-in or reboot to finish setup." -ForegroundColor Green
