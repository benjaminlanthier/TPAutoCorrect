import logging
import shutil
import sys
import os
import git


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

        self.repo_branch = kwargs.get("repo_branch", self.DEFAULT_REPO_BRANCH)
        self.repo_name = kwargs.get("repo_name", self.DEFAULT_REPO_NAME)
        self.repo = None

        self._initialize_remote_path()
        self._initialize_local_path()
        if self.local_path is None:
            raise RuntimeError(
                "Something went wrong with the initialization of the local path. If the source is remote, "
                "make sure that the remote path is correct. If the source is local, make sure that the "
                "local path exists."
            )
        self.working_path = kwargs.get("working_path", None)

    @property
    def src_path(self):
        return self._src_path

    @property
    def local_path(self):
        return self._local_path

    @property
    def remote_path(self):
        return self._remote_path

    @property
    def repo_url(self):
        return self.remote_path

    @property
    def is_local(self):
        return os.path.exists(self.src_path)

    @property
    def is_remote(self):
        return not self.is_local

    def _initialize_local_path(self):
        if self.is_local:
            self._local_path = self.src_path
        else:
            assert self._remote_path is not None, "remote_path must be initialized before local_path"
            self._local_path = self._clone_repo()

    def _initialize_remote_path(self):
        if self.is_remote:
            if self._src_path.begins_with("http"):
                self._remote_path = self.src_path
            else:
                self._remote_path = self.DEFAULT_REPO_URL.format(self.src_path)
        else:
            self._remote_path = None

    def copy(self, dst_path: str = None, overwrite=False):
        dst_path = dst_path or self.working_path
        if os.path.exists(dst_path):
            if overwrite:
                shutil.rmtree(dst_path)
            else:
                raise RuntimeError(f"Path {dst_path} already exists. Set overwrite to True to overwrite.")
        if self.is_local:
            shutil.copytree(self.local_path, dst_path)
        else:
            self._clone_repo(dst_path)
            self.repo.git.checkout(self.repo_branch)
            self.repo.git.pull()

    def _clone_repo(self, dst_path: str = None):
        dst_path = dst_path or self.working_path
        self.repo_name = self.repo_url.split("/")[-1].split(".")[0]
        logging.info(f"Cloning repo {self.repo_name} from {self.repo_url} to {dst_path} ...")
        self.repo = git.Repo.clone_from(self.repo_url, dst_path, branch=self.repo_branch)
        self.repo_name = self.repo.remotes.origin.url.split("/")[-1].split(".")[0]
        logging.info(f"Cloning repo {self.repo_name} from {self.repo_url} to {dst_path}. Done.")
        return self.repo

    def setup_at(self, dst_path: str = None, overwrite=False):
        dst_path = dst_path or self.working_path
        self.copy(dst_path, overwrite=overwrite)
        return dst_path


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

    def setup_at(self, dst_path: str = None, overwrite=False):
        dst_path = super().setup_at(dst_path, overwrite=overwrite)
        self.maybe_create_venv()

    def maybe_create_venv(self):
        if os.path.exists(self.venv_path) and self.recreate_venv and not self.venv_recreated_flag:
            logging.info(f"Recreating venv {self.venv} ...")
            shutil.rmtree(self.venv_path)
            self.venv_recreated_flag = True
        if not os.path.exists(self.venv_path):
            logging.info(f"Creating venv at {self.venv_path} ...")
            stdout = self.send_cmd_to_process(f"python -m venv {self.venv}", activate_venv=False)
            logging.info(f"Creating venv -> Done. stdout: {stdout}")
            self.exec_setup_cmds()


class SourceTests(Source):
    def __init__(self, src_path, *args, **kwargs):
        super().__init__(src_path, *args, **kwargs)

    def get_source_tests(self):
        pass





