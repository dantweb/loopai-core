import unittest
from unittest.mock import MagicMock

from core.models.broadcast_data import BroadcastData


class MockLogger:
    def __init__(self):
        self.error = MagicMock()

class MockAdapter:
    def __init__(self):
        self.logger = MockLogger()

    def get_nested_data(self, data, field):
        """
        Traverse a potentially nested dictionary (or JSON-like structure)
        using a '/'-delimited field path. If a value is encountered that is a string,
        try to parse it as JSON and continue traversal on the parsed object.
        """
        import json
        keys = field.split('/')

        def recurse(current_data, remaining_keys):
            if not remaining_keys:
                return current_data

            # If current_data is a string, try parsing it as JSON before proceeding
            if isinstance(current_data, str):
                # Attempt to convert single quotes to double quotes
                # (Not recommended for production, but as a workaround)
                current_data = current_data.replace("'", '"')
                try:
                    current_data = json.loads(current_data)
                except json.JSONDecodeError as e:
                    if self.logger:
                        self.logger.error(f"Failed to parse JSON: {e}")
                    return None

            if not isinstance(current_data, dict):
                if self.logger:
                    self.logger.error(f"Expected dict but got {type(current_data)}: {current_data}")
                return None

            key = remaining_keys[0]
            if key not in current_data:
                if self.logger:
                    self.logger.error(f"Key '{key}' not found in current data: {current_data}")
                return None

            return recurse(current_data[key], remaining_keys[1:])

        return recurse(data, keys)


