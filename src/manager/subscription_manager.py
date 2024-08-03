from typing import (
    Dict,
    Set,
    List,
)


class SubscriptionManager:
    def __init__(self) -> None:
        # map topics with subscribed endpoints
        self._subscription_map: Dict[str, Set[str]] = {}

    def subscribe(self, topic: str, endpoint: str) -> bool:
        """
        Create a subscription between a topic and an endpoint.

        :param topic: Topic to be subscribed
        :param endpoint: Subscribing url
        :return isSubscribed: True if mapping is successful, False otherwise
        """
        if not topic or not endpoint:
            return False
        topic = topic.strip()
        endpoint = endpoint.strip()

        if len(topic) == 0 or len(endpoint) == 0:
            return False

        if topic not in self._subscription_map:
            self._subscription_map[topic] = set()

        self._subscription_map[topic].add(endpoint)
        return True

    def get_subscribers(self, topic: str) -> List[str]:
        subscribers = self._subscription_map.get(topic.strip(), set())
        return list(subscribers)
