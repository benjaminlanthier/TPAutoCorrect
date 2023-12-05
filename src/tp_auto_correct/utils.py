import os
import shutil
from typing import Optional


def find_filepath(filename: str, root: Optional[str] = None) -> Optional[str]:
    root = root or os.getcwd()
    for root, dirs, files in os.walk(root):
        for file in files:
            if file == filename:
                return os.path.join(root, file)
    return None


def rm_pycache(root: Optional[str] = None):
    root = root or os.getcwd()
    for root, dirs, files in os.walk(root):
        for dir in dirs:
            if dir == "__pycache__":
                shutil.rmtree(os.path.join(root, dir))
                

def rm_pyc_files(root: Optional[str] = None):
    root = root or os.getcwd()
    for root, dirs, files in os.walk(root):
        for file in files:
            if file.endswith(".pyc"):
                shutil.rmtree(os.path.join(root, file))
