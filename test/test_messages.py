import logging

from aiodistbus.messages import Message, SubscribeData

logger = logging.getLogger("aiodistbus")


def test_jsonable_message():
    msg = Message("SUBSCRIBE", SubscribeData(event_type=["test"]))
    json_msg = msg.to_json()
    logger.debug(json_msg)
