Set-Location -Path 'C:\workspace\drive-status'
if (-not (Test-Path .)) { exit }

# Stash any changes and pull the latest from the master branch
git stash
git checkout master
git pull

Set-Location -Path 'C:\workspace\scripts\home-media'
if (-not (Test-Path .)) { exit }

git stash
git checkout master
git pull
.\smbConnectionResults.ps1  # Replace with the actual script name

Set-Location -Path 'C:\workspace\drive-status'
if (-not (Test-Path .)) { exit }

# Add changes, commit, and push
git add .
$today = Get-Date -Format "yyyy/MM/dd HH:mm"
git commit -m "drive status from $today"
git push
