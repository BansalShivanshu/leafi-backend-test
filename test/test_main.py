import unittest
from unittest.mock import patch
from main import app
from utils import http_codes
from requests.exceptions import ConnectionError


class TestFlaskApp(unittest.TestCase):
    def setUp(self) -> None:
        app.testing = True
        self.client = app.test_client()
        self.headers = {"Content-Type": "application/json"}

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
            headers=self.headers,
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
            headers=self.headers,
        )
        self.assertEqual(response.status_code, http_codes.HTTP_INTERNAL_ERR)
        self.assertEqual(
            response.get_json(), {"message": "Subscription was unsuccessful"}
        )

    def test_subscribe_endpoint_bad_requests(self):
        response = self.client.post(
            "/subscribe/ ",
            json={"url": "http://localhost:8000/testing"},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, http_codes.HTTP_BAD_REQUEST)
        self.assertEqual(
            response.get_json()["message"],
            "Please check topic and URL again. At least one was not found.",
        )

        response = self.client.post(
            "subscribe/test-topic",
            json={"url": "http:/localhost:8000/testing"},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, http_codes.HTTP_BAD_REQUEST)
        self.assertEqual(response.get_json()["message"], "Invalid URL provided.")

    @patch("main.message_broker")
    @patch("main.subscription_manager")
    def test_publish_message(
        self, subscription_manager_mock, message_broker_mock
    ):
        subscribers = ["http//localhost:8000/sample"]
        subscription_manager_mock.get_subscribers.return_value = subscribers
        message_broker_mock.publish_message.return_value = None

        response = self.client.post(
            "/publish/test-topic",
            json={"message": "this is a test message"},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, http_codes.HTTP_OK)
        self.assertEqual(
            response.get_json(), {"message": "Message has been sent to all subscribers"}
        )

        message_broker_mock.publish_message.return_value = subscribers
        response = self.client.post(
            "/publish/test-topic",
            json={"message": "this is a test message"},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, http_codes.HTTP_INTERNAL_ERR)
        self.assertEqual(
            response.get_json(),
            {
                "message": f"Message could not be sent to the following subscribers: {subscribers}. \
            Please contact admin/support for more information."
            },
        )

    def test_publish_message_client_side_errors(self):
        response = self.client.post(
            "/publish/ ", json={"message": "test message"}, headers=self.headers
        )
        self.assertEqual(response.status_code, http_codes.HTTP_BAD_REQUEST)
        self.assertEqual(
            response.get_json(), {"message": "Invalid topic, please try again"}
        )

        subscribers = ["http//localhost:8000/sample"]
        response = self.client.post(
            "/publish/test-topic", data={"url": subscribers[0]}, headers=self.headers
        )
        self.assertEqual(response.status_code, http_codes.HTTP_BAD_REQUEST)


    def test_event_get_endpoint(self):
        response = self.client.get("/event")
        self.assertEqual(response.status_code, http_codes.HTTP_OK)
        self.assertEqual(
            response.get_json(), {"message": "Following messages were waiting: {}"}
        )

    def test_event_post_endpoint(self):
        def post_event():
            return self.client.post(
                "/event",
                json={"message": "This is a test message following pub-sub model"},
                headers=self.headers,
            )

        response = post_event()
        self.assertEqual(response.status_code, http_codes.HTTP_SERVICE_UNAVAILABLE)
        self.assertEqual(
            response.get_json(),
            {
                "message": "/event is not accepting any POST requests at this time. Please try again later."
            },
        )

    def test_toggle_events_integration(self):
        def post_event():
            return self.client.post(
                "/event",
                json={"message": "This is a test message following pub-sub model"},
                headers=self.headers,
            )

        post_event()

        response = self.client.get("/toggle_post_event")
        self.assertEqual(response.status_code, http_codes.HTTP_OK)
        self.assertEqual(response.get_json(), {"message": "Endpoint toggled"})

        response = post_event()
        self.assertEqual(response.status_code, http_codes.HTTP_OK)
        self.assertEqual(response.get_json(), {"message": "/event recieved data"})

    def test_flask_subscription_subscribe_integration(self):
        self.client.post(
            "/subscribe/test-topic",
            json={"url": "http://localhost:8000/testing"},
            headers=self.headers,
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

    def test_flask_subscription_events_toggle_integration(self):
        pass
