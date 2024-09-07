import logging
import unittest
from configparser import ConfigParser
from os import path as os_path
from unittest.mock import patch, mock_open

from src.pyanitrack.utils.config import Config, checkConfigPath

_logger = logging.getLogger(__name__)

TESTS_DIR = os_path.dirname(os_path.abspath(__file__))

CONFIG_CONTENT = """
[default]
Test: False
[Section1]
param1: 10
param2: 'value'
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

    @patch('builtins.open', new_callable=mock_open, read_data=CONFIG_CONTENT)
    def test_save_config(self, mock_file):
        """Test saving the current configuration attributes back to the config file."""
        config = Config(self.valid_config_path)
        config['default'] = {'Test': True}
        config['Section1'] = {'param1': 10, 'param2': 'value'}

        config.saveConfig()
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

    # @patch('builtins.open', new_callable=mock_open, read_data=CONFIG_CONTENT)
    # def test_load_nonexistent_section(self, mock_file):
    #     """Test handling of loading a nonexistent section."""
    #     config = Config(self.valid_config_path)
    #     parser = ConfigParser()
    #     parser.read_string(self.CONFIG_CONTENT)
    #     with self.assertLogs(_logger, level='ERROR') as log:
    #         section_data = config.loadSection(self.valid_config_path, parser, 'NonexistentSection')
    #         self.assertEqual(section_data, {})
    #         self.assertIn("Section 'NonexistentSection' not found", log.output[0])

    @patch('builtins.open', new_callable=mock_open, read_data=CONFIG_CONTENT)
    @patch('os.path.exists', return_value=True)
    def test_set_config(self, mock_exists, mock_file):
        """Test setting configuration attributes."""
        config = Config(self.valid_config_path)
        new_config = {'default': {'NewParam': 123}}
        config.setConfig(new_config)
        self.assertEqual(config.get('default'), {'Test': False, 'NewParam': 123})
