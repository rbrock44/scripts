declare -A shares=(
  ["Share1"]="//10.0.0.50/usbc"
  ["Share2"]="//10.0.0.50/usbd"
  ["Share3"]="//10.0.0.50/usbe"
  ["Share4"]="//10.0.0.50/usbf"
)

declare -A pushUrls=(
  ["Share1"]="http://10.0.0.150:3002/api/push/wa2OJhU5O3?status=up&msg=OK&ping="
  ["Share2"]="http://10.0.0.150:3002/api/push/sNXeytIaFv?status=up&msg=OK&ping="
  ["Share3"]="http://10.0.0.150:3002/api/push/Ww4943DDeU?status=up&msg=OK&ping="
  ["Share4"]="http://10.0.0.150:3002/api/push/N2Z0YLfMUv?status=up&msg=OK&ping="
)

for name in "${!shares[@]}"; do
  mountpoint="/mnt/check-$name"
  mkdir -p "$mountpoint"
  if mount -t cifs -o guest "${shares[$name]}" "$mountpoint" &> /dev/null; then
    curl -s "${pushUrls[$name]}" > /dev/null
    echo "$name is up"
    umount "$mountpoint"
  else
    echo "$name is down"
  fi
done
