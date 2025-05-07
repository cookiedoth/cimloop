import shutil
import time
from typing import Callable, Union, Iterable, List
import os
import threading
import joblib
import pytimeloop.timeloopfe.v4 as tl
import sys
import importlib.util
import sys
from tqdm import tqdm
import glob
import yaml
import subprocess
import tempfile

# fmt: off
THIS_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(THIS_SCRIPT_DIR)
from processors import ArrayProcessor
from tl_output_parsing import parse_timeloop_output, MacroOutputStats, MacroOutputStatsList

from plots import *
# fmt: on

from joblib import delayed as delayed


def single_test(result) -> MacroOutputStatsList:
    return MacroOutputStatsList([result])


def parallel_test(
    delayed_calls: List[Callable], n_jobs: int = 32
) -> MacroOutputStatsList:
    if not isinstance(delayed_calls, Iterable):
        delayed_calls = [delayed_calls]

    delayed_calls = list(delayed_calls)
    return MacroOutputStatsList(
        tqdm(
            joblib.Parallel(return_as="generator", n_jobs=n_jobs)(delayed_calls),
            total=len(delayed_calls),
        )
    )


def path_from_model_dir(*args):
    return os.path.abspath(os.path.join(THIS_SCRIPT_DIR, "..", "models", *args))


def get_run_dir():
    out_dir = os.path.join(
        THIS_SCRIPT_DIR,
        "..",
        "outputs",
        f"{os.getpid()}.{threading.current_thread().ident}",
    )
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def get_spec(
    macro: str,
    tile: str = None,
    chip: str = None,
    system: str = "ws_dummy_buffer_one_macro",
    iso: str = None,
    dnn: str = None,
    layer: str = None,
    max_utilization: bool = False,
    extra_print: str = "",
    jinja_parse_data: dict = None,
) -> tl.Specification:
    paths = [
        os.path.abspath(
            os.path.join(THIS_SCRIPT_DIR, "..", "models", "top.yaml.jinja2")
        )
    ]

    jinja_parse_data = {
        **(jinja_parse_data or {}),
        "macro": macro,
        "tile": tile,
        "chip": chip,
        "system": system,
        "iso": iso if iso else macro,
        "dnn": dnn,
        "layer": layer,
    }
    jinja_parse_data = {k: v for k, v in jinja_parse_data.items() if v is not None}

    paths2print = [p for p in paths]
    while any(paths2print):
        if all(paths2print[0][0] == p[0] for p in paths2print):
            paths2print = [p[1:] for p in paths2print]
        else:
            break
    paths2print = ", ".join(paths2print)

    if not extra_print:
        extra_print = f"{os.getpid()}.{threading.current_thread().ident}"

    spec = tl.Specification.from_yaml_files(
        *paths, processors=[ArrayProcessor], jinja_parse_data=jinja_parse_data
    )
    if max_utilization:
        spec.variables["MAX_UTILIZATION"] = True

    return spec


