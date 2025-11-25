oh-my-posh init pwsh --config "C:\workspace\scripts\ohmyposh\ohmyposh.json" | Invoke-Expression

$env:DOTNET_CLI_TELEMETRY_OPTOUT=1

Set-Alias -Name dotnet86 -Value "C:\Program Files (x86)\dotnet\dotnet.exe"
Set-Alias -Name work  -Value "Set-Location C:\workspace"
Set-Alias -Name g     -Value "git"
Set-Alias -Name ga     -Value "git add ."

Set-Alias -Name prod     -Value "npm run prod"

Import-Module -Name Terminal-Icons
Import-Module PSReadLine 
Set-PSReadLineKeyHandler -Chord "Ctrl+f" -Function ForwardWord
