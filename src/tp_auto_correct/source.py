import logging
import shutil
import subprocess
import sys
import os
from typing import Optional

import git
from github import Github
from github import Auth

from src.tp_auto_correct import utils


class Source:
    # Git
    DEFAULT_REPO_NAME = "<repo_name>"
    DEFAULT_REPO_URL = "https://github.com/{}.git"
    DEFAULT_REPO_BRANCH = "main"

    def __init__(self, src_path, *args, **kwargs):
        self._src_path = src_path
        self.args = args
        self.kwargs = kwargs

        self._local_path = None
        self._remote_path = None
        self._repo_url = kwargs.get("repo_url", kwargs.get("url", None))
        
        # self.auth = Auth.Token("access_token")
        # self.github = Github(auth=self.auth)
        self.repo_branch = kwargs.get("repo_branch", self.DEFAULT_REPO_BRANCH)
        self.repo_name = kwargs.get("repo_name", self.DEFAULT_REPO_NAME)
        self.repo = None

        self.working_path = kwargs.get("working_path", None)

    @property
    def src_path(self) -> str:
        r"""
        Return the source path of the object. This is the path from where to copy the source files.
        This can be the path from a local folder or a remote repo.
        
        :return: The source path of the object.
        :rtype: str
        """
        return self._src_path

    @property
    def local_path(self) -> Optional[str]:
        r"""
        Return the local path of the object. This is the path where the source files are copied to. Will
        return None if the current object is not setup yet.
        
        :return: The local path of the object.
        :rtype: str
        """
        return self._local_path

    @property
    def remote_path(self) -> Optional[str]:
        r"""
        Return the remote path of the object or in other words the repo url if the source is remote.
        
        :return: The remote path of the object.
        """
        return self._remote_path

    @property
    def repo_url(self) -> str:
        r"""
        Return the remote path of the object or in other words the repo url if the source is remote.

        :return: The remote path of the object.
        """
        return self.remote_path

    @property
    def is_local(self) -> bool:
        return os.path.exists(self.src_path)

    @property
    def is_remote(self) -> bool:
        return not self.is_local
    
    @property
    def is_setup(self) -> bool:
        return self.local_path is not None

    def copy(self, dst_path: str = None, overwrite=False):
        dst_path = dst_path or self.working_path
        tmp_local_path = os.path.join(dst_path, os.path.basename(self.src_path))
        if tmp_local_path == self.src_path:
            return
        self._local_path = tmp_local_path
        if os.path.exists(self.local_path):
            if overwrite:
                shutil.rmtree(self.local_path)
            else:
                raise RuntimeError(f"Path {self.local_path} already exists. Set overwrite to True to overwrite.")
        if self.is_remote:
            self._clone_repo(self.local_path)  # TODO: need to extract the good folder at self.src_path after cloning
        else:
            shutil.copytree(self.src_path, self.local_path, dirs_exist_ok=True)
    
    def _clone_repo(self, dst_path: str = None):
        dst_path = dst_path or self.local_path
        self.repo_name = self.repo_url.split("/")[-1].split(".")[0]
        logging.info(f"Cloning repo {self.repo_name} from {self.repo_url} to {dst_path} ...")
        self.repo = git.Repo.clone_from(self.repo_url, dst_path, branch=self.repo_branch)
        self.repo.git.checkout(self.repo_branch)
        self.repo.git.pull()
        self.repo_name = self.repo.remotes.origin.url.split("/")[-1].split(".")[0]
        logging.info(f"Cloning repo {self.repo_name} from {self.repo_url} to {dst_path}. Done.")
        return self.repo

    def setup_at(self, dst_path: str = None, overwrite=False, **kwargs) -> str:
        dst_path = dst_path or self.working_path
        self.working_path = dst_path
        self.copy(dst_path, overwrite=overwrite)
        if kwargs.get("debug", False):
            print(self)
        return dst_path

    def send_cmd_to_process(
            self,
            cmd: str,
            timeout: Optional[int] = None,
            **kwargs
    ):
        fmt_cmd = f"{cmd}" + ('\n' if not cmd.endswith('\n') else '')
        process = subprocess.Popen(
            fmt_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            universal_newlines=True,
            encoding="utf8",
            errors='ignore',
            cwd=kwargs.get("cwd", os.path.normpath(self.working_path))
        )
        stdout, stderr = process.communicate(timeout=timeout)
        return stdout

    def __repr__(self):
        _repr = f"{self.__class__.__name__}(src={self.src_path}"
        if self.working_path is not None:
            _repr += f", working_path={self.working_path}"
        if self.is_local:
            _repr += ", is_local=True"
        else:
            _repr += ", is_remote=True"
        _repr += ")"
        return _repr