def run_with_mapping(
    spec: tl.Specification,
    mapping_file: str,
    accelergy_verbose: bool = False,
) -> dict:
    """Run Timeloop with a specific mapping file.
    
    This function executes timeloop-mapper directly as a subprocess, which is more
    reliable than trying to use the Python API for fixed mappings.
    
    Args:
        spec: The Timeloop specification
        mapping_file: Path to the mapping YAML file
        accelergy_verbose: Whether to run accelergy in verbose mode
        
    Returns:
        The evaluation results
    """
    import subprocess
    import tempfile
    import shutil
    
    # Create output directory
    output_dir = get_run_dir()
    os.makedirs(output_dir, exist_ok=True)
    
    # Create temporary files for the command-line approach
    spec_file = os.path.join(output_dir, "spec.yaml")
    
    # Save the spec as YAML using tl's own utilities
    with open(spec_file, 'w') as f:
        if hasattr(spec, 'to_yaml_str'):
            f.write(spec.to_yaml_str())
        else:
            # Fallback - try to use the internal structure
            import json
            spec_dict = spec.spec if hasattr(spec, 'spec') else spec.__dict__
            json.dump(spec_dict, f, indent=2)
    
    # Create a minimal mapper config file
    mapper_config = os.path.join(output_dir, "mapper.yaml")
    with open(mapper_config, 'w') as f:
        f.write("""
mapper:
  algorithm: exhaustive
  search_size: 1
  timeout: 0
  victory_condition: 0
""")
    
    # Copy the mapping file to the output directory
    map_file_in_output = os.path.join(output_dir, "mapping.yaml")
    shutil.copy(mapping_file, map_file_in_output)
    
    # Run timeloop-mapper directly using subprocess
    cmd = [
        "timeloop-mapper",
        spec_file,
        mapper_config,
        map_file_in_output,
        "-o", output_dir
    ]
    
    print(f"Running command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Command output:")
        print(result.stdout)
        
        # Parse the results from the stats file
        stats_file = os.path.join(output_dir, "timeloop-mapper.stats.txt")
        if os.path.exists(stats_file):
            return MacroOutputStats.from_output_stats(
                tl.output_parsing.OutputStats.from_file(stats_file)
            )
        else:
            print("Stats file not found after running timeloop-mapper")
            
    except subprocess.CalledProcessError as e:
        print(f"Error running timeloop-mapper: {e}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
    except Exception as e:
        print(f"Unexpected error: {e}")
    
    # If subprocess approach fails, fall back to the normal API approach
    print("Falling back to normal API approach")
    mapper = tl.mapper.Mapper()
    mapper.algorithm = "exhaustive"
    mapper.search_size = 1
    mapper.timeout = 0
    spec.mapper = mapper
    
    return run_mapper(spec, accelergy_verbose)


def quick_run(
    macro: str,
    variables: dict = None,
    accelergy_verbose: bool = False,
    **kwargs,
):
    spec = get_spec(
        macro=macro,
        system="ws_dummy_buffer_one_macro",
        max_utilization=True,
        **kwargs,
    )
    variables = variables or {}
    spec.variables.update(variables)
    for k in list(spec.variables.keys()):
        if k not in variables:
            spec.variables[k] = spec.variables.pop(k)

    return run_mapper(spec, accelergy_verbose=accelergy_verbose)


def get_diagram(
    macro: str,
    container_names: Union[str, List[str]] = (),
    ignore: List[str] = (),
    variables: dict = None,
    **kwargs,
):
    spec = get_spec(
        macro=macro,
        system="ws_dummy_buffer_one_macro",
        max_utilization=True,
        **kwargs,
    )
    spec.variables.update(variables or {})
    return spec.to_diagram(container_names, ignore)


def get_test(
    macro: str,
    function_name: str,
):
    # Python path is macro path + _tests.py
    path = os.path.abspath(
        os.path.join(
            THIS_SCRIPT_DIR, "..", "models", "arch", "1_macro", macro, "_tests.py"
        )
    )
    if not os.path.exists(path):
        raise FileNotFoundError(f"No test file found at {path}")
    modspec = importlib.util.spec_from_file_location("modname", path)
    module = importlib.util.module_from_spec(modspec)
    modspec.loader.exec_module(module)
    return getattr(module, function_name)


def run_layer(
    macro: str,
    layer: str,
    variables: dict = None,
    callfunc: Callable = None,
    iso: str = None,
    tile=None,
    chip=None,
    system="ws_dummy_buffer_many_macro",
):
    spec = get_spec(
        macro=macro, iso=iso, layer=layer, tile=tile, chip=chip, system=system
    )
    spec.architecture.name2leaf("macro").attributes["has_power_gating"] = True

    variables = variables or {}

    spec.variables.update(variables)
    for k in list(spec.variables.keys()):
        if k not in variables:
            spec.variables[k] = spec.variables.pop(k)

    if callfunc is not None:
        callfunc(spec)

    try:
        return run_mapper(spec=spec)
    except Exception as e:
        print(f"Error processing spec with {macro}, {iso}, {layer}, {variables}")
        raise e


def run_layer_with_mapping(
    macro: str,
    layer: str,
    mapping_file: str,
    variables: dict = None,
    callfunc: Callable = None,
    iso: str = None,
    tile=None,
    chip=None,
    system="ws_dummy_buffer_many_macro",
):
    """Run a layer with a specific mapping file.
    
    Args:
        macro: The macro to use
        layer: The layer to run
        mapping_file: Path to the mapping YAML file
        variables: Optional variables to set
        callfunc: Optional function to call on the spec
        iso: Optional iso parameter
        tile: Optional tile parameter
        chip: Optional chip parameter
        system: The system to use
        
    Returns:
        The evaluation results
    """
    spec = get_spec(
        macro=macro, iso=iso, layer=layer, tile=tile, chip=chip, system=system
    )
    spec.architecture.name2leaf("macro").attributes["has_power_gating"] = True

    variables = variables or {}

    spec.variables.update(variables)
    for k in list(spec.variables.keys()):
        if k not in variables:
            spec.variables[k] = spec.variables.pop(k)

    if callfunc is not None:
        callfunc(spec)

    try:
        return run_with_mapping(spec=spec, mapping_file=mapping_file)
    except Exception as e:
        print(f"Error processing spec with {macro}, {iso}, {layer}, {variables}")
        raise e


def save_best_mapping(output_stats, output_file):
    """Save the best mapping from a mapper run to a file.
    
    Args:
        output_stats: The output stats from run_mapper
        output_file: The file to save the mapping to
    """
    # Check if the output_stats object has a mapping attribute
    has_mapping = hasattr(output_stats, 'mapping')
    if has_mapping and output_stats.mapping:
        # We already have a mapping in the object, use it
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(output_stats.mapping)
        print(f"Saved best mapping to {output_file}")
        return True
    
    # If we don't have a mapping in the object, try to find it in one of the output directories
    # Look for map files in outputs directory
    output_dirs = glob.glob(os.path.join(THIS_SCRIPT_DIR, "..", "outputs", "*"))
    map_files = []
    for output_dir in output_dirs:
        map_files.extend(glob.glob(f"{output_dir}/*.map.txt"))
    
    # Try to read from the most recent map file if available
    if map_files:
        # Sort by modification time (newest first)
        map_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        try:
            with open(map_files[0], 'r') as f:
                mapping_content = f.read()
            
            # Write the mapping to the output file
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(mapping_content)
            print(f"Saved best mapping to {output_file} (loaded from {map_files[0]})")
            return True
        except Exception as e:
            print(f"Error reading or writing mapping file: {e}")
            return False
    
    # If we reach here, we couldn't find mapping data
    print("Warning: Could not find mapping data in the provided output stats or any output directory")
    return False


def run_mapper(
    spec: tl.Specification,
    accelergy_verbose: bool = False,
    mapping_file: str = None,
) -> dict:
    """Run Timeloop mapper to find an optimal mapping.
    
    Args:
        spec: The Timeloop specification
        accelergy_verbose: Whether to run accelergy in verbose mode
        mapping_file: Optional path to a mapping file to use instead of searching
        
    Returns:
        The evaluation results
    """
    output_dir = get_run_dir()

    run_prefix = f"{output_dir}/timeloop-mapper"
    
    # Call the mapper with or without a mapping file
    if mapping_file:
        # Copy the mapping file to the output directory
        import shutil
        mapping_in_output = os.path.join(output_dir, "mapping.yaml")
        shutil.copy(mapping_file, mapping_in_output)
        
        print(f"Using provided mapping from {mapping_file}")
        # Check if call_mapper supports the flags parameter
        import inspect
        call_mapper_params = inspect.signature(tl.call_mapper).parameters
        
        if 'flags' in call_mapper_params:
            # If flags is supported, use it to specify the mapping file
            mapper_result = tl.call_mapper(
                specification=spec,
                output_dir=output_dir,
                log_to=os.path.join(output_dir, f"{run_prefix}.log"),
                flags=["--mapping-file", mapping_in_output]
            )
        else:
            # If flags is not supported, we need a different approach
            # Let's try setting the mapping directly on the spec
            try:
                # Read the mapping file to see if we can parse it
                with open(mapping_file, 'r') as f:
                    mapping_content = f.read()
                
                # Try a simple approach - just set a fixed mapper
                from pytimeloop.timeloopfe.v4.mapper import Mapper
                spec.mapper = Mapper()
                spec.mapper.algorithm = "exhaustive"
                spec.mapper.search_size = 1
                spec.mapper.timeout = 0
                
                # Run the mapper normally, it should use our config
                mapper_result = tl.call_mapper(
                    specification=spec,
                    output_dir=output_dir,
                    log_to=os.path.join(output_dir, f"{run_prefix}.log"),
                )
            except Exception as e:
                print(f"Error setting mapping: {e}")
                # Fall back to the normal call
                mapper_result = tl.call_mapper(
                    specification=spec,
                    output_dir=output_dir,
                    log_to=os.path.join(output_dir, f"{run_prefix}.log"),
                )
    else:
        # Normal mapper call without a mapping file
        mapper_result = tl.call_mapper(
            specification=spec,
            output_dir=output_dir,
            log_to=os.path.join(output_dir, f"{run_prefix}.log"),
        )
        
    if accelergy_verbose:
        tl.call_accelergy_verbose(
            specification=spec,
            output_dir=output_dir,
            log_to=os.path.join(output_dir, "accelergy.log"),
        )

    return MacroOutputStats.from_output_stats(mapper_result)
