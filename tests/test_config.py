import logging
import unittest
from configparser import ConfigParser, DuplicateOptionError
from os import path as os_path
from unittest.mock import patch, mock_open

from src.pyanitrack.utils import joinPath
from src.pyanitrack.utils.config import Config, checkConfigPath
from src.pyanitrack.utils.env import Env

_logger = logging.getLogger(__name__)

TESTS_DIR = os_path.dirname(os_path.abspath(__file__))

CONFIG_CONTENT = """
[default]
Test: False
[Section1]
param1: 10
param2: 'value'
"""

DUPLICATE_OPTION_CONFIG_CONTENT = """
[Section1]
param1 = value1
param1 = value2  # Duplicate option, should raise an error
"""


class TestConfig(unittest.TestCase):

    def setUp(self):
        # Prepare necessary paths and values for tests
        self.valid_config_path = os_path.abspath(TESTS_DIR + '/test_data/pyanitrack.conf')
        self.invalid_config_path = os_path.abspath('/invalid/path/to/config.conf')

    @patch('os.path.exists', return_value=True)
    def test_check_valid_config_path(self, mock_exists):
        """Test the check for a valid config file path."""
        self.assertTrue(checkConfigPath(self.valid_config_path))
        mock_exists.assert_called_once_with(self.valid_config_path)

    @patch('os.path.exists', return_value=False)
    def test_check_invalid_config_path(self, mock_exists):
        """Test the check for an invalid config file path raises an error."""
        with self.assertRaises(FileExistsError):
            checkConfigPath(self.invalid_config_path)
        mock_exists.assert_called_once_with(self.invalid_config_path)

    @patch('builtins.open', new_callable=mock_open, read_data=CONFIG_CONTENT)
    @patch('os.path.exists', return_value=True)
    def test_load_config(self, mock_exists, mock_file):
        """Test loading of a valid config file."""
        config = Config(self.valid_config_path)
        self.assertIsInstance(config, Config)
        self.assertEqual(config.get('default'), {'Test': False})
        self.assertEqual(config['Section1']['param1'], 10)
        self.assertEqual(config['Section1']['param2'], "value")
        self.assertEqual(str(config), "{'default': {'Test': False}, 'Section1': {'param1': 10, 'param2': 'value'}}")
        self.assertEqual(repr(config), "Config({'default': {'Test': False}, 'Section1': {'param1': 10, 'param2': 'value'}})")

    @patch('builtins.open', new_callable=mock_open, read_data=DUPLICATE_OPTION_CONFIG_CONTENT)
    @patch('os.path.exists', return_value=True)
    @patch('src.pyanitrack.utils.config._logger')
    def test_load_config_duplicate_option_error(self, mock_logger, mock_exists, mock_file):
        """Test handling of DuplicateOptionError in config loading."""
        with self.assertRaises(DuplicateOptionError):
            config = Config(config_path="dummy_path")
        mock_logger.error.assert_called_once()
        self.assertIn("Duplicate Option Error occurred", mock_logger.error.call_args[0][0])

    @patch('os.path.exists', return_value=False)
    def test_load_missing_config(self, mock_exists):
        """Test handling of a missing config file."""
        with self.assertRaises(FileExistsError):
            Config(self.invalid_config_path)

    def test_split_path_into_dir_and_name(self):
        """Test splitting a path into directory and filename."""
        config = Config(self.valid_config_path)
        directory, filename = config._splitPathIntoDirAndName(self.valid_config_path)
        self.assertEqual(directory, os_path.dirname(self.valid_config_path))
        self.assertEqual(filename, os_path.basename(self.valid_config_path))

    def test_split_invalid_path(self):
        """Test handling of an invalid path format."""
        config = Config(self.valid_config_path)
        self.assertFalse(config._splitPathIntoDirAndName('invalid_config.txt'))
        self.assertFalse(config._splitPathIntoDirAndName(''))
        self.assertFalse(config._splitPathIntoDirAndName(False))

    @patch('builtins.open', new_callable=mock_open, read_data=CONFIG_CONTENT)
    @patch('src.pyanitrack.utils.config._logger')
    def test_save_config(self, mock_logger, mock_file):
        """Test saving the current configuration attributes back to the config file."""
        config = Config(self.valid_config_path)
        config['default'] = {'Test': True}
        config['Section1'] = {'param1': 10, 'param2': 'value'}

        config.saveConfig()
        mock_logger.info.assert_called_once_with(f"Config saved to '{self.valid_config_path}'")
        config_path = os_path.join(config.config_dir, config.filename)

        mock_file.assert_called_with(config_path, 'w')
        handle = mock_file()

        # Verify the written content
        written_content = ''.join(call[0][0] for call in handle.write.call_args_list)
        self.assertIn('[default]\n', written_content)
        self.assertIn('test = True\n', written_content)
        self.assertIn('[Section1]\n', written_content)
        self.assertIn('param1 = 10\n', written_content)
        self.assertIn('param2 = value\n', written_content)

        config.filename = ''
        config.saveConfig()
        config_path = joinPath(os_path.abspath(TESTS_DIR + '/test_data'), config.DEFAULT_PROFILE_NAME, ext=config.CONFIG_EXT)
        mock_logger.info.assert_any_call(f"Config saved to '{config_path}'")

    def test_unload_config(self):
        """Test removing section attributes from Config."""
        config = Config(self.valid_config_path)
        config._config = {'default': {'Test': True}, 'Section1': {'param1': 10}}
        config._sections = ['default', 'Section1']
        config.unloadConfig()
        self.assertFalse(hasattr(config, 'default'))
        self.assertFalse(hasattr(config, 'Section1'))
        self.assertEqual(config._sections, [])

    @patch('builtins.open', new_callable=mock_open, read_data=CONFIG_CONTENT)
    def test_load_section(self, mock_file):
        """Test loading a specific section from a config file."""
        config = Config(self.valid_config_path)
        parser = ConfigParser()
        parser.read_string(CONFIG_CONTENT)
        section_data = config.loadSection(self.valid_config_path, parser, 'Section1')
        self.assertEqual(section_data, {'param1': 10, 'param2': 'value'})

        config = Config(self.valid_config_path)
        config.loadConfig(sections='Section1')
        self.assertEqual(section_data, {'param1': 10, 'param2': 'value'})

    @patch('builtins.open', new_callable=mock_open, read_data=CONFIG_CONTENT)
    @patch('src.pyanitrack.utils.config._logger')
    def test_load_nonexistent_section(self, mock_logger, mock_file):
        """Test loading a nonexistent section from a config file."""
        config = Config('')
        self.assertFalse(config.config_path)
        parser = ConfigParser()
        parser.read_string(CONFIG_CONTENT)
        section_data = config.loadSection(self.valid_config_path, parser, 'Test Test')
        self.assertEqual(section_data, {})
        mock_logger.error.assert_called_once_with(f"Section 'Test Test' not found in '{self.valid_config_path}'")

    @patch('builtins.open', new_callable=mock_open, read_data=CONFIG_CONTENT)
    @patch('os.path.exists', return_value=True)
    def test_set_config(self, mock_exists, mock_file):
        """Test setting configuration attributes."""
        config = Config(self.valid_config_path)
        new_config = {'default': {'NewParam': 123}}
        config.setConfig(new_config)
        self.assertEqual(config.get('default'), {'Test': False, 'NewParam': 123})
        self.assertEqual(str(config), "{'default': {'Test': False, 'NewParam': 123}, 'Section1': {'param1': 10, 'param2': 'value'}}")

    @patch('builtins.open', new_callable=mock_open, read_data=CONFIG_CONTENT)
    @patch('os.path.exists', return_value=True)
    def test_load_config_with_env(self, mock_exists, mock_file):
        """Test loading of a valid config file with Env."""
        config = Env(self.valid_config_path, project_name="test").config
        self.assertIsInstance(config, Config)
        self.assertEqual(config.filename, 'pyanitrack.conf')
        self.assertEqual(repr(config), "test.Config({'default': {'Test': False}, 'Section1': {'param1': 10, 'param2': 'value'}})")
        config.env.project_name_text = "Test"
        self.assertEqual(repr(config), "Test.Config({'default': {'Test': False}, 'Section1': {'param1': 10, 'param2': 'value'}})")

    def test_config_with_env(self):
        """Test config with Env."""
        config = Env('', project_name="test").config
        self.assertIsInstance(config, Config)
        self.assertEqual(config.filename, 'test')

    @patch('src.pyanitrack.utils.config._logger')
    @patch('src.pyanitrack.utils.addEnvPath')
    def test_add_env_paths_success(self, mock_addEnvPath, mock_logger):
        """Test adding env paths success."""
        env_paths = {
            "PATH1": "/some/path1",
            "PATH2": "/some/path2",
        }

        config = Config(self.valid_config_path)
        config.env_paths = env_paths

        config.addEnvPaths()

        mock_addEnvPath.assert_any_call("/some/path1", env_name="PATH1")
        mock_addEnvPath.assert_any_call("/some/path2", env_name="PATH2")
        mock_logger.info.assert_called_once_with("Environment paths have been added")

    @patch('src.pyanitrack.utils.config._logger')
    @patch('src.pyanitrack.utils.addEnvPath')
    def test_add_env_paths_no_env_paths(self, mock_addEnvPath, mock_logger):
        """Test adding env paths without env paths."""
        config = Config(self.valid_config_path)
        self.assertFalse(hasattr(config, "env_paths"))

        config.addEnvPaths()

        mock_addEnvPath.assert_not_called()
        mock_logger.info.assert_not_called()

