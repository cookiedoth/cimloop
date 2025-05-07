#!/usr/bin/env python
"""
Example showing how to:
1. Run Timeloop mapper to find an optimal mapping
2. Save that mapping to a file
3. Reuse the saved mapping for future experiments
"""

import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts import utils as utl

# Parameters
MACRO = "nestquant"
ARCH = "baseline"
LAYER = "dnn/resnet50/layers/conv1"

# Step 1: Run mapper to find optimal mapping
print("Step 1: Running mapper to find optimal mapping...")
result = utl.run_layer(
    macro=MACRO,
    system="_none",
    layer=LAYER
)

# Print summary of the optimal mapping found
print(f"Optimal mapping found with:")
print(f"  Energy: {result.energy} pJ")
print(f"  Cycles: {result.cycles}")
print(f"  EDP: {result.energy * result.cycles}")

# Step 2: Save the mapping
print("\nStep 2: Saving the optimal mapping to a file...")
mapping_file = "saved_mapping.yaml"
utl.save_best_mapping(result, mapping_file)

# Step 3: Run evaluator with the saved mapping
print("\nStep 3: Running evaluator with the saved mapping...")
eval_result = utl.run_layer_with_mapping(
    macro=MACRO,
    system="_none",
    layer=LAYER,
    mapping_file=mapping_file
)

# Verify the results match
print("\nVerifying results:")
print(f"Original mapper result:")
print(f"  Energy: {result.energy} pJ")
print(f"  Cycles: {result.cycles}")

print(f"Evaluator result with saved mapping:")
print(f"  Energy: {eval_result.energy} pJ")
print(f"  Cycles: {eval_result.cycles}")

print("\nNow you can use this mapping file for other experiments!") 