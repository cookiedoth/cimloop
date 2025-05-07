import sys
import os
import shutil

# fmt: off
THIS_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MACRO_NAME = os.path.basename(THIS_SCRIPT_DIR)
sys.path.append(os.path.abspath(os.path.join(THIS_SCRIPT_DIR, '..', '..', '..', '..')))
from scripts import utils as utl
import scripts
# fmt: on

def test_area_energy_breakdown(arch, layer, use_dnn=False):
    """
    Test area and energy breakdown for different nestquant architectures.
    
    Parameters:
    - arch: Architecture configuration (w0, w3, w3s, w4)
    - layer: Layer configuration file path
    - use_dnn: If True, uses utl.quick_run for DNN workload instead of utl.run_layer
    """
    layer_path = utl.path_from_model_dir(layer)
    arch_target = os.path.join(THIS_SCRIPT_DIR, "arch.yaml")
    arch_src = os.path.join(THIS_SCRIPT_DIR, f"arch_{arch}.yaml")
    assert os.path.exists(arch_src)
    shutil.copy(arch_src, arch_target)
    print("Running on layer", layer_path)
    print("Architecture is taken from", arch_src)
    # print("Quant_w is", quant_w)

    if use_dnn:
        result = utl.quick_run(
            macro=MACRO_NAME,
            dnn=os.path.basename(layer_path),  # Use dnn parameter instead of workload
        )
    else:
        result = utl.run_layer(
            macro=MACRO_NAME,
            system="_none",
            layer=layer_path,
        )

    result.clear_zero_areas()
    result.clear_zero_energies()
    return result

if __name__ == "__main__":
    test_area_energy_breakdown()
