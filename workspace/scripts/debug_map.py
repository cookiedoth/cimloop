#!/usr/bin/env python3
"""
Simplified debug script that focuses on the mapping issue
without requiring joblib
"""

import os
import sys
import glob
from pathlib import Path

# Add parent directory to path
script_dir = os.path.dirname(os.path.realpath(__file__))
workspace_dir = os.path.dirname(script_dir)
sys.path.append(workspace_dir)

# We're creating a minimal mock result object
class MockResult:
    def __init__(self):
        self.mapping = None

def save_best_mapping(output_stats, output_file):
    """Save the best mapping from a mapper run to a file."""
    print("DEBUG: Type of output_stats:", type(output_stats))
    print("DEBUG: Available attributes:", [attr for attr in dir(output_stats) if not attr.startswith('__')])
    
    # Debug mapping attribute specifically
    has_mapping = hasattr(output_stats, 'mapping')
    print("DEBUG: Has mapping attribute:", has_mapping)
    if has_mapping:
        print("DEBUG: Type of mapping:", type(output_stats.mapping))
        print("DEBUG: Is mapping None?", output_stats.mapping is None)
        if output_stats.mapping is not None:
            print("DEBUG: First 100 chars of mapping:", str(output_stats.mapping)[:100])
    
    # Look for map files in outputs directory
    output_dirs = glob.glob(os.path.join(workspace_dir, "outputs", "*"))
    map_files = []
    for output_dir in output_dirs:
        map_files.extend(glob.glob(f"{output_dir}/*.map.txt"))
    
    print("DEBUG: Map files found:", map_files)
    
    # Try to read from the most recent map file if available
    if (not has_mapping or output_stats.mapping is None) and map_files:
        # Sort by modification time (newest first)
        map_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        print("DEBUG: Reading mapping from most recent map file:", map_files[0])
        try:
            with open(map_files[0], 'r') as f:
                mapping_content = f.read()
            
            # Store the mapping in the output_stats object
            output_stats.mapping = mapping_content
            has_mapping = True
            print("DEBUG: Successfully loaded mapping from file")
            print("DEBUG: First 100 chars of loaded mapping:", mapping_content[:100])
        except Exception as e:
            print(f"DEBUG: Error reading map file: {e}")
    
    # Main logic
    if has_mapping and output_stats.mapping:
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        try:
            with open(output_file, 'w') as f:
                f.write(output_stats.mapping)
            print(f"Saved best mapping to {output_file}")
            return True
        except Exception as e:
            print(f"DEBUG: Error writing output file: {e}")
            return False
    
    # If we reach here, we couldn't find mapping data
    print("Warning: Could not find mapping data in the provided output stats")
    return False

def main():
    print("Starting debug script...")
    result = MockResult()
    output_file = os.path.join(workspace_dir, "best_mapping.yaml")
    save_best_mapping(result, output_file)
    
    # If we successfully created the mapping file, try to check its contents
    if os.path.exists(output_file):
        print("\nContents of the mapping file (first 20 lines):")
        with open(output_file, 'r') as f:
            for i, line in enumerate(f):
                if i >= 20:
                    break
                print(line.strip())

if __name__ == "__main__":
    main() 