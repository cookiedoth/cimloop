#!/usr/bin/env python3
"""
Script to create a properly formatted YAML mapping file for Timeloop

The mapping files saved from Timeloop's output are in a textual format meant for
human reading, not for being parsed back by Timeloop. This script demonstrates
how to create a proper YAML mapping file that Timeloop can use.
"""

import os
import yaml

# Example mapping in the format Timeloop expects
example_mapping = {
    "mapping": [
        {
            "target": "DRAM",
            "type": "temporal",
            "factors": "P=256",
            "permutation": "P"
        },
        {
            "target": "shared_glb",
            "type": "temporal",
            "factors": "M=128 C=4 P=8",
            "permutation": "MCP"
        },
        {
            "target": "inter_PE_column_spatial",
            "type": "spatial",
            "factors": "M=4",
            "permutation": "M",
            "split": 1
        },
        {
            "target": "inter_PE_spatial",
            "type": "spatial",
            "factors": "M=2 C=2",
            "permutation": "MC",
            "split": 0
        },
        {
            "target": "ifmap_spad",
            "type": "temporal",
            "factors": "C=2",
            "permutation": "C"
        },
        {
            "target": "psum_spad",
            "type": "temporal",
            "factors": "M=2",
            "permutation": "M"
        },
        {
            "target": "inter_1bit_x_1bit_mac_spatial",
            "type": "spatial",
            "factors": "Z=8 Y=4 X=8",
            "permutation": "ZYX",
            "split": 3
        },
        {
            "target": "here_to_fix_a_bug",
            "type": "temporal",
            "factors": "",
            "permutation": ""
        }
    ]
}

# Save the mapping to a YAML file
with open("proper_mapping.yaml", "w") as f:
    yaml.dump(example_mapping, f, default_flow_style=False)

print(f"Created proper mapping file: proper_mapping.yaml")

# Just to verify, load the file back and print it
with open("proper_mapping.yaml", "r") as f:
    loaded_mapping = yaml.safe_load(f)

print("\nVerified loaded mapping structure:")
print(yaml.dump(loaded_mapping, default_flow_style=False))

print("\nNow you can use this mapping file with run_layer_with_mapping:")
print("""
import utils as utl

eval_result = utl.run_layer_with_mapping(
    macro="nestquant",
    layer="workloads/llm/gemm.yaml",
    mapping_file="proper_mapping.yaml"
)
""") 