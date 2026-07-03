# Scripts

> This project holds various scripts used in my ecosystem of processes and applications <br/>

---

## 📚 Table of Contents

- [What's My Purpose?](#-whats-my-purpose)
- [How to Use](#-how-to-use)
  - [List of Scripts](#list-of-scripts)
- [Technologies](#-technologies)
- [Getting Started (Local Setup)](#-getting-started-local-setup)
  - [Run Locally](#run-locally)

---

## 🧠 What's My Purpose?

This project holds various scripts used in my ecosystem of processes and applications. Its grown to include several technologies  

---

## 🚦 How to Use

---

### List of Scripts

* Bash
  * Useful bash aliases that enhance my life. Move the following to C:\Users\<user>
    * .bashrc
    * .bash_profile
* Home-Media
  * driveStatusRun.ps1
    * Should be synced with task scheduler to get retrieve automatic git pushes of (drive-status's)[https://github.com/rbrock44/drive-status], kicks off smbConnectionResults.ps1
  * smbConnectionResults.ps1
    * Reads and outputs the status's of various Open Media Vault drives      
* Powershell
  * Keep-Repo-Active.ps1
    * Wired into Task Scheduler to run daily; checks a local repo clone's last commit date and pushes an empty commit once it nears 2 months of inactivity, so scheduled GitHub Actions keep running
  * Stop-ServiceByName.ps1
    * Stops a given Windows service by name, waiting for it to fully stop
* s01
  * bootHPA.sh
    * Will launch/run the Home-Page-Api application
  * check-smb.sh
    * Checks media shares and uploads to local uptime-kuma instance    
  * serveHP.sh
    * Will launch/run the Home-Page web application
* Tampermonkey
  * family-recipe-author-scraper.js
    * Grabs all unique authors from (family recipe website)[https://family-recipes.ryan-brock.com/]
  * youtube-continuer.js
    * Automatically clicks the youtube resume playing popup for uninterrupted watching/listening
  * Job Scraping Scripts
    * The following are scripts that add a career button (that googles searches company name careers) and a button to copy excel data (it formats data to fit my personal job tracking excel sheet)
      * indeed-job-scraper-and-careers-button.js
      * indeed-jobs-careers-button.js
      * linkedin-careers-button.js
      * linkedin-job-scraper.js
      * workday-job-scraper.js
      * ziprecruiter-jobs.scraper-and-careers-button.js
* windows
  * home-page-media-uploader.sh
    * Reads media files from Open Media Vault drive folders and pushed to github repo (media-file)[(https://github.com/rbrock44/home-page-media-file)]

---

## 🛠 Technologies

- Bash
- Powershell
- Javascript

---

## 🚀 Getting Started (Local Setup)

* Install [node](https://nodejs.org/en)
* Clone [repo](https://github.com/rbrock44/scripts)

---

### Run Locally

Run a script in the appropiate terminal

---
