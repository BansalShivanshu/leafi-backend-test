from flask import (
    Flask,
    request,
    jsonify,
    make_response,
)
from typing import List
from manager.subscription_manager import SubscriptionManager
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
        return jsonify(topic_subscribers), 200
    return make_response(
        jsonify(
            {"message": "Topic either does not exist or has no subscribed endpoints"}
        ),
        404,
    )


@app.route("/subscribe/<string:topic>", methods=["POST"])
def setup_subscription(topic: str):
    logger.info(f"Subscription requested for topic {topic}")
    return make_response(jsonify({"message": f"Topic to be subscribed: {topic}"}), 200)


if __name__ == "__main__":
    app.run()
