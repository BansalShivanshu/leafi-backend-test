from collections import deque
from typing import (
    Dict,
    List,
    Optional,
)
from datetime import (
    datetime,
    timezone,
)
from utils.http_codes import HTTP_OK
from threading import Lock
import logging
import requests
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageBroker:
    def __init__(self) -> None:
        self._messages_map: Dict[str, deque] = {}
        self._lock = Lock()

    def publish_message(
        self, topic: str, subscribers: List[str], message: Dict[str, str]
    ) -> List:
        """
        Method publishes messages to all subscribers for a given topic.
        If a subscriber is unable to receive messages at this time, they're stored for polling at a later time.

        :return failed_subscribers_list: returns a list of subscribers that did not receive the message
        """
        logger.info(f"Publishing message for topic: {topic}")
        message["topic"] = topic
        message["message_timestamp_utc"] = datetime.now(timezone.utc).isoformat()

        failed_subscribers = []

        with self._lock:
            for subscriber in subscribers:
                if subscriber not in self._messages_map:
                    self._messages_map[subscriber] = deque()
                self._messages_map[subscriber].append(message)
                logger.info(f"added message to queue for {subscriber}")

        for subscriber in subscribers:
            # send message
            try:
                response = requests.post(
                    url=subscriber,
                    json=message,
                    headers={"Content-Type": "application/json"},
                )
                if response.status_code == HTTP_OK:
                    logger.info(f"Message successfully sent to {subscriber}")

                    with self._lock:
                        if self._messages_map.get(subscriber):
                            self._messages_map[subscriber].popleft()
                else:
                    failed_subscribers.append(subscriber)
                    logger.error(
                        f"Failed to send message to {subscriber}, adding to queue for polling. Client returned: {response.text}"
                    )
            except Exception as e:
                failed_subscribers.append(subscriber)
                logger.error(
                    f"Error occured while sending message for topic {topic}: {e}"
                )
                logger.error(f"Stacktrace: {traceback.format_exc()}")

        return failed_subscribers

    def retrieve_message(self, subscriber: str) -> Optional[Dict[str, str]]:
        """
        Poll one message at a time for a given subscriber.

        TODO: ONLY THE TRUE SUBSCRIBER CAN CALL THIS! URL X CANNOT FETCH FOR Y.
            THIS WOULD REQUIRE AN AUTHENTICATION LAYER, OUT OF SCOPE AT THE MOMENT
        """
        with self._lock:
            if self._messages_map.get(subscriber):
                return self._messages_map.get(subscriber).popleft()
        return None
