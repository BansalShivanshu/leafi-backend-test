from flask import (
    Flask,
    request,
    jsonify,
    make_response,
)
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

logger.info("This is a dummy server to mock subscriptions")
logger.info("Usage: URL usage to subscribe: http://localhost:5000/{ ANY_ENDPOINT_NAME }")
logger.info("Examples: http://localhost:5000/event2, http://localhost:5000/randomevent, http://localhost:5000/leafi-is-cool")
logger.info("*****************************************************************\n")


@app.route("/<string:endpoint>", methods=["POST"])
def listen_to_publishers(endpoint: str):
    endpoint = endpoint.strip()
    logger.info(f"Message incoming to {endpoint}\n")
    data = request.get_json()

    if not endpoint:    # endpoint is empty
        return create_response(
            message="Subscriber cannot be empty. Please check again.",
            status_code=400,    # bad request
        )

    # log the message
    data = request.get_json()
    print(f"{endpoint} received the following message: {data}\n")
    return create_response(
        message=f"{endpoint} received the data.",
        status_code=200,    # http ok
    )


def create_response(message: str, status_code: int):
    return make_response(
        jsonify(
            {
                "message": message,
            },
        ),
        status_code,
    )


if __name__ == "__main__":
    app.run(port=5000)
