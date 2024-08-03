import unittest
from unittest.mock import patch
from main import app
from utils import http_codes


class TestFlaskApp(unittest.TestCase):
    def setUp(self) -> None:
        app.testing = True
        self.client = app.test_client()

    def test_root_endpoint(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, http_codes.HTTP_OK)
        self.assertEqual(
            response.data.decode(), "Hello, World! Usage information in Readme.md"
        )

    def test_subscribe_endpoint(self):
        response = self.client.post(
            "/subscribe/test-topic", data={"url": "http//localhost:8000/testing"}
        )
        self.assertEqual(response.status_code, http_codes.HTTP_UNSUPPORTED_MEDIA_TYPE)

        response = self.client.post(
            "/subscribe/test-topic",
            json={"url": "http://localhost:8000/testing"},
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, http_codes.HTTP_CREATED)
        self.assertEqual(
            response.get_json(),
            {
                "message": "Subscription created successfully between test-topic and http://localhost:8000/testing"
            },
        )

    @patch("main.subscription_manager")
    def test_subscribe_internal_server_error(self, subscription_manager_mock):
        subscription_manager_mock.subscribe.return_value = False
        response = self.client.post(
            "/subscribe/test-topic",
            json={"url": "http://localhost:8000/testing"},
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, http_codes.HTTP_INTERNAL_ERR)
        self.assertEqual(
            response.get_json(), {"message": "Subscription was unsuccessful"}
        )

    def test_subscribe_endpoint_bad_requests(self):
        response = self.client.post(
            "/subscribe/ ",
            json={"url": "http://localhost:8000/testing"},
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, http_codes.HTTP_BAD_REQUEST)
        self.assertEqual(
            response.get_json()["message"],
            "Please check topic and URL again. At least one was not found.",
        )

        response = self.client.post(
            "subscribe/test-topic",
            json={"url": "http:/localhost:8000/testing"},
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(response.status_code, http_codes.HTTP_BAD_REQUEST)
        self.assertEqual(response.get_json()["message"], "Invalid URL provided.")

    def test_flask_subscription_subscribe_integration(self):
        self.client.post(
            "/subscribe/test-topic",
            json={"url": "http://localhost:8000/testing"},
            headers={"Content-Type": "application/json"},
        )

        response = self.client.get("subscribers/non-existent-topic")
        self.assertEqual(response.status_code, http_codes.HTTP_NOT_FOUND)
        self.assertEqual(
            response.get_json(),
            {"message": "Topic either does not exist or has no subscribed endpoints"},
        )

        response = self.client.get("subscribers/test-topic")
        self.assertEqual(response.status_code, http_codes.HTTP_OK)
        self.assertEqual(response.get_json(), ["http://localhost:8000/testing"])
