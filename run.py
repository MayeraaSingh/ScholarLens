"""
ScholarLens Entry Point
Runs the main CLI from the project root directory.
"""
import sys
import os
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parent.absolute()

# Add project root to Python path so 'src' is importable as a package
sys.path.insert(0, str(project_root))

# Change to project root directory
os.chdir(project_root)

# Import and run main from the src package
from src.main import main

if __name__ == "__main__":
    main()
