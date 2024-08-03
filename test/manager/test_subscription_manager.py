import unittest
from src.manager.subscription_manager import SubscriptionManager


class TestSubscriptionManager(unittest.TestCase):

    def setUp(self) -> None:
        self.subscription_manager = SubscriptionManager()

    def test_subscribe_basic_success(self):
        result = self.subscription_manager.subscribe(
            "topic1", "http://localhost:8000/test"
        )
        self.assertTrue(result)
        self.assertIn("topic1", self.subscription_manager._subscription_map)
        self.assertIn(
            "http://localhost:8000/test",
            self.subscription_manager._subscription_map["topic1"],
        )

    def test_subscribe_invalid_inputs(self):
        result = self.subscription_manager.subscribe("", "")
        self.assertFalse(result)

        result = self.subscription_manager.subscribe("", "https://localhost:8000/test")
        self.assertFalse(result)

        result = self.subscription_manager.subscribe("test-topic", "")
        self.assertFalse(result)

        result = self.subscription_manager.subscribe(" ", " ")
        self.assertFalse(result)

        result = self.subscription_manager.subscribe(
            None, "https://localhost:8000/test"
        )
        self.assertFalse(result)

        result = self.subscription_manager.subscribe("test-topic", None)
        self.assertFalse(result)

    def test_subscribe_duplicate_endpoint(self):
        self.subscription_manager.subscribe("test-topic", "http://localhost:8000/test")
        result = self.subscription_manager.subscribe(
            "test-topic", "http://localhost:8000/test"
        )
        self.assertTrue(result)
        self.assertEqual(
            len(self.subscription_manager._subscription_map["test-topic"]), 1
        )

    def test_get_subscribers_success(self):
        self.subscription_manager.subscribe("test-topic", "http://localhost:8000/test")
        result = self.subscription_manager.get_subscribers("test-topic")
        self.assertEquals(len(result), 1)
        self.assertEquals(result[0], "http://localhost:8000/test")

    def test_get_subscribers_empty(self):
        result = self.subscription_manager.get_subscribers("test-topic")
        self.assertEquals(len(result), 0)
