from flask import (
    Flask,
    request,
    jsonify,
)
from typing import List
from manager.subscription_manager import SubscriptionManager
from manager.message_broker import MessageBroker
from manager.database_manager import DatabaseManager
from utils.response import Response
from utils.validation import Validation
from threading import Lock, Thread
import utils.http_codes as HttpStatus
import logging
import os
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
MESSAGE_TABLE_NAME = os.environ.get("MESSAGE_TABLE_NAME")
ALLOW_POST_EVENT_ENDPOINT = False
subscription_manager = SubscriptionManager()
message_broker = MessageBroker()
database_manager = DatabaseManager(MESSAGE_TABLE_NAME)
thread_lock = Lock()


@app.route("/")
def hello_world():
    return "Hello, World! Usage information in Readme.md"


@app.route("/subscribers/<string:topic>", methods=["GET"])
def get_subscription_info(topic: str):
    topic_subscribers: List[str] = subscription_manager.get_subscribers(topic=topic)
    if topic_subscribers:
        return jsonify(topic_subscribers), HttpStatus.HTTP_OK
    return Response.create(
        message="Topic either does not exist or has no subscribed endpoints",
        status_code=HttpStatus.HTTP_NOT_FOUND,
    )


@app.route("/subscribe/<string:topic>", methods=["POST"])
def setup_subscription(topic: str):
    data = request.get_json()
    logger.info(f"Subscription requested for topic {topic} with data: {data}")

    if not data or "url" not in data or topic.strip() == "":
        return Response.create(
            message="Please check topic and URL again. At least one was not found.",
            status_code=HttpStatus.HTTP_BAD_REQUEST,
        )

    if not Validation.isValidUrl(data["url"]):
        return Response.create(
            message="Invalid URL provided.", status_code=HttpStatus.HTTP_BAD_REQUEST
        )

    isSubscribed = subscription_manager.subscribe(topic=topic, endpoint=data["url"])
    if isSubscribed:
        return Response.create(
            message=f"Subscription created successfully between {topic} and {data['url']}",
            status_code=HttpStatus.HTTP_CREATED,
        )

    return Response.create(
        message="Subscription was unsuccessful",
        status_code=HttpStatus.HTTP_INTERNAL_ERR,
    )


@app.route("/publish/<string:topic>", methods=["POST"])
def publish_message(topic: str):
    data = request.get_json()
    logger.info(f"Message {data} is requested to be published for topic {topic}")

    topic = topic.strip()
    if not topic:
        return Response.create(
            message="Invalid topic, please try again",
            status_code=HttpStatus.HTTP_BAD_REQUEST,
        )
    if not data:
        return Response.create(
            message="No data found to send",
            status_code=HttpStatus.HTTP_BAD_REQUEST,
        )

    subscribers = subscription_manager.get_subscribers(topic=topic)
    if not subscribers:
        return Response.create(
            message=f"No subscribers found for topic {topic}",
            status_code=HttpStatus.HTTP_NOT_FOUND,
        )

    failed_subscribers = message_broker.publish_message(
        topic=topic,
        subscribers=subscribers,
        message=data,
        database_client=database_manager,
    )
    if not failed_subscribers:
        return Response.create(
            message="Message has been sent to all subscribers",
            status_code=HttpStatus.HTTP_OK,
        )
    return Response.create(
        message=f"Message could not be sent to the following subscribers: {failed_subscribers}. \
            Please contact admin/support for more information.",
        status_code=HttpStatus.HTTP_INTERNAL_ERR,
    )


@app.route("/event", methods=["GET"])
def setup_event_subscriber():
    messages = message_broker.retrieve_message(
        subscriber="http://localhost:8000/event", database_client=database_manager
    )
    print(f"got the following messages: {messages}")

    """
    trigger threads to update database status.
    delayed execution by 5s to ensure subscriber recieves messages
    if server fails in the meantime, threads will never execute as they get killed simultaniously.
    """

    def update_db_status(timestamp):
        time.sleep(5)
        database_manager.set_message_received(
            subscriber="http://localhost:8000/event", timestamp=timestamp
        )

    for message in messages:
        print(message["message_timestamp_utc"])
        Thread(
            target=update_db_status, args=(message["message_timestamp_utc"],)
        ).start()

    return Response.create(
        message=f"Following messages were waiting: {messages}",
        status_code=HttpStatus.HTTP_OK,
    )


@app.route("/event", methods=["POST"])
def post_event():
    if not ALLOW_POST_EVENT_ENDPOINT:
        return Response.create(
            message="/event is not accepting any POST requests at this time. Please try again later.",
            status_code=HttpStatus.HTTP_SERVICE_UNAVAILABLE,
        )

    data = request.get_json()
    print(f"Got the following data for POST /EVENT {data}")
    return Response.create(
        message="/event recieved data", status_code=HttpStatus.HTTP_OK
    )


@app.route("/toggle_post_event", methods=["GET"])
def toggle_post_event():
    global ALLOW_POST_EVENT_ENDPOINT
    with thread_lock:
        ALLOW_POST_EVENT_ENDPOINT ^= True
    return Response.create(message="Endpoint toggled", status_code=HttpStatus.HTTP_OK)


if __name__ == "__main__":
    app.run()