class TestGetNestedData(unittest.TestCase):

    def setUp(self):
        self.adapter = MockAdapter()

    def test_successful_retrieval_nested_dict(self):
        # Given a nested dictionary
        data = {
            "level1": {
                "level2": {
                    "value": 42
                }
            }
        }
        field = "level1/level2/value"
        result = self.adapter.get_nested_data(data, field)
        self.assertEqual(result, 42, "Should retrieve the nested value correctly.")


    def test_successful_retrieval_complex_nested_dict(self):
        # Given a nested dictionary
        data = {
            "level1": {
                "level2": "{ 'value': 42 }"
            }
        }
        field = "level1/level2/value"
        result = self.adapter.get_nested_data(data, field)
        self.assertEqual(result, 42, "Should retrieve the nested value correctly.")


    def test_successful_retrieval_complex_nested2_dict(self):
        # Given a nested dictionary
        data = {
            "level1": {
                "level2": "{ \"value\": 42 }"
            }
        }
        field = "level1/level2/value"
        result = self.adapter.get_nested_data(data, field)
        self.assertEqual(result, 42, "Should retrieve the nested value correctly.")

    def test_successful_retrieval_complex_nested3_dict(self):
        # Given a nested dictionary
        data = '{"saved": {"model_id": "meta-llama/Meta-Llama-3.1-70B-Instruct", "step_id": "loop_step1", "result": {"title": "AI Revolution Gains Momentum: Humanoid Robots and Generative AI Transform Industries", "summary": "Latest AI and robotics advancements revolutionize industries and daily life", "tags": "AI, robotics, humanoid robots, generative AI, technological advancements", "category": "Technology", "leadparagraph": "Recent breakthroughs in AI and robotics are transforming industries and daily life", "articlebody": "<h3>Humanoid Robots Redefine Interaction</h3> MagicBots latest humanoid robots are designed to learn and adapt, enabling seamless human-machine interaction. These intelligent machines can recognize and respond to emotions, gestures, and voice commands, making them ideal for customer service, healthcare, and education. <h3>Apples Focus on Generative AI</h3> Apples growing interest in generative AI is expected to revolutionize content creation. The company is exploring the potential of AI-generated music, videos, and even code. This technology could significantly impact the creative industries, enabling new forms of artistic expression and automation. <h3>Industry Transformations</h3> The convergence of AI and robotics is transforming various industries. For instance, AI-powered robots are optimizing manufacturing processes, improving efficiency, and reducing costs. In healthcare, AI-assisted diagnosis and treatment are becoming increasingly prevalent. As these technologies continue to evolve, we can expect even more revolutionary changes in the years to come. The advancements in AI and robotics are not limited to these examples. From smart homes to autonomous vehicles, the impact of these technologies is being felt across various sectors. As we move forward, its essential to stay informed about the latest developments and their potential applications. The future of AI and robotics holds much promise. As these technologies continue to advance, we can expect significant improvements in our daily lives, from enhanced productivity to improved healthcare outcomes. Staying up-to-date with the latest breakthroughs and innovations will be crucial in navigating this evolving landscape."}}}'
        field = "saved/result/title"
        result = self.adapter.get_nested_data(data, field)
        self.assertEqual(result, 'AI Revolution Gains Momentum: Humanoid Robots and Generative AI Transform Industries', "Should retrieve the nested value correctly.")


    def test_successful_retrieval_complex_nested3_dict(self):
        # Given a nested dictionary
        raw_data = '{"saved": {"model_id": "meta-llama/Meta-Llama-3.1-70B-Instruct", "step_id": "loop_step1", "result": {"title": "AI Revolution Gains Momentum: Humanoid Robots and Generative AI Transform Industries", "summary": "Latest AI and robotics advancements revolutionize industries and daily life", "tags": "AI, robotics, humanoid robots, generative AI, technological advancements", "category": "Technology", "leadparagraph": "Recent breakthroughs in AI and robotics are transforming industries and daily life", "articlebody": "<h3>Humanoid Robots Redefine Interaction</h3> MagicBots latest humanoid robots are designed to learn and adapt, enabling seamless human-machine interaction. These intelligent machines can recognize and respond to emotions, gestures, and voice commands, making them ideal for customer service, healthcare, and education. <h3>Apples Focus on Generative AI</h3> Apples growing interest in generative AI is expected to revolutionize content creation. The company is exploring the potential of AI-generated music, videos, and even code. This technology could significantly impact the creative industries, enabling new forms of artistic expression and automation. <h3>Industry Transformations</h3> The convergence of AI and robotics is transforming various industries. For instance, AI-powered robots are optimizing manufacturing processes, improving efficiency, and reducing costs. In healthcare, AI-assisted diagnosis and treatment are becoming increasingly prevalent. As these technologies continue to evolve, we can expect even more revolutionary changes in the years to come. The advancements in AI and robotics are not limited to these examples. From smart homes to autonomous vehicles, the impact of these technologies is being felt across various sectors. As we move forward, its essential to stay informed about the latest developments and their potential applications. The future of AI and robotics holds much promise. As these technologies continue to advance, we can expect significant improvements in our daily lives, from enhanced productivity to improved healthcare outcomes. Staying up-to-date with the latest breakthroughs and innovations will be crucial in navigating this evolving landscape."}}}'
        data = BroadcastData(raw_data)
        field = "saved/result/title"
        result = self.adapter.get_nested_data(data.to_json(), field)
        self.assertEqual(result, 'AI Revolution Gains Momentum: Humanoid Robots and Generative AI Transform Industries',
                         "Should retrieve the nested value correctly.")

    def test_retrieval_with_json_string(self):
        # Given a structure where the second level is a JSON string
        data = {
            "level1": '{"level2": {"value": "hello"}}'
        }
        field = "level1/level2/value"
        result = self.adapter.get_nested_data(data, field)
        self.assertEqual(result, "hello", "Should parse the JSON string and continue traversal.")

    def test_missing_key_and_invalid_json(self):
        # Given a structure missing a key
        data_missing_key = {
            "level1": {
                "someOtherKey": "not_value"
            }
        }
        field_missing = "level1/value"
        result_missing = self.adapter.get_nested_data(data_missing_key, field_missing)
        self.assertIsNone(result_missing, "Should return None when the key is missing.")
        self.adapter.logger.error.assert_called_with(
            "Key 'value' not found in current data: {'someOtherKey': 'not_value'}"
        )

        # Given invalid JSON string
        data_invalid_json = {
            "level1": '{"level2": invalid_json_here}'  # invalid JSON
        }
        field_invalid_json = "level1/level2"
        result_invalid_json = self.adapter.get_nested_data(data_invalid_json, field_invalid_json)
        self.assertIsNone(result_invalid_json, "Should return None when JSON parsing fails.")
        # The logger should have logged a JSON parse error
        self.adapter.logger.error.assert_any_call(
            unittest.mock.ANY  # We just ensure an error was called, could match the exact message
        )


if __name__ == '__main__':
    unittest.main()
