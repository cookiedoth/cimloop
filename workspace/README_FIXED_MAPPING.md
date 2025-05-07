# Using Fixed Mappings with Timeloop

This document explains how to use a specific fixed mapping with Timeloop instead of having the mapper find the optimal mapping each time.

## Overview

The normal Timeloop workflow uses the `mapper` to search the space of possible mappings and find an optimal one. However, there are situations where you might want to use a specific mapping:

1. To compare different architectures with the same mapping
2. To analyze the effects of specific mapping decisions
3. To speed up experiments when you already know a good mapping
4. When you've found a mapping you like and want to reuse it

## Workflow

The workflow has three main steps:

1. **Run the mapper** to find an optimal mapping
2. **Save the mapping** to a YAML file
3. **Reuse the mapping** by running the evaluator with the saved mapping file

## New Utility Functions

We've added several utility functions to make this workflow easy:

1. `run_with_mapping(spec, mapping_file)`: Run Timeloop evaluator with a specific mapping
2. `run_layer_with_mapping(macro, layer, mapping_file, ...)`: Run a layer with a specific mapping
3. `save_best_mapping(output_stats, output_file)`: Save the best mapping from a run to a file

## Example Usage

See `examples/use_fixed_mapping.py` for a complete example of the workflow.

```python
# 1. Run mapper to find optimal mapping
result = utl.run_layer(macro="nestquant", layer="dnn/resnet50/layers/conv1")

# 2. Save the mapping
mapping_file = "saved_mapping.yaml"
utl.save_best_mapping(result, mapping_file)

# 3. Reuse the mapping for other experiments
eval_result = utl.run_layer_with_mapping(
    macro="nestquant",
    layer="dnn/resnet50/layers/conv1",
    mapping_file=mapping_file
)
```

## Mapping File Format

The mapping file is a YAML file with a list of mapping directives under the `mapping:` key. See `examples/example_mapping.yaml` for an example of the format.

Each directive specifies:
- `target`: The hardware level being targeted
- `type`: The type of directive (`temporal`, `spatial`, or `bypass`)
- `factors`: The loop bounds for each dimension
- `permutation`: The loop ordering (inner to outer)
- `split`: (For spatial mappings) How to split loops across hardware dimensions
- `bypass`/`keep`: Which tensors to bypass or keep at each level

For more details on the mapping format, see the [Timeloop documentation](https://timeloop.csail.mit.edu/previous_versions/timeloop-accelergy-v3/timeloop/input-formats/mapping). 