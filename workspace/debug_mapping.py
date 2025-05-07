#!/usr/bin/env python3
"""
Debug script to understand mapping format and loading
"""
import os
import sys
import yaml

# Set up the path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(script_dir)

# Create a sample mapping file for testing
sample_mapping = """
mapping:
  - target: DRAM
    type: temporal
    factors: C=1 K=16 R=1 S=1 P=7 Q=7 N=1
    permutation: KQPNRSC
  - target: GlobalBuffer
    type: temporal
    factors: C=32 K=2 R=3 S=3 P=1 Q=1 N=1
    permutation: SRCKQPN
"""

mapping_file = os.path.join(script_dir, "sample_mapping.yaml")
with open(mapping_file, "w") as f:
    f.write(sample_mapping)
print(f"Created sample mapping file at: {mapping_file}")

# Load the sample mapping
with open(mapping_file, "r") as f:
    mapping_content = f.read()
    print("Raw mapping content:")
    print(mapping_content)

# Parse with YAML
mapping_data = yaml.safe_load(mapping_content)
print("\nParsed mapping data:")
print(mapping_data)

# Extract the mapping list
if isinstance(mapping_data, dict) and 'mapping' in mapping_data:
    mapping_list = mapping_data['mapping']
    print("\nExtracted mapping list:")
    print(mapping_list)
else:
    print("\nNo 'mapping' key found in the parsed data")

# Now load the real mapping file that's causing issues
if os.path.exists("best_mapping.yaml"):
    print("\n\nLoading the real best_mapping.yaml file:")
    with open("best_mapping.yaml", "r") as f:
        real_mapping_content = f.read()
        print("First 200 characters:")
        print(real_mapping_content[:200])
    
    try:
        real_mapping_data = yaml.safe_load(real_mapping_content)
        print("\nParsed real mapping data type:", type(real_mapping_data))
        
        if isinstance(real_mapping_data, dict):
            print("Keys:", real_mapping_data.keys())
            if 'mapping' in real_mapping_data:
                print("Real mapping list type:", type(real_mapping_data['mapping']))
                print("First item:", real_mapping_data['mapping'][0] if real_mapping_data['mapping'] else "Empty list")
        else:
            print("Real mapping data is not a dictionary, it's a:", type(real_mapping_data))
            
    except Exception as e:
        print(f"Error parsing real mapping file: {e}")
else:
    print("best_mapping.yaml file not found")

# Try using the mapping directly with the API
try:
    print("\nTrying to import and use pytimeloop...")
    import pytimeloop.timeloopfe.v4 as tl
    from pytimeloop.timeloopfe.v4.mapper import Mapper
    
    # Create a simple spec for testing
    spec = tl.Specification()
    
    # Set the mapper
    mapper = Mapper()
    mapper.algorithm = "hybrid"
    mapper.search_size = 1
    mapper.timeout = 0
    mapper.victory_condition = 0
    spec.mapper = mapper
    
    # Try to set the mapping
    if os.path.exists("best_mapping.yaml"):
        with open("best_mapping.yaml", "r") as f:
            content = f.read()
        
        data = yaml.safe_load(content)
        if isinstance(data, dict) and 'mapping' in data:
            spec.mapping = data['mapping']
            print("Successfully set mapping on spec from dict['mapping']")
        else:
            # Try setting the whole content
            spec.mapping = data
            print("Successfully set mapping on spec directly")
    
    print("Spec mapping type:", type(spec.mapping) if hasattr(spec, 'mapping') else "No mapping set")
    
except Exception as e:
    print(f"Error testing with pytimeloop: {e}")
    import traceback
    traceback.print_exc() 