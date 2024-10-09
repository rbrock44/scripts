#!/bin/bash

# Function to check if a Samba share is accessible
check_samba_share() {
    share_path="$1"
    smbclient -L "$share_path" -N >/dev/null 2>&1 && echo "Accessible" || echo "Inaccessible"
}

# Get current datetime in hours and minutes
datetime=$(date +"%H:%M")

# List of Samba share paths to check
share1="//10.0.0.50/usbc"
share2="//10.0.0.50/usbd"
share3="//10.0.0.50/usbe"
share4="//10.0.0.50/usbf"

# Check each Samba share
share1_status=$(check_samba_share "$share1")
share2_status=$(check_samba_share "$share2")
share3_status=$(check_samba_share "$share3")
share4_status=$(check_samba_share "$share4")

# Output datetime and Samba share statuses
echo "$datetime, $share1: $share1_status, $share2: $share2_status, $share3: $share3_status, $share4: $share4_status"
