import unittest
from os import path as os_path
from unittest.mock import patch

from src.pyanitrack.utils.env import Env


class TestEnv(unittest.TestCase):

    def setUp(self):
        self.config_path = "path/to/config"
        self.default_kwargs = {
            "project_name": "TestProject",
            "project_name_text": "Test Project",
            "version": "1.0.0",
            "instance": "test_instance",
            "project_dir": "path/to/project",
        }

    @patch("src.pyanitrack.utils.env.os_path.exists")
    @patch("src.pyanitrack.utils.env.Config")
    @patch("src.pyanitrack.utils.env.LoggerHandler")
    def test_init_creates_logger_and_config(self, mock_logger_handler, mock_config, mock_exist_path):
        """Test that Env initializes with a config and logger correctly."""
        def config_get_side_effect(key, default={}):
            """Simulate log config."""
            if key == "logs":
                return {"no_logs": False, "max_bytes": 1024 * 1024, "backup_count": 3}
            return default

        # Set the side_effect for the config.get() method
        mock_config.return_value.get.side_effect = config_get_side_effect

        env = Env(self.config_path, logs_dir="path/to/logs", **self.default_kwargs)
        mock_config.assert_called_once_with(self.config_path, env=env, project_name="TestProject",
                                            project_name_text="Test Project", version="1.0.0",
                                            instance="test_instance", project_dir='path/to/project')
        mock_logger_handler.assert_called_once_with("path/to/logs", project_name="TestProject",
                                                    instance="test_instance", no_logs=False, max_bytes=1024 * 1024,
                                                    backup_count=3)

    @patch("src.pyanitrack.utils.env.os_path.exists")
    @patch("src.pyanitrack.utils.env.Config")
    def test_call_updates_attributes(self, mock_config, mock_exist_path):
        """Test that calling the Env instance dynamically updates its attributes."""

        env = Env(self.config_path, **self.default_kwargs)
        env(project_name="UpdatedProject", version="2.0.0")

        with patch("src.pyanitrack.utils.env._logger.warning") as mock_warning:
            env(unexpected_key="unexpected_value")
            mock_warning.assert_called_once_with("Unexpected key, got: unexpected_key")

        self.assertEqual(env.project_name, "UpdatedProject")
        self.assertEqual(env.version, "2.0.0")

    @patch("src.pyanitrack.utils.env.os_path.exists")
    @patch("src.pyanitrack.utils.env.Config")
    @patch("src.pyanitrack.utils.env.LoggerHandler")
    def test_init_no_logger_if_no_logs(self, mock_logger_handler, mock_config, mock_exist_path):
        """Test that the logger is not initialized if `no_logs` is set to True."""
        def config_get_side_effect(key, default={}):
            """Simulate log config."""
            if key == "logs":
                return {"no_logs": True}
            return default

        # Set the side_effect for the config.get() method
        mock_config.return_value.get.side_effect = config_get_side_effect

        env = Env(self.config_path, **self.default_kwargs)

        mock_logger_handler.assert_not_called()

    @patch("src.pyanitrack.utils.env.Config")
    @patch("src.pyanitrack.utils.env.os_path.exists", return_value=True)
    def test_project_dir_validation(self, mock_exist_path, mock_config):
        """Test that the project directory validation works correctly."""
        env = Env(self.config_path, **self.default_kwargs)

        self.assertEqual(env.project_dir, os_path.abspath("path/to/project"))
        mock_exist_path.assert_called_once_with(os_path.abspath("path/to/project"))

    @patch("src.pyanitrack.utils.env.os_path.exists", return_value=False)
    def test_invalid_project_dir_validation(self, mock_exist_path):
        """Test that the project directory validation works correctly."""
        with self.assertRaises(FileExistsError):
            env = Env(self.config_path, **self.default_kwargs)

    @patch("src.pyanitrack.utils.env.Config")
    @patch("src.pyanitrack.utils.env.os_path.exists", return_value=True)
    def test_env_str_and_repr(self, mock_exist_path, mock_config):
        """Test that the Env's __str__ and __repr__ methods return expected values."""
        env = Env(self.config_path, **self.default_kwargs)
        expected_str = "Env(project='Test Project', version='1.0.0')"
        self.assertEqual(str(env), expected_str)
        self.assertEqual(repr(env), expected_str)

    @patch("src.pyanitrack.utils.env.Config")
    @patch("src.pyanitrack.utils.env.os_path.exists", return_value=True)
    def test_env_equality(self, mock_exist_path, mock_config):
        """Test that the equality and inequality checks for Env instances work."""
        env1 = Env(self.config_path, **self.default_kwargs)
        env2 = Env(self.config_path, **self.default_kwargs)

        self.assertEqual(env1, env1)
        self.assertNotEqual(env1, env2)


if __name__ == "__main__":
    unittest.main()
