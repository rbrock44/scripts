#!/bin/bash

declare -A shares=(
  ["usbc"]="//10.0.0.50/usbc"
  ["usbd"]="//10.0.0.50/usbd"
  ["usbe"]="//10.0.0.50/usbe"
  ["usbf"]="//10.0.0.50/usbf"
)

declare -A pushUrls=(
  ["usbc"]="http://10.0.0.150:3002/api/push/wa2OJhU5O3?status=up&msg=OK&ping="
  ["usbd"]="http://10.0.0.150:3002/api/push/sNXeytIaFv?status=up&msg=OK&ping="
  ["usbe"]="http://10.0.0.150:3002/api/push/Ww4943DDeU?status=up&msg=OK&ping="
  ["usbf"]="http://10.0.0.150:3002/api/push/N2Z0YLfMUv?status=up&msg=OK&ping="
)

datetime=$(date '+%Y-%m-%d %H:%M:%S')

for name in "${!shares[@]}"; do
  mountpoint="/mnt/check-$name"
  mkdir -p "$mountpoint"
  if mount -t cifs -o guest "${shares[$name]}" "$mountpoint" &> /dev/null; then
    curl -s "${pushUrls[$name]}" > /dev/null
    echo "$name is up - $datetime"
    umount "$mountpoint"
  else
    echo "$name is down - $datetime"
  fi
done
