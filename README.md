# Scripts Readme

This repo hold various scripts used in my ecosystem of processes and applications

<br/>

## List of Scripts

* Bash
  * .bashrc
    * Useful bash aliases that enhance my life
* Home-Media
  * driveStatusRun.ps1
    * Should be synced with task scheduler to get retrieve automatic git pushes of (drive-status's)[https://github.com/rbrock44/drive-status], kicks off smbConnectionResults.ps1
  * smbConnectionResults.ps1
    * Reads and outputs the status's of various Open Media Vault drives      
* s01
  * bootHPA.sh
    * Will launch/run the Home-Page-Api application     
  * serveHP.sh
    * Will launch/run the Home-Page web application
* windows
  * home-page-media-uploader.sh
    * Reads media files from Open Media Vault drive folders and pushed to github repo (media-file)[(https://github.com/rbrock44/home-page-media-file)]
