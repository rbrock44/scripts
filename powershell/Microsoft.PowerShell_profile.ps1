oh-my-posh init pwsh --config "C:\workspace\scripts\ohmyposh\ohmyposh.json" | Invoke-Expression

$env:DOTNET_CLI_TELEMETRY_OPTOUT=1

Set-Alias -Name dotnet86 -Value "C:\Program Files (x86)\dotnet\dotnet.exe"
Set-Alias -Name work  -Value "Set-Location C:\workspace"
Set-Alias -Name g     -Value "git"
Set-Alias -Name ga     -Value "git add ."

Set-Alias -Name prod     -Value "npm run prod"

function gpushn {
    git push --set-upstream origin $(git rev-parse --abbrev-ref HEAD)
}
Set-Alias gpushn gpushn

function pull-all {
    bash "C:\workspace\scripts\bash\pull-all-repos.sh"
}
Set-Alias pull-all pull-all

function status-all {
    bash "C:\workspace\scripts\bash\status-all-repos.sh"
}
Set-Alias status-all status-all

Import-Module -Name Terminal-Icons
Import-Module PSReadLine 
Set-PSReadLineKeyHandler -Chord "Ctrl+f" -Function ForwardWord
