import unittest
from unittest.mock import MagicMock

from core.adapters.broadcast_adapter import BroadcastAdapter


class TestBroadcastAdapter(unittest.TestCase):
    def setUp(self):
        self.adapter = BroadcastAdapter()
        self.adapter.logger = MagicMock()  # Mock the logger to avoid actual logging during tests


    def test_prepare_result_with_missing_field(self):
        # Mock the nested field structure
        self.adapter.field = "result/result/nonexistent_field"

        # Input data
        row = {
            "result": {
                "model_id": "meta-llama/Meta-Llama-3.1-8B-Instruct",
                "step_id": "loop_step1",
                "result": {
                    "summary": "AI-powered cooling systems slash energy consumption in data centres"
                }
            }
        }
        self.adapter.field = "result/result/title"
        result = self.adapter.prepare_result(row)

        self.assertIsNone(result)


    def test_prepare_result_with_other_valid_data(self):
        # Mock the nested field structure
        self.adapter.field = "data/result/title"

        # Input data
        input_data = {
            "data": {
                "model_id": "meta-llama/Meta-Llama-3.1-8B-Instruct",
                "step_id": "loop_step1",
                "result": {
                    "title": "Revolutionising Data Centre Sustainability with AI-Powered Innovations",
                    "summary": "AI-powered cooling systems slash energy consumption in data centres",
                    "tags": "DataCentre, Sustainabilty, AI, Cloud Computing, Innovation, EnergyEfficiency",
                    "category": "Tech",
                    "lead_paragraph": "Artificial intelligence is transforming data centre sustainability",
                    "article_body": "Data centres play a vital role in our increasingly digital world..."
                }
            }
        }

        # Expected output
        expected_output = "Revolutionising Data Centre Sustainability with AI-Powered Innovations"

        # Call the method
        result = self.adapter.prepare_result(input_data)

        # Assertions
        self.assertEqual(result, expected_output)


    def test_prepare_result_with_other_valid_dict_return(self):
        # Mock the nested field structure
        self.adapter.field = "data/result"

        # Input data
        input_data = {
            "data": {
                "model_id": "meta-llama/Meta-Llama-3.1-8B-Instruct",
                "step_id": "loop_step1",
                "result": {
                    "title": "Revolutionising Data Centre Sustainability with AI-Powered Innovations",
                    "summary": "AI-powered cooling systems slash energy consumption in data centres",
                    "tags": "DataCentre, Sustainabilty, AI, Cloud Computing, Innovation, EnergyEfficiency",
                    "category": "Tech",
                    "lead_paragraph": "Artificial intelligence is transforming data centre sustainability",
                    "article_body": "Data centres play a vital role in our increasingly digital world..."
                }
            }
        }

        # Expected output
        expected_output = {
                    "title": "Revolutionising Data Centre Sustainability with AI-Powered Innovations",
                    "summary": "AI-powered cooling systems slash energy consumption in data centres",
                    "tags": "DataCentre, Sustainabilty, AI, Cloud Computing, Innovation, EnergyEfficiency",
                    "category": "Tech",
                    "lead_paragraph": "Artificial intelligence is transforming data centre sustainability",
                    "article_body": "Data centres play a vital role in our increasingly digital world..."
                }

        # Call the method
        result = self.adapter.prepare_result(input_data)

        # Assertions
        self.assertEqual(result, expected_output)

    def test_prepare_result_with_valid_data(self):
        self.adapter.field = "saved/title"
        input_data = {
            "saved": {
                "title": "Tackling the sustainability crisis in the cloud and high-tech industry",
                "brief": "As cloud computing and AI continue to grow, data centres are facing unprecedented energy demands and cooling challenges, leading to a sustainability crisis. IBM and AWS are exploring new technologies and collaborations to reduce their carbon footprint."
            }
        }
        expected_output = "Tackling the sustainability crisis in the cloud and high-tech industry"
        result = self.adapter.prepare_result(input_data)
        self.assertEqual(result, expected_output)


if __name__ == "__main__":
    unittest.main()
