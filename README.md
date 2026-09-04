# Scripts

> This project holds various scripts used in my ecosystem of processes and applications <br/>

---

## Table of Contents

- [What's My Purpose?](#whats-my-purpose)
- [How to Use](#how-to-use)
  - [List of Scripts](#list-of-scripts)
- [Technologies](#technologies)
- [Getting Started (Local Setup)](#getting-started-local-setup)
  - [Run Locally](#run-locally)
- [How to Contribute](#how-to-contribute)

---

## What's My Purpose?

This project holds various scripts used in my ecosystem of processes and applications. Its grown to include several technologies  

---

## How to Use

---

### List of Scripts

* Bash
  * Useful bash aliases that enhance my life. Move the following to C:\Users\<user>
    * .bashrc
    * .bash_profile
  * The alias list is mirrored in powershell/Microsoft.PowerShell_profile.ps1
  * pull-all-repos.sh
    * Syncs every repo under c:/workspace with its main/master branch, stashing and restoring local changes; run via the `pull-all` alias
  * status-all-repos.sh
    * Prints only the repos under c:/workspace that are dirty, ahead/behind, or have no upstream; run via the `status-all` alias
  * settings.example.json
    * Template for the per-machine settings both of those scripts read. Copy it to bash/settings.json, which is gitignored so it stays unique to the machine
    * `ignoredRepos` - repo folder names under c:/workspace to skip entirely; globs like `*-archive` work. Missing file, missing key, or an empty list means nothing is skipped
* Cloudflare-Workers
  * unknown-subdomain-redirect.ts
    * Catches requests to subdomains of ryan-brock.com that aren't in the allowed list and redirects them to `lost.ryan-brock.com?from=<subdomain>`; known subdomains pass straight through
    * Requires two pieces of Cloudflare config to actually fire:
      * A proxied wildcard DNS record (`AAAA  *  100::`, orange cloud) so unknown subdomains resolve to the edge instead of returning NXDOMAIN
      * A worker route of `*.ryan-brock.com/*` on the zone
    * Add new subdomains to `allowedSubdomains` when they go live, otherwise they'll get bounced to lost
  * blog-counters.ts
    * View and like counts for (blog)[https://blog.ryan-brock.com/], stored in Workers KV. The only live service the blog has - if it's down or unconfigured the post still reads fine and the counter just doesn't render
    * `GET /api/counts/:slug`, `POST /api/views/:slug`, `POST /api/likes/:slug`
    * Requires three pieces of Cloudflare config:
      * A worker route of `blog.ryan-brock.com/api/*` on the zone. This is more specific than `*.ryan-brock.com/*`, so it wins and unknown-subdomain-redirect never sees these requests
      * A KV namespace bound as `COUNTERS`
      * `blog` present in unknown-subdomain-redirect's `allowedSubdomains` so the rest of the site isn't bounced to lost
    * Likes are idempotent and views are deduped for 24h against a hashed visitor id; known crawler user-agents are ignored so the numbers aren't mostly Googlebot. Raw IPs are never stored
    * After deploying, set `countersApi` to `/api` in the blog's `src/site.config.json` and rebuild
* Home-Media
  * driveStatusRun.ps1
    * Should be synced with task scheduler to get retrieve automatic git pushes of (drive-status's)[https://github.com/rbrock44/drive-status], kicks off smbConnectionResults.ps1
  * smbConnectionResults.ps1
    * Reads and outputs the status's of various Open Media Vault drives      
* Powershell
  * Microsoft.PowerShell_profile.ps1
    * Prompt setup plus the aliases above. Move to C:\Users\<user>\Documents\PowerShell
    * `Set-Alias` only takes a command name, not a command line, so anything taking arguments is a function with an alias pointing at it
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

## Technologies

- Bash
- Powershell
- Javascript
- Typescript
- Cloudflare Workers

---

## Getting Started (Local Setup)

* Install [node](https://nodejs.org/en)
* Clone [repo](https://github.com/rbrock44/scripts)

---

### Run Locally

Run a script in the appropiate terminal

---

## How to Contribute

Found a typo or a small, obvious fix? Open a PR directly.
Want to change behavior or add something bigger? Open an issue first so we can talk it through before you put in the work.

---
