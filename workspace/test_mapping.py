#!/usr/bin/env python3
"""
Test script for fixed mapping functionality
"""
import os
import sys
import importlib
import traceback

# Add project root to path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(script_dir))

# Make sure we're using the latest version of utils
from scripts import utils
importlib.reload(utils)
from scripts import utils as utl

# Set up logging
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_test():
    """
    Run a test to see if we can save a mapping and then use it
    """
    try:
        # Step 1: Run mapper to get a mapping
        logger.info("Step 1: Running mapper to get a mapping...")
        result = utl.run_layer(
            macro="nestquant", 
            layer="workloads/llm/gemm.yaml"
        )
        
        # Save the mapping
        mapping_file = "best_mapping.yaml"
        logger.info(f"Step 2: Saving mapping to {mapping_file}...")
        success = utl.save_best_mapping(result, mapping_file)
        if not success:
            logger.error("Failed to save mapping")
            return
        
        logger.info(f"Reading saved mapping file: {mapping_file}")
        with open(mapping_file, 'r') as f:
            logger.info(f"First 100 chars of mapping: {f.read()[:100]}")
        
        # Step 3: Now use the saved mapping
        logger.info("Step 3: Using the saved mapping...")
        try:
            eval_result = utl.run_layer_with_mapping(
                macro="nestquant",
                layer="workloads/llm/gemm.yaml",
                mapping_file=mapping_file
            )
            
            # Compare the results
            logger.info("Results comparison:")
            logger.info(f"Original mapping - Energy: {result.energy}, Cycles: {result.cycles}")
            logger.info(f"Reused mapping - Energy: {eval_result.energy}, Cycles: {eval_result.cycles}")
            
        except Exception as e:
            logger.error(f"Error running with mapping: {e}")
            logger.error(traceback.format_exc())
    
    except Exception as e:
        logger.error(f"Error in test: {e}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    run_test() 