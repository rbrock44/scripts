#!/bin/bash

# List of directories containing .gcode files
directories=(
    # "/C/workspace/scripts" # testomg directory
    "//10.0.0.5/octoprint/uploads"
    "//10.0.0.50/usbc/3D Prints/PLA/Ender 3 v2"
)

for directory in "${directories[@]}"; do
    echo $directory
    cd "$directory" || continue

    # Loop through all .gcode files in the directory
    while IFS= read -r -d '' file; do
        # Check if the file contains the target line and the following line
        if grep -q "G28 ; Home all axes" "$file" && ! grep -q "G29 ;" "$file"; then
            # Create a temporary file with the modified content
            tmp_file="$(mktemp)"
            awk '/G28 ; Home all axes/{print; getline; if (!/G29 ;/) print "G29 ;"; print; next} 1' "$file" > "$tmp_file"
            
            # Replace the original file with the modified content
            mv "$tmp_file" "$file"
            
            echo "Added G29 line to $file"
        fi
    done < <(find "$directory" -type f -name "*.gcode" -print0)
done