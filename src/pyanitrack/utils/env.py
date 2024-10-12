
import logging
from os import path as os_path

from .. import utils
from ..utils.config import Config
from ..utils.logger import LoggerHandler

_logger = logging.getLogger(__name__)

UTILS_DIR = os_path.dirname(os_path.abspath(__file__))
SRC_DIR = os_path.dirname(UTILS_DIR)  # Get source directory


class Env:

    PROJECT_DIR = SRC_DIR

    def __init__(self, config_path: str, *args, **kwargs):
        # Referenced objects
        self.config = None
        self.logger = None

        # Project details
        self.project_dir: str = ""
        self.project_name: str = ""
        self.project_name_text: str = ""
        self.instance: str = ""
        self.version: str = ""

        # Database
        self.conn = None
        self.cur = None

        logs_dir = kwargs.get("logs_dir")
        if logs_dir:
            kwargs.pop("logs_dir")

        self.__call__(*args, **kwargs)

        if self.project_dir:  # Ensure given project dir exists
            utils.path.checkPath(self.project_dir, errors='raise')

        kwargs = {'env': self, **kwargs}
        self.config = Config(config_path, **kwargs)

        # Create logger
        if not self.config.get("logs", {}).get("no_logs", False):
            self.logger = LoggerHandler(logs_dir or "", project_name=self.project_name, instance=self.instance,
                                        **self.config.get("logs"))

    def __call__(self, *args, **kwargs):
        """Update the Env with given attributes."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                _logger.warning(f"Unexpected key, got: {key}")

        if "project_dir" in kwargs:
            # Validate given project dir, fallback to root dir
            if not self.project_dir or not utils.path.existPath(self.project_dir):
                self.project_dir = self.PROJECT_DIR

    def __str__(self) -> str:
        return f"Env(project='{self.project_name_text}', version='{self.version}')"

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other):
        return self is other

    def __ne__(self, other):
        return self is not other

    def __hash__(self):
        return object.__hash__(self)
