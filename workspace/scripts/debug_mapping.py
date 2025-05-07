import importlib
import utils
importlib.reload(utils)
import utils as utl

# Run the layer
result = utl.run_layer(macro="nestquant", layer="workloads/llm/gemm.yaml")

# Debug information about the output_stats object
print("Type of result:", type(result))
print("Dir of result:", dir(result))
print("Has mapping attribute:", hasattr(result, 'mapping'))

# Check if we have raw_data
if hasattr(result, 'raw_data'):
    print("Has raw_data attribute")
    print("Keys in raw_data:", result.raw_data.keys() if hasattr(result.raw_data, 'keys') else "raw_data is not a dict")
    print("raw_data contains mapping:", 'mapping' in result.raw_data if hasattr(result.raw_data, 'keys') else False)

# Let's debug the run_mapper function to see where mapping comes from
run_dir = utl.get_run_dir()
print("\nChecking output files in:", run_dir)

import os
if os.path.exists(run_dir):
    print("Files in run_dir:", os.listdir(run_dir))
    map_files = [f for f in os.listdir(run_dir) if f.endswith('.map.txt')]
    if map_files:
        map_file_path = os.path.join(run_dir, map_files[0])
        print(f"\nFound map file: {map_file_path}")
        print("Map file content sample (first 10 lines):")
        with open(map_file_path, 'r') as f:
            content = f.readlines()
            for line in content[:10]:
                print(line.strip())
    else:
        print("No map files found")
else:
    print("Run directory does not exist") 