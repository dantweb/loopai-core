import unittest
import json
from unittest.mock import Mock, patch
from PIL import Image
import io
import sys
import os

# Add the core directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from core.models.broadcast_data import BroadcastData


class TestBroadcastData(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures before each test method."""
        pass

    def tearDown(self):
        """Clean up after each test method."""
        pass

    # Constructor Tests
    def test_init_with_none(self):
        """Test initialization with None input."""
        bd = BroadcastData(None)
        self.assertIsNone(bd.data)
        self.assertEqual(bd.properties, [])
        self.assertIsNone(bd.image)

    def test_init_with_dict(self):
        """Test initialization with dictionary input."""
        test_dict = {"key1": "value1", "key2": 42}
        bd = BroadcastData(test_dict)
        self.assertEqual(bd.data, test_dict)
        self.assertIn("str", bd.properties)
        self.assertIn("int", bd.properties)

    def test_init_with_list(self):
        """Test initialization with list input."""
        test_list = [{"key1": "value1"}, {"key2": "value2"}]
        bd = BroadcastData(test_list)
        self.assertEqual(bd.data, test_list)
        self.assertIn("str", bd.properties)

    def test_init_with_valid_json_string(self):
        """Test initialization with valid JSON string."""
        json_string = '{"key": "value", "number": 123}'
        bd = BroadcastData(json_string)
        self.assertEqual(bd.data["key"], "value")
        self.assertEqual(bd.data["number"], 123)

    def test_init_with_invalid_json_string(self):
        """Test initialization with invalid JSON string."""
        invalid_json = "not json"
        bd = BroadcastData(invalid_json)
        self.assertEqual(bd.data, {})

    def test_init_with_broadcast_data(self):
        """Test initialization with another BroadcastData object."""
        original_data = {"key": "value"}
        bd1 = BroadcastData(original_data)
        bd2 = BroadcastData(bd1)
        self.assertEqual(bd2.data, original_data)

    def test_init_with_other_type(self):
        """Test initialization with other data types."""
        bd = BroadcastData(123)
        self.assertEqual(bd.data, {})

    # JSON Normalization Tests
    def test_normalize_single_quotes_to_double_quotes(self):
        """Test normalization of single quotes to double quotes."""
        test_data = {"text": "{'key': 'value'}"}
        bd = BroadcastData(test_data)
        # The JSON string should be parsed and converted to a dict
        self.assertIsInstance(bd.data["text"], dict)
        self.assertEqual(bd.data["text"]["key"], "value")

    def test_normalize_python_literals(self):
        """Test normalization of Python literals to JSON equivalents."""
        test_data = {"text": "{'boolean': True, 'null_value': None, 'false_val': False}"}
        bd = BroadcastData(test_data)
        self.assertEqual(bd.data["text"]["boolean"], True)
        self.assertIsNone(bd.data["text"]["null_value"])
        self.assertEqual(bd.data["text"]["false_val"], False)

    def test_normalize_unquoted_keys(self):
        """Test normalization of unquoted keys."""
        test_data = {"text": "{key: 'value', number: 42}"}
        bd = BroadcastData(test_data)
        self.assertIsInstance(bd.data["text"], dict)
        self.assertEqual(bd.data["text"]["key"], "value")
        self.assertEqual(bd.data["text"]["number"], 42)

    def test_normalize_trailing_commas(self):
        """Test removal of trailing commas."""
        test_data = {"text": "{'key1': 'value1', 'key2': 'value2',}"}
        bd = BroadcastData(test_data)
        self.assertIsInstance(bd.data["text"], dict)
        self.assertEqual(len(bd.data["text"]), 2)

    def test_normalize_nested_json_strings(self):
        """Test normalization of nested JSON strings."""
        test_data = {
            "level1": {
                "level2": "{'switch_executor': 'llm'}"
            }
        }
        bd = BroadcastData(test_data)
        self.assertIsInstance(bd.data["level1"]["level2"], dict)
        self.assertEqual(bd.data["level1"]["level2"]["switch_executor"], "llm")

    def test_normalize_json_in_list(self):
        """Test normalization of JSON strings within lists."""
        test_data = {
            "items": ["{'key': 'value1'}", "{'key': 'value2'}"]
        }
        bd = BroadcastData(test_data)
        self.assertIsInstance(bd.data["items"][0], dict)
        self.assertIsInstance(bd.data["items"][1], dict)
        self.assertEqual(bd.data["items"][0]["key"], "value1")
        self.assertEqual(bd.data["items"][1]["key"], "value2")

    def test_looks_like_json_detection(self):
        """Test the _looks_like_json method."""
        bd = BroadcastData({})

        # Should detect JSON-like strings
        self.assertTrue(bd._looks_like_json("{'key': 'value'}"))
        self.assertTrue(bd._looks_like_json('{"key": "value"}'))
        self.assertTrue(bd._looks_like_json("[1, 2, 3]"))
        self.assertTrue(bd._looks_like_json("[]"))
        self.assertTrue(bd._looks_like_json("{}"))

        # Should not detect non-JSON strings
        self.assertFalse(bd._looks_like_json("regular string"))
        self.assertFalse(bd._looks_like_json("123"))
        self.assertFalse(bd._looks_like_json(""))
        self.assertFalse(bd._looks_like_json(None))

    # Method Tests
    def test_has_method_with_dict(self):
        """Test has method with dictionary data."""
        bd = BroadcastData({"key1": "value1", "key2": "value2"})
        self.assertTrue(bd.has("key1"))
        self.assertFalse(bd.has("key3"))

    def test_has_method_with_list(self):
        """Test has method with list data."""
        bd = BroadcastData([{"key1": "value1"}, {"key2": "value2"}])
        self.assertTrue(bd.has("key1"))
        self.assertTrue(bd.has("key2"))
        self.assertFalse(bd.has("key3"))

    def test_get_method_with_dict(self):
        """Test get method with dictionary data."""
        bd = BroadcastData({"key1": "value1", "key2": "value2"})
        self.assertEqual(bd.get("key1"), "value1")
        self.assertEqual(bd.get("key3", "default"), "default")

    def test_get_method_with_list(self):
        """Test get method with list data."""
        bd = BroadcastData([{"key1": "value1"}, {"key1": "value2"}])
        result = bd.get("key1")
        self.assertIsInstance(result, list)
        self.assertIn("value1", result)
        self.assertIn("value2", result)

    def test_set_method(self):
        """Test set method."""
        bd = BroadcastData({})
        bd.set("new_key", "new_value")
        self.assertEqual(bd.data["new_key"], "new_value")
        self.assertIn("str", bd.properties)

    def test_to_json_method(self):
        """Test to_json method."""
        test_data = {"key": "value", "number": 42}
        bd = BroadcastData(test_data)
        json_output = bd.to_json()
        parsed = json.loads(json_output)
        self.assertEqual(parsed["key"], "value")
        self.assertEqual(parsed["number"], 42)

    def test_to_dict_method(self):
        """Test to_dict method."""
        test_data = {"key": "value"}
        bd = BroadcastData(test_data)
        dict_output = json.loads(bd.to_json())
        self.assertEqual(dict_output, test_data)

    def test_flatten_data_method(self):
        """Test flatten_data method."""
        nested_data = {
            "level1": {
                "level2": {
                    "key": "value"
                }
            },
            "array": [1, 2, 3]
        }
        bd = BroadcastData(nested_data)
        flattened = bd.flatten_data()

        self.assertIn("level1_level2_key", flattened)
        self.assertEqual(flattened["level1_level2_key"], "value")
        self.assertIn("array_0", flattened)
        self.assertEqual(flattened["array_0"], 1)

    def test_find_value_recursive_by_key(self):
        """Test find_value_recursive_by_key method."""
        test_data = {
            "switch_executor": "llm",
            "nested": {
                "switch_executor": "gpt"
            },
            "list": "[{\"switch_executor\": \"replicate\"}]",
            "wierd": "{'wierd01': 'garyb'}",
            "wierd2": "{\'very_wierd\': \'garyb2\'}",
            "other": '{"one_another":  {"more_strange_" : "even more complex"} }'
        }
        bd = BroadcastData(test_data)

        results = list(bd.find_value_recursive_by_key("switch_executor"))
        self.assertEqual(len(results), 3)
        self.assertIn("llm", results)
        self.assertIn("gpt", results)
        self.assertEqual(bd.get("wierd")["wierd01"], "garyb")  # Corrected from bd["wierd"][0]["wierd"]
        self.assertEqual(bd.get("wierd2")["very_wierd"], "garyb2")  # Corrected from bd["wierd2"][0]["very_wierd"]
        self.assertEqual(bd.get("other")["one_another"]["more_strange_"], "even more complex")  # Corrected from bd["wierd2"][0]["very_wierd"]


    def test_find_value_recursive_by_key_with_normalized_json(self):
        """Test find_value_recursive_by_key with JSON strings that get normalized."""
        test_data = {
            "text": "{'switch_executor': 'llm'}",
            "other_data": "regular string"
        }
        bd = BroadcastData(test_data)
        results = list(bd.find_value_recursive_by_key("switch_executor"))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], "llm")

    def test_get_unique_key_method(self):
        """Test get_unique_key method."""
        bd = BroadcastData({})
        existing_keys = {"key": 1, "key_1": 2}
        unique_key = bd.get_unique_key("key", existing_keys)
        self.assertEqual(unique_key, "key_2")

    # Edge Cases
    def test_malformed_json_handling(self):
        """Test handling of malformed JSON that can't be fixed."""
        test_data = {"text": "{this is not json at all}"}
        bd = BroadcastData(test_data)
        # Should remain as string since it can't be parsed
        self.assertIsInstance(bd.data["text"], str)

    def test_empty_json_strings(self):
        """Test handling of empty JSON strings."""
        test_data = {"empty_object": "{}", "empty_array": "[]"}
        bd = BroadcastData(test_data)
        self.assertEqual(bd.data["empty_object"], {})
        self.assertEqual(bd.data["empty_array"], [])

    def test_deeply_nested_structure(self):
        """Test with deeply nested data structure."""
        deep_data = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": "{'final_key': 'final_value'}"
                    }
                }
            }
        }
        bd = BroadcastData(deep_data)
        results = list(bd.find_value_recursive_by_key("final_key"))

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], "final_value")

    def test_properties_tracking(self):
        """Test that properties are correctly tracked."""
        test_data = {"string": "text", "number": 42, "boolean": True}
        bd = BroadcastData(test_data)
        self.assertIn("str", bd.properties)
        self.assertIn("int", bd.properties)
        self.assertIn("bool", bd.properties)

    def test_filesystem_adapter_compatibility(self):
        """Test that JSON normalization works with filesystem adapter expected data."""
        # This simulates the data structure that's causing test failures
        test_data = {
            "result": {
                "response": {
                    "updated_files": [
                        {
                            "path": "post/inbox/new/message1756287702.json",
                            "file_operation": "update",
                            "file_content": '{"message": {"from": "FRBG/cityhall", "to": "FRBG/Agent_hwp2bg", "data": "Test message"}}'
                        }
                    ]
                }
            }
        }
        bd = BroadcastData(test_data)

        # The JSON string in file_content should be parsed into an object
        file_content = bd.data["result"]["response"]["updated_files"][0]["file_content"]
        self.assertIsInstance(file_content, dict)
        self.assertEqual(file_content["message"]["from"], "FRBG/cityhall")

    def test_broadcast_adapter_compatibility(self):
        """Test that JSON normalization works with broadcast adapter expected data."""
        test_data = {
            'result': {
                'model_id': 'meta-llama/Meta-Llama-3.1-8B-Instruct',
                'step_id': 'loop_step1',
                'result': {
                    'summary': 'AI-powered cooling systems slash energy consumption in data centres'
                }
            }
        }
        bd = BroadcastData(test_data)

        # Verify the structure is maintained correctly
        self.assertEqual(bd.data['result']['result']['summary'],
                         'AI-powered cooling systems slash energy consumption in data centres')

    def test_real_world_json_normalization(self):
        """Test with real-world malformed JSON data."""
        # Common malformed JSON patterns found in logs
        test_cases = [
            {"text": "{'switch_executor': 'llm'}"},  # Single quotes
            {"text": "{switch_executor: 'llm'}"},  # Unquoted keys
            {"text": "{'key': True, 'null': None}"},  # Python literals
            {"text": "{'key1': 'value1', 'key2': 'value2',}"},  # Trailing comma
        ]

        for test_data in test_cases:
            with self.subTest(test_data=test_data):
                bd = BroadcastData(test_data)
                # All should be parsed as dict objects
                self.assertIsInstance(bd.data["text"], dict)


if __name__ == '__main__':
    unittest.main()