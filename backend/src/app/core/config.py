import os
from pathlib import Path

class Settings:
    INPUT_ROOT: Path = Path(os.getenv("INPUT_ROOT", "/media/input"))
    OUTPUT_ROOT: Path = Path(os.getenv("OUTPUT_ROOT", "/media/output"))
    
    # Ensure roots are absolute
    def __init__(self):
        self.INPUT_ROOT = self.INPUT_ROOT.resolve()
        self.OUTPUT_ROOT = self.OUTPUT_ROOT.resolve()

settings = Settings()
