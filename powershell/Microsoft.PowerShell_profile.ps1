oh-my-posh init pwsh --config "C:\workspace\scripts\ohmyposh\ohmyposh.json" | Invoke-Expression

$env:DOTNET_CLI_TELEMETRY_OPTOUT=1

Set-Alias -Name dotnet86 -Value "C:\Program Files (x86)\dotnet\dotnet.exe"
Set-Alias -Name g -Value git

# Aliases below mirror bash/.bashrc - keep the two in sync.

function Set-WorkspaceLocation { Set-Location C:\workspace }
Set-Alias work Set-WorkspaceLocation

function Invoke-GitPull { git pull @args }
Set-Alias gpull Invoke-GitPull

function Invoke-GitPush { git push @args }
Set-Alias gpush Invoke-GitPush

function Invoke-GitPushNew {
    git push --set-upstream origin $(git rev-parse --abbrev-ref HEAD)
}
Set-Alias gpushn Invoke-GitPushNew

# bash also aliases gc to git checkout; here gc stays Get-Content and gco is used instead.
function Invoke-GitCheckout { git checkout @args }
Set-Alias gco Invoke-GitCheckout

function Invoke-GitAddAll { git add . }
Set-Alias ga Invoke-GitAddAll

# bash also aliases gcm to git commit -m; here gcm stays Get-Command and gcmsg is used instead.
function Invoke-GitCommitMessage { git commit -m @args }
Set-Alias gcmsg Invoke-GitCommitMessage

function Invoke-GitResetHardUpstream { git reset --hard '@{u}' }
Set-Alias gro Invoke-GitResetHardUpstream

function Invoke-NpmProd { npm run prod }
Set-Alias prod Invoke-NpmProd

function Invoke-PullAllRepos {
    bash "C:\workspace\scripts\bash\pull-all-repos.sh"
}
Set-Alias pull-all Invoke-PullAllRepos

function Invoke-StatusAllRepos {
    bash "C:\workspace\scripts\bash\status-all-repos.sh"
}
Set-Alias status-all Invoke-StatusAllRepos

Import-Module -Name Terminal-Icons
Import-Module PSReadLine 
Set-PSReadLineKeyHandler -Chord "Ctrl+f" -Function ForwardWord
