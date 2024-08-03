from flask import (
    Flask,
    request,
    jsonify,
)
from typing import List
from manager.subscription_manager import SubscriptionManager
from utils.response import Response
import utils.http_codes as HttpStatus
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
subscription_manager = SubscriptionManager()


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

    if not data or "url" not in data:
        return Response.create(
            message="URL not found to subscribe",
            status_code=HttpStatus.HTTP_BAD_REQUEST,
        )

    isSubscribed = subscription_manager.subscribe(topic=topic, endpoint=data["url"])
    if isSubscribed:
        return Response.create(
            message=f"Subscription created succcessfully between {topic} and {data['url']}",
            status_code=HttpStatus.HTTP_CREATED,
        )

    return Response.create(
        message="Subscription was unsuccessful",
        status_code=HttpStatus.HTTP_INTERNAL_ERR,
    )


if __name__ == "__main__":
    app.run()
