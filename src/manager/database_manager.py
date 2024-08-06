import boto3
import logging
import traceback
from typing import (
    List,
    Dict,
)
from boto3.dynamodb.conditions import Attr
from collections import deque

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, table_name) -> None:
        dynamodb = boto3.resource("dynamodb")
        self.message_table = dynamodb.Table(table_name)  # lazy load

    def store_messages(self, subscribers: List[str], message: Dict[str, str]):
        insertion_time_utc = message[
            "message_timestamp_utc"
        ]  # optimized query and gets

        try:
            with self.message_table.batch_writer(
                overwrite_by_pkeys=[
                    "subscriber",
                    "timestamp",
                ]  # allows easy status mutation
            ) as batch:
                for subscriber in subscribers:
                    # insert message row to the table
                    item: dict = {
                        "subscriber": subscriber,
                        "timestamp": insertion_time_utc,
                        "message": message,
                        "is_received": False,
                    }

                    batch.putItem(Item=item)
        except Exception as e:
            logger.fatal(f"[CRITICAL ERROR] Database failed to upload message: {e}")
            logger.fatal(f"Stacktrace: \n {traceback.format_exc()}")
            raise RuntimeError(
                "Unexpected error occured while adding messages to database. Please check error logs."
            )

    def set_message_received(self, subscriber: str, timestamp: str):
        key_args = {"subscriber": subscriber, "timestamp": timestamp}

        data = self.message_table.get_item(Key=key_args, ConsistentRead=True)
        item = data["Item"]

        if item["is_received"]:
            logger.info("message already marked as received")
            return True
        item["is_received"] = True

        response = self.message_table.update_item(
            Key=key_args,
            UpdateExpression="set is_received = :r",
            ExpressionAttributeValues={
                ":r": True,
            },
            ReturnValues="UPDATED_NEW",
        )
        if response["ResponseMetadata"]["HTTPStatusCode"] != 200:
            logger.error(
                f"Unexpected error occured while updating item. Response received: {response}"
            )
            return False
        return True

    def poll_messages(self, subscriber: str):
        """
        Returns a queue to undelivered messages to subscriber from latest to earliest.
        eg: Message sent yesterday will be delivered before a message sent today.

        Queue format: [{ "message": published_message, message_timestamp_utc: utc_time_isoformat }]
        """
        scan_args = {
            "FilterExpression": Attr("is_received").eq(False),
            "ConsistentRead": True,
        }

        try:
            response = self.message_table.scan(**scan_args)
            data = response["Items"]

            while response.get("LastEvaluatedKey"):
                response = self.message_table.scan(
                    **scan_args, ExclusiveStartKey=response["LastEvaluatedKey"]
                )
                data.extend(response["Items"])
                print(f"Second response: {response['Items']}")

            messages = [row["message"] for row in data]
            return deque(sorted(messages, key=lambda x: x["message_timestamp_utc"]))
        except Exception as e:
            logger.fatal(f"[CRITICAL ERROR] Database failed to retreive messages: {e}")
            logger.fatal(f"Stacktrace: {traceback.format_exc()}")
            raise RuntimeError(
                "Unexpected error occured while fetching messages from database. Please check error logs."
            )
