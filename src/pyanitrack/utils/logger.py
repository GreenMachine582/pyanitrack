
import logging
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from os import listdir, makedirs, path, remove as os_remove

_logger = logging.getLogger(__name__)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


def _validateLogLevel(log_level: str):
    """Validate log level."""
    if log_level.lower() not in ["debug", "info", "warning", "error", "critical"]:
        raise ValueError(f"Invalid log level: {log_level}")


def _buildLogDirectory(logs_dir: str = "", add_file_handler: bool = True):
    """Build log directory if not exists."""
    if not add_file_handler:
        return
    if not logs_dir:
        raise ValueError("No log directory specified.")
    makedirs(logs_dir, exist_ok=True)


class LoggerHandler:

    EXT: str = "log"
    LOG_LEVEL: str = "info"
    ADD_CONSOLE_HANDLER: bool = True
    ADD_FILE_HANDLER: bool = False

    # Log file name generation
    ADD_INSTANCE: bool = True
    ADD_TIME_STAMP: bool = True

    # File loggers with rotating handler
    MAX_BYTES = 10 * 1024 * 1024  # 10MB
    BACKUP_COUNT = 5
    AGE_LIMIT = 60 * 60 * 24 * 7  # 7 days

    def __init__(self, env, logs_dir: str = ""):
        self.env = env
        self.logs_dir = logs_dir
        self.timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        _buildLogDirectory(self.logs_dir, self.config["add_file_handler"])

        self.log_level = self._getConfig("log_level").upper()
        # Clean old logs if applicable
        if self.logs_dir:
            self.cleanLogs()

        # Validate log level
        _validateLogLevel(self.log_level)

        self.logger = self._buildLogger()

    @property
    def config(self):
        """Return references config from environment."""
        return self.env.config

    def _getConfig(self, key: str, section: str = "logs"):
        """Get value from provided config or use class defined config."""
        logs_config = self.env.config.get(section or "")
        if key in logs_config:  # Configured value
            return logs_config[key]
        elif hasattr(self, key.upper()):  # Return class default
            return getattr(self, key.upper())

    def _getLogFileName(self, level: str) -> str:
        """Constructs the filename of the log file."""
        names = [self._getConfig("project_name", "project")]
        if self.ADD_INSTANCE and self.env.instance:
            names.append(self.env.instance)
        names.append(level)
        if self._getConfig('add_time_stamp'):
            names.append(self.timestamp)
        names = filter(lambda x: x, names)
        return f"{'_'.join(names)}.{self._getConfig('ext')}"

    def _buildLogger(self):
        """Build the logger by creating and attaching handlers."""
        log_formatter = logging.Formatter("%(asctime)s <%(levelname)s> %(message)s  \t(%(name)s.%(funcName)s)")
        # logger = logging.getLogger(self.project_name if self.project_name else __name__)
        logger = logging.getLogger()  # Root logger
        logger.handlers = []
        logger.setLevel(logging.DEBUG)

        # File loggers
        if self.logs_dir and self._getConfig('add_file_handler'):
            max_bytes, backup_count = self._getConfig('max_bytes'), self._getConfig('backup_count')
            for level in ['debug', 'info', 'warning']:
                file_path = path.abspath(f"{self.logs_dir}/" + self._getLogFileName(level))
                file_handler = RotatingFileHandler(file_path, maxBytes=max_bytes, backupCount=backup_count)
                file_handler.setLevel(getattr(logging, level.upper()))
                file_handler.setFormatter(log_formatter)
                logger.addHandler(file_handler)

        # Console logger
        if self._getConfig('add_console_handler'):
            console_handler = logging.StreamHandler()
            console_handler.setLevel(getattr(logging, self.log_level))
            console_handler.setFormatter(log_formatter)
            logger.addHandler(console_handler)

        return logger

    def cleanLogs(self):
        """Remove old log files (clean cache)"""
        now = time.time()
        age_limit = self._getConfig("age_limit")

        for filename in listdir(self.logs_dir):
            file_path = path.abspath(f"{self.logs_dir}/" + filename)
            if not path.isfile(file_path) or not filename.endswith(self._getConfig('ext')):
                continue  # Not expected log file or ext
            creation_time = path.getctime(file_path)
            if now - creation_time < age_limit:
                continue  # Not aged enough
            # Remove aged files
            try:
                os_remove(file_path)
                _logger.debug(f"Deleted old log file: {filename}")
            except PermissionError:
                _logger.warning(f"Failed to delete old log file due to permissions: {filename}")

    def getLogger(self):
        return self.logger

    def close(self):
        """Shut down the logger and close all handlers."""
        handlers = self.logger.handlers[:]
        for handler in handlers:
            handler.close()
            self.logger.removeHandler(handler)
        _logger.debug("Logger closed successfully.")
