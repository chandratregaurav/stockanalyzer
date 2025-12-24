
import os

file_path = 'dashboard.py'

with open(file_path, 'r') as f:
    lines = f.readlines()

# Identify the block
start_line_idx = -1
end_line_idx = -1

for i, line in enumerate(lines):
    if line.strip() == "import time" and lines[i+1].strip() == "import base64":
        start_line_idx = i
    if line.strip().startswith("st.markdown(f'<audio autoplay=\"true\""):
        end_line_idx = i

if start_line_idx != -1 and end_line_idx != -1:
    print(f"Found block at lines {start_line_idx+1} to {end_line_idx+1}")
    
    # Extract block
    block_lines = lines[start_line_idx : end_line_idx+1]
    
    # Remove block from original location (and potential surrounding empty lines)
    # We create a new list excluding these lines
    remaining_lines = lines[:start_line_idx] + lines[end_line_idx+1:]
    
    # Find insertion point (after 'from stock_screener import StockScreener')
    insert_idx = -1
    for i, line in enumerate(remaining_lines):
        if "from stock_screener import StockScreener" in line:
            insert_idx = i + 1
            break
            
    if insert_idx != -1:
        # Insert block
        new_lines = remaining_lines[:insert_idx] + ['\n'] + block_lines + ['\n'] + remaining_lines[insert_idx:]
        
        with open(file_path, 'w') as f:
            f.writelines(new_lines)
        print("Successfully moved code block to top.")
    else:
        print("Could not find insertion point.")
else:
    print("Could not find the misplaced code block.")
