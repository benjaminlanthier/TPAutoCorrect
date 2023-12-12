import os
import sys
import shutil
from typing import Optional, Union, List


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


def try_rm_trees(paths: Union[str, List[str]], ignore_errors: bool = True):
    if isinstance(paths, str):
        paths = [paths]
    for path in paths:
        try_rmtree(path, ignore_errors=ignore_errors)


def rm_direnames_from_root(dirnames: Union[str, List[str]], root: Optional[str] = None):
    if isinstance(dirnames, str):
        dirnames = [dirnames]
    root = root or os.getcwd()
    for root, dirs, files in os.walk(root):
        for dir in dirs:
            if dir in dirnames:
                try_rmtree(os.path.join(root, dir))
    return True


def rm_filetypes_from_root(filetypes: Union[str, List[str]], root: Optional[str] = None):
    if isinstance(filetypes, str):
        filetypes = [filetypes]
    root = root or os.getcwd()
    for root, dirs, files in os.walk(root):
        for file in files:
            if any([file.endswith(filetype) for filetype in filetypes]):
                try_rmtree(os.path.join(root, file))
    return True


def rm_pycache(root: Optional[str] = None):
    return rm_direnames_from_root("__pycache__", root=root)


def rm_pyc_files(root: Optional[str] = None):
    return rm_filetypes_from_root(".pyc", root=root)


def rm_pyo_files(root: Optional[str] = None):
    return rm_filetypes_from_root(".pyo", root=root)


def rm_pytest_cache(root: Optional[str] = None):
    return rm_direnames_from_root(".pytest_cache", root=root)


def reindent_json_file(filepath: str, indent: int = 4, dont_exist_ok: bool = True):
    import json

    if not os.path.exists(filepath):
        if dont_exist_ok:
            return None
        raise FileNotFoundError(f"File {filepath} does not exist")
    if not os.path.isfile(filepath):
        raise ValueError(f"File {filepath} must be a file.")

    with open(filepath, "r") as f:
        data = json.load(f)
    with open(filepath, "w") as f:
        json.dump(data, f, indent=indent)
    return filepath


def is_file_in_dir(filename: str, dirpath: str) -> bool:
    for root, dirs, files in os.walk(dirpath):
        for file in files:
            if file == filename:
                return True
    return False


def is_subpath_in_path(subpath: str, path: str) -> bool:
    subpath = os.path.abspath(subpath)
    path = os.path.abspath(path)
    return subpath in path


def import_obj_from_file(obj_name: str, filepath: str):
    from importlib import util as importlib_util

    spec = importlib_util.spec_from_file_location("module.name", filepath)
    foo = importlib_util.module_from_spec(spec)
    len_root = len(filepath.split(os.path.sep))
    import_root = os.path.dirname(filepath)
    for _ in range(len_root):
        try:
            spec.loader.exec_module(foo)
        except (ImportError, ModuleNotFoundError):
            sys.path.append(os.path.dirname(import_root))
        else:
            break
        import_root = os.path.dirname(import_root)
    obj = getattr(foo, obj_name)

    # filepath = os.path.normpath(filepath)
    # relative_path = os.path.relpath(filepath, os.getcwd())
    # module_name_ext = relative_path.replace(os.path.sep, ".")
    # module_name = module_name_ext.rsplit(".", 1)[0]
    # obj = getattr(importlib.import_module(module_name), obj_name)
    return obj


