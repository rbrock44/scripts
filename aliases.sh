#!/bin/bash

# add these to the .bashrc file
alias work='cd /c/workspace/'
alias g=git
alias gpull='git pull'
alias gpush='git push'
alias gpushn='git push --set-upstream origin $(git rev-parse --abbrev-ref HEAD)'
alias gc='git checkout'
alias ga='git add .'
alias gcm='git commit -m'
alias prod='npm run prod'