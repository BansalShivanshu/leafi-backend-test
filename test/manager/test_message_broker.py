import unittest
from unittest.mock import (
    patch,
    MagicMock,
)
from manager.message_broker import MessageBroker
from utils.http_codes import (
    HTTP_OK,
    HTTP_SERVICE_UNAVAILABLE,
)
from requests.exceptions import ConnectionError
from collections import deque


class TestMessageBroker(unittest.TestCase):
    def setUp(self) -> None:
        self.message_broker = MessageBroker()
        self.topic = "test-topic"
        self.subscribers = [
            "http://localhost:8000/testing",
            "https://www.somerandomurl.com/",
        ]
        self.message = {"message": "this is a test message", "whoami": "the publisher"}

    @patch("manager.message_broker.requests")
    def test_publish_message_basic_success(self, request_mock):
        request_mock.post.return_value.status_code = HTTP_OK

        failed_subscribers = self.message_broker.publish_message(
            topic=self.topic, subscribers=self.subscribers, message=self.message
        )

        self.assertTrue(len(failed_subscribers) == 0)
        for subscriber in self.subscribers:
            self.assertTrue(len(self.message_broker._messages_map[subscriber]) == 0)

    @patch("manager.message_broker.requests")
    def test_publish_message_failed_subscribers(self, request_mock):
        request_mock.post.return_value.status_code = HTTP_SERVICE_UNAVAILABLE
        failed_subscribers = self.message_broker.publish_message(
            topic=self.topic, subscribers=self.subscribers, message=self.message
        )

        self.assertTrue(len(failed_subscribers) == 2)
        self.assertIn(self.subscribers[0], failed_subscribers)
        self.assertIn(self.subscribers[1], failed_subscribers)

        for subscriber in self.subscribers:
            self.assertTrue(len(self.message_broker._messages_map[subscriber]) == 1)
            self.assertEqual(
                self.message_broker._messages_map[subscriber].popleft()["topic"],
                self.topic,
            )

    @patch("manager.message_broker.requests")
    def test_publish_message_raised_exception(self, request_mock):
        request_mock.post.side_effect = ConnectionError("Testing raised exception")

        with self.assertLogs("manager.message_broker", level="ERROR"):
            failed_subscribers = self.message_broker.publish_message(
                topic=self.topic, subscribers=self.subscribers, message=self.message
            )
            self.assertEqual(self.subscribers, failed_subscribers)

    def test_retrieve_message(self):
        # test empty
        message = self.message_broker.retrieve_message(subscriber=self.subscribers[0])
        self.assertIsNone(message)

        # test with data
        for subscriber in self.subscribers:
            self.message_broker._messages_map[subscriber] = deque()
            self.message_broker._messages_map[subscriber].append(self.message)
        message = self.message_broker.retrieve_message(self.subscribers[1])
        self.assertEqual(message["whoami"], self.message["whoami"])

    @patch("manager.message_broker.requests")
    def test_message_broker_integration_basic_success(self, request_mock):
        request_mock.post.return_value.status_code = HTTP_OK

        self.message_broker.publish_message(
            topic=self.topic, subscribers=self.subscribers, message=self.message
        )
        message = self.message_broker.retrieve_message(subscriber=self.subscribers[1])
        self.assertIsNone(message)

    @patch("manager.message_broker.datetime")
    @patch("manager.message_broker.requests")
    def test_message_broker_integration_failure(self, request_mock, datetime_mock):
        time_isoformat = "2024-08-04T12:00:00+00:00"

        request_mock.post.return_value.status_code = HTTP_SERVICE_UNAVAILABLE
        datetime_mock.now.return_value = MagicMock()
        datetime_mock.now.return_value.isoformat.return_value = time_isoformat

        self.message_broker.publish_message(
            topic=self.topic, subscribers=self.subscribers, message=self.message
        )

        message = self.message_broker.retrieve_message(subscriber=self.subscribers[0])

        self.assertEqual(message["topic"], self.topic)
        self.assertEqual(message["message_timestamp_utc"], time_isoformat)
