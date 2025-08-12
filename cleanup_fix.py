#!/usr/bin/env python3
# Quick fix to clean up the main_other.py file

with open('/Users/patrick/Desktop/Reddit/main_other.py', 'r') as f:
    lines = f.readlines()

# Find the start and end of the mess
start_line = None
end_line = None

for i, line in enumerate(lines):
    if "'rarepuppers', 'cats', 'dogs'," in line:
        start_line = i
    elif "# Mische alle Subreddits zufällig" in line:
        end_line = i
        break

if start_line and end_line:
    # Remove the problematic lines
    new_lines = lines[:start_line] + lines[end_line:]
    
    # Write back
    with open('/Users/patrick/Desktop/Reddit/main_other.py', 'w') as f:
        f.writelines(new_lines)
    
    print(f"Removed lines {start_line} to {end_line}")
else:
    print("Could not find the problematic section")