import os
import sys
import re
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root and src to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT))

from src import paths
from src.data_processor import (
    MERGE_MAP,
    extract_province,
    load_population_data
)

print("Starting test of new data processor...")