class SourceCode(Source):
    # Code
    DEFAULT_OUTPUT_FOLDER = "results"
    DEFAULT_CMDS = "pip install -r requirements.txt && python main.py"
    DEFAULT_CODE_ROOT_FOLDER = "."

    # Venv
    DEFAULT_VENV = "venv"
    VENV_SCRIPTS_FOLDER_BY_OS = {
        "win32": r"{}\Scripts",
        "linux": "{}/bin",
        "darwin": "{}/bin",
    }
    VENV_ACTIVATE_CMD_BY_OS = {
        "win32": r"{}\Scripts\activate.bat",
        "linux": "source {}/bin/activate",
        "darwin": "source {}/bin/activate",
    }
    DEFAULT_SETUP_CMDS = "pip install -r requirements.txt"
    DEFAULT_RECREATE_VENV = True

    def __init__(self, src_path, *args, **kwargs):
        super().__init__(src_path, *args, **kwargs)
        self.code_root_folder = kwargs.get("code_root_folder", self.DEFAULT_CODE_ROOT_FOLDER)
        self.venv = kwargs.get("venv", self.DEFAULT_VENV)
        self.reqs_path = kwargs.get("requirements_path", self.find_requirements_path())

    @property
    def is_venv_created(self):
        return os.path.exists(self.get_venv_path())
    
    def find_requirements_path(self) -> Optional[str]:
        local_root = os.path.join(self.src_path, "..")
        return utils.find_filepath("requirements.txt", root=local_root)

    def setup_at(self, dst_path: str = None, overwrite=True, **kwargs):
        dst_path = super().setup_at(dst_path, overwrite=overwrite)
        venv_stdout = self.maybe_create_venv()
        reqs_stdout = self.install_requirements()
        if kwargs.get("debug", False):
            print(f"venv_stdout: {venv_stdout}")
            print(f"reqs_stdout: {reqs_stdout}")
        return dst_path

    def get_venv_path(self, dst_path: str = None) -> str:
        dst_path = dst_path or self.working_path
        return os.path.join(dst_path, self.venv)

    def maybe_create_venv(self, dst_path: str = None):
        dst_path = dst_path or self.working_path
        venv_path = self.get_venv_path(dst_path)
        stdout = ""
        if os.path.exists(venv_path):
            logging.info(f"Recreating venv {self.venv} ...")
            shutil.rmtree(venv_path)
        if not os.path.exists(venv_path):
            logging.info(f"Creating venv at {venv_path} ...")
            stdout = self.send_cmd_to_process(f"python -m venv {venv_path}", cwd=dst_path)
            logging.info(f"Creating venv -> Done. stdout: {stdout}")
        return stdout

    def get_venv_scripts_folder(self, dst_path: str = None) -> str:
        dst_path = dst_path or self.working_path
        return self.VENV_SCRIPTS_FOLDER_BY_OS[sys.platform].format(self.get_venv_path(dst_path))

    def get_venv_python_path(self, dst_path: str = None) -> str:
        dst_path = dst_path or self.working_path
        return os.path.join(
            self.get_venv_scripts_folder(dst_path),
            "python"
        )

    def install_requirements(self):
        if self.reqs_path is None:
            return "No requirements.txt file found."
        return self.send_cmd_to_process(
            f"{self.get_venv_python_path()} -m pip install -r {self.reqs_path}",
            cwd=self.working_path
        )

    def send_cmd_to_process(
            self,
            cmd: str,
            timeout: Optional[int] = None,
            **kwargs
    ):
        if self.is_venv_created:
            if cmd.startswith("python"):
                cmd = cmd.replace("python", self.get_venv_python_path())
            if cmd.startswith("pip"):
                cmd = cmd.replace("pip", os.path.join(self.get_venv_scripts_folder(), "pip"))
        return super().send_cmd_to_process(cmd, timeout=timeout, **kwargs)


class SourceTests(Source):
    def __init__(self, src_path, *args, **kwargs):
        super().__init__(src_path, *args, **kwargs)

    def setup_at(self, dst_path: str = None, overwrite=True, **kwargs):
        dst_path = super().setup_at(dst_path, overwrite=overwrite)
        return dst_path
    
    def rename_test_files(self, dst_path: str = None, pattern: str = "{}_"):
        dst_path = dst_path or self.local_path
        assert os.path.exists(dst_path), f"Path {dst_path} does not exist."
        assert "{}" in pattern, f"Pattern {pattern} must contain {{}}."
        for root, dirs, files in os.walk(dst_path):
            for file in files:
                if file.startswith("test_") and file.endswith(".py"):
                    new_file = pattern.format(file).replace(".py", "") + ".py"
                    os.rename(
                        os.path.join(root, file),
                        os.path.join(root, new_file)
                    )
