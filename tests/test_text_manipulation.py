import unittest
from src.pyanitrack.utils.text_manipulation import (camelToSnake, snakeToCamel, stripText, sanitiseText,
                                                    sanitiseTextCommon)


class TestTextManipulation(unittest.TestCase):

    def test_camel_to_snake(self):
        """Test cases for camelToSnake."""
        # Basic conversions
        self.assertEqual(camelToSnake('CamelCase'), 'camel_case')
        self.assertEqual(camelToSnake('ThisIsATest'), 'this_is_a_test')

        # Already in snake_case
        self.assertEqual(camelToSnake('already_snake_case'), 'already_snake_case')

        # Single word (no underscores expected)
        self.assertEqual(camelToSnake('Word'), 'word')

        # Numbers in camel case
        self.assertEqual(camelToSnake('CamelCase123'), 'camel_case123')
        self.assertEqual(camelToSnake('Camel123Case'), 'camel123_case')

    def test_snake_to_camel(self):
        """Test cases for snakeToCamel."""
        # Basic conversions
        self.assertEqual(snakeToCamel('snake_case'), 'snakeCase')
        self.assertEqual(snakeToCamel('this_is_a_test'), 'thisIsATest')

        # Already in CamelCase
        self.assertEqual(snakeToCamel('CamelCase'), 'CamelCase')

        # Single word (should remain the same)
        self.assertEqual(snakeToCamel('word'), 'word')

        # Numbers in snake case
        self.assertEqual(snakeToCamel('snake_case_123'), 'snakeCase123')
        self.assertEqual(snakeToCamel('snake_123_case'), 'snake123Case')

    def test_edge_cases(self):
        """Test edge cases for both methods."""
        # Empty string
        self.assertEqual(camelToSnake(''), '')
        self.assertEqual(snakeToCamel(''), '')

        # Single character
        self.assertEqual(camelToSnake('A'), 'a')
        self.assertEqual(snakeToCamel('a'), 'a')

        # Non-alphanumeric characters
        self.assertEqual(camelToSnake('Camel@Case'), 'camel@_case')
        self.assertEqual(snakeToCamel('snake_case@'), 'snakeCase@')


class TestTextManipulationStripText(unittest.TestCase):

    def test_default_strip(self):
        """Test default stripping behavior."""
        # Basic stripping with default settings
        self.assertEqual(stripText('Hello World!'), 'hello_world')
        self.assertEqual(stripText('   Special  characters!@$'), 'special_characters')

        # Stripping with custom replace_with character
        self.assertEqual(stripText('Hello World!', replace_with='-'), 'hello-world')

    def test_lower_false(self):
        """Test when the lower parameter is set to False."""
        self.assertEqual(stripText('Hello World!', lower=False), 'Hello_World')

    def test_strip_false(self):
        """Test when the strip parameter is set to False."""
        self.assertEqual(stripText('***Hello***World***', replace_with='*', strip=False), '*hello*world*')

    def test_custom_default_set(self):
        """Test with a custom default set of characters to replace."""
        default = set('abc')
        self.assertEqual(stripText('abcHello World!', default=default), 'hello world!')
        self.assertEqual(stripText('Cabin', default=default), 'in')

    def test_include_characters(self):
        """Test including additional characters to replace."""
        include = set('&')
        self.assertEqual(stripText('Hello & World!', include=include), 'hello_world')

    def test_exclude_characters(self):
        """Test excluding characters from being replaced."""
        exclude = set('!')
        self.assertEqual(stripText('Hello World!', exclude=exclude), 'hello_world!')

    def test_edge_cases(self):
        """Test edge cases for stripText."""
        # Empty string
        self.assertEqual(stripText(''), '')

        # No characters to replace
        self.assertEqual(stripText('No special chars'), 'no_special_chars')

        # String already processed
        self.assertEqual(stripText('hello_world'), 'hello_world')

    def test_replace_with_multiple_chars(self):
        """Test replace_with value longer than 1 character."""
        self.assertEqual(stripText('Hello World!', replace_with='__'), 'hello__world')

    def test_multiple_replacement_handling(self):
        """Test multiple consecutive replace_with characters are reduced to one."""
        self.assertEqual(stripText('Hello!!   World@@!!', replace_with='_'), 'hello_world')


class TestTextManipulationSanitiseText(unittest.TestCase):

    def test_sanitise_replace_and_remove(self):
        """Test sanitiseText with both replace_ and remove_ sets."""
        raw_text = 'Hello - World! @Example_Test'
        replace_set = {' ', '-'}
        remove_set = {'!', '@'}
        expected_output = 'hello_world_example_test'
        result = sanitiseText(raw_text, replace_=replace_set, remove_=remove_set, sep='_')
        self.assertEqual(result, expected_output)

    def test_sanitise_replace_only(self):
        """Test sanitiseText with only replace_ set."""
        raw_text = 'Some - text to replace'
        replace_set = {' '}
        expected_output = 'some_-_text_to_replace'
        result = sanitiseText(raw_text, replace_=replace_set, sep='_')
        self.assertEqual(result, expected_output)

    def test_sanitise_remove_only(self):
        """Test sanitiseText with only remove_ set."""
        raw_text = 'Remove these characters: !@#'
        remove_set = {'!', '@', '#'}
        expected_output = 'remove these characters:'
        result = sanitiseText(raw_text, remove_=remove_set, sep=' ')
        self.assertEqual(result, expected_output)

    def test_sanitise_no_replace_or_remove(self):
        """Test sanitiseText with no replace_ or remove_ sets."""
        raw_text = 'No_replacements_or_removals_here'
        expected_output = 'no_replacements_or_removals_here'
        result = sanitiseText(raw_text, sep='_')
        self.assertEqual(result, expected_output)

    def test_sanitise_common(self):
        """Test sanitiseTextCommon with common operations."""
        raw_text = 'Common - Sanitisation | Test; This is #Text!'
        expected_output = 'common_sanitisation_test_this_is_text'
        result = sanitiseTextCommon(raw_text)
        self.assertEqual(result, expected_output)

    def test_sanitise_common_empty_input(self):
        """Test sanitiseTextCommon with empty input."""
        raw_text = ''
        expected_output = ''
        result = sanitiseTextCommon(raw_text)
        self.assertEqual(result, expected_output)


if __name__ == '__main__':
    unittest.main()
