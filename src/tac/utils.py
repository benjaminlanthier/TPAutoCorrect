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


def find_dir(dirname: str, root: Optional[str] = None) -> Optional[str]:
    root = root or os.getcwd()
    for root, dirs, files in os.walk(root):
        for _dir in dirs:
            if _dir == dirname:
                return os.path.join(root, _dir)
    return None


def shutil_onerror(func, path, exc_info):
    """
    Error handler for ``shutil.rmtree``.

    If the error is due to an access error (read only file)
    it attempts to add write permission and then retries.

    If the error is for another reason it re-raises the error.

    Usage : ``shutil.rmtree(path, onerror=onerror)``
    """
    import stat
    # Is the error an access error?
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        raise


def rm_file(filepath: Optional[str] = None):
    if filepath is None:
        return
    if not os.path.exists(filepath):
        return
    if not os.path.isfile(filepath):
        raise ValueError(f"filepath must be a file, got {filepath}")
    try:
        os.remove(filepath)
    except PermissionError:
        shutil_onerror(os.remove, filepath, None)


def try_rmtree(path: str, ignore_errors: bool = True):
    try:
        shutil.rmtree(path, ignore_errors=ignore_errors, onerror=shutil_onerror)
    except FileNotFoundError:
        pass


def rm_pycache(root: Optional[str] = None):
    root = root or os.getcwd()
    for root, dirs, files in os.walk(root):
        for dir in dirs:
            if dir == "__pycache__":
                try_rmtree(os.path.join(root, dir))


def rm_pyc_files(root: Optional[str] = None):
    root = root or os.getcwd()
    for root, dirs, files in os.walk(root):
        for file in files:
            if file.endswith(".pyc"):
                try_rmtree(os.path.join(root, file))
