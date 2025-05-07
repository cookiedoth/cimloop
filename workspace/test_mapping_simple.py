#!/usr/bin/env python3
"""
Simplified test script for fixed mapping functionality
"""
import os
import sys
import traceback
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir, ".."))

try:
    # Import only what we need
    import pytimeloop.timeloopfe.v4 as tl
    from pytimeloop.timeloopfe.v4.mapper import Mapper
    
    def get_run_dir():
        """Create a run directory for Timeloop output"""
        import tempfile
        output_dir = tempfile.mkdtemp(prefix="timeloop_")
        return output_dir
    
    def run_test():
        """Test the fixed mapping approach"""
        logger.info("Starting test...")
        
        # Create a simple mapping YAML
        mapping_content = """
mapping:
  - target: DRAM
    type: temporal
    factors: C=1 K=16 R=1 S=1 P=7 Q=7 N=1
    permutation: KQPNRSC
  - target: GlobalBuffer
    type: temporal
    factors: C=32 K=2 R=3 S=3 P=1 Q=1 N=1
    permutation: SRCKQPN
  - target: RegisterFile
    type: temporal
    factors: C=1 K=1 R=1 S=1 P=8 Q=8 N=1
    permutation: QPNSKRC
        """
        
        # Save this mapping to a file
        mapping_file = os.path.join(script_dir, "test_mapping.yaml")
        with open(mapping_file, "w") as f:
            f.write(mapping_content)
        logger.info(f"Created test mapping file at {mapping_file}")
        
        # Create a simple specification
        logger.info("Creating test specification...")
        spec = tl.Specification()
        
        # Create a mapper that just evaluates
        mapper = Mapper()
        mapper.algorithm = "exhaustive"
        mapper.search_size = 1
        mapper.timeout = 0
        mapper.victory_condition = 0
        spec.mapper = mapper
        
        # Add the mapping
        import yaml
        mapping_data = yaml.safe_load(mapping_content)
        if isinstance(mapping_data, dict) and 'mapping' in mapping_data:
            spec.mapping = mapping_data['mapping']
        else:
            spec.mapping = mapping_data
        
        logger.info("Spec created with fixed mapping")
        logger.info(f"Mapper config: {spec.mapper}")
        logger.info(f"Mapping type: {type(spec.mapping)}")
        
        # Output directory
        output_dir = get_run_dir()
        logger.info(f"Created output directory: {output_dir}")
        
        # Try to run the mapper
        try:
            logger.info("Running mapper with fixed mapping...")
            run_prefix = f"{output_dir}/timeloop-mapper"
            mapper_result = tl.call_mapper(
                specification=spec,
                output_dir=output_dir,
                log_to=os.path.join(output_dir, f"{run_prefix}.log")
            )
            logger.info("Mapper completed successfully")
            logger.info(f"Result: {mapper_result}")
        except Exception as e:
            logger.error(f"Error running mapper: {e}")
            logger.error(traceback.format_exc())
        
        logger.info("Test complete")
    
    if __name__ == "__main__":
        run_test()

except Exception as e:
    logger.error(f"Import error: {e}")
    logger.error(traceback.format_exc()) 