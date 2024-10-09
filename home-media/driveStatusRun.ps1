Set-Location -Path 'C:\workspace\drive-status'
if (-not (Test-Path .)) { exit }

git stash
git checkout master
git pull

Set-Location -Path 'C:\workspace\scripts'
if (-not (Test-Path .)) { exit }

git pull
cd home-media
.\smbConnectionResults.ps1

Set-Location -Path 'C:\workspace\drive-status'
if (-not (Test-Path .)) { exit }

git add .
$today = Get-Date -Format "yyyy/MM/dd HH:mm"
git commit -m "drive status from $today"
git push