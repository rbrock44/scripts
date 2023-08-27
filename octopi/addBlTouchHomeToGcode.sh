#!/bin/bash

# List of directories containing .gcode files
directories=(
    "O:\PLA"
    "Z:\3D Prints\PLA\Ender 3 v2"
    # Add more directories as needed
)

# Loop through each directory
for directory in "${directories[@]}"; do
    # Loop through all .gcode files in the directory
    for file in "$directory"/*.gcode; do
        # Check if the file contains the target line and the following line
        if grep -q "G28 ; Home all axes" "$file" && ! grep -q "G29 ;" "$file"; then
            # Add the missing line
            sed -i '/G28 ; Home all axes/{n; /G29 ;/! i\G29 ;}' "$file"
            echo "Added G29 line to $file"
        fi
    done
done