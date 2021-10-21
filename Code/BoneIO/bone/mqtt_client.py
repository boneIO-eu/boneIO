"""Provide an MQTT client for providing BoneIO MQTT broker."""
import asyncio
import json
import logging
import uuid
from contextlib import AsyncExitStack
from typing import Any, Callable, Optional, Set, Union

from asyncio_mqtt import Client as AsyncioClient, MqttError
import paho.mqtt.client as mqtt
from paho.mqtt.properties import Properties
from paho.mqtt.subscribeoptions import SubscribeOptions
from .const import PAHO

_LOGGER = logging.getLogger(__name__)


class MQTTClient:
    """Represent an MQTT client."""

    def __init__(
        self,
        host: str,
        port: int = 1883,
        **client_options: Any,
    ) -> None:
        """Set up client."""
        self.host = host
        self.port = port
        if "client_id" not in client_options:
            client_options["client_id"] = mqtt.base62(uuid.uuid4().int, padding=22)
        if "logger" not in client_options:
            client_options["logger"] = logging.getLogger(PAHO)
        client_options["clean_session"] = True
        self.client_options = client_options
        self.asyncio_client: AsyncioClient = None
        self.create_client()
        self.reconnect_interval = 1
        self.publish_queue: asyncio.Queue = asyncio.Queue()

    def create_client(self) -> None:
        """Create the asyncio client."""
        self.asyncio_client = AsyncioClient(
            self.host,
            self.port,
            **self.client_options,
        )

    async def connect(self, *, timeout: float = 10.0) -> None:
        """Connect to the broker.

        Can raise asyncio_mqtt.MqttError.
        """
        await self.asyncio_client.connect(timeout=timeout)

    async def disconnect(self, *, timeout: float = 10.0) -> None:
        """Disconnect from the broker.

        Can raise asyncio_mqtt.MqttError.
        """
        await self.asyncio_client.disconnect(timeout=timeout)

    async def publish(  # pylint:disable=too-many-arguments
        self,
        topic: str,
        payload: Optional[str] = None,
        qos: int = 0,
        retain: bool = False,
        properties: Optional[Properties] = None,
        timeout: float = 10,
    ) -> None:
        """Publish to topic.

        Can raise asyncio_mqtt.MqttError.
        """
        params: dict = {"qos": qos, "retain": retain, "timeout": timeout}
        if payload:
            params["payload"] = payload
        if properties:
            params["properties"] = properties

        _LOGGER.debug("Sending message topic: %s, payload: %s", topic, payload)
        await self.asyncio_client.publish(topic, **params)

    async def subscribe(  # pylint:disable=too-many-arguments
        self,
        topic: str,
        qos: int = 0,
        options: Optional[SubscribeOptions] = None,
        properties: Optional[Properties] = None,
        timeout: float = 10.0,
    ) -> None:
        """Subscribe to topic.

        Can raise asyncio_mqtt.MqttError.
        """
        params: dict = {"qos": qos, "timeout": timeout}
        if options:
            params["options"] = options
        if properties:
            params["properties"] = properties

        await self.asyncio_client.subscribe(topic, **params)

    async def unsubscribe(
        self, topic: str, properties: Optional[Properties] = None, timeout: float = 10.0
    ) -> None:
        """Unsubscribe from topic.

        Can raise asyncio_mqtt.MqttError.
        """
        params: dict = {"timeout": timeout}
        if properties:
            params["properties"] = properties

        await self.asyncio_client.unsubscribe(topic, **params)

    def send_message(self, topic: str, payload: Union[str, dict]) -> None:
        """Send a message from the manager options."""
        to_publish = (topic, json.dumps(payload) if type(payload) == dict else payload)
        self.publish_queue.put_nowait(to_publish)

    async def _handle_publish(self) -> None:
        """Publish messages as they are put on the queue."""
        while True:
            to_publish: tuple = await self.publish_queue.get()
            await self.publish(*to_publish)
            self.publish_queue.task_done()

    async def start_client(self, manager: any) -> None:
        """Start the client with the manager."""
        # Reconnect automatically until the client is stopped.
        while True:
            try:
                await self._subscribe_manager(manager)
            except MqttError as err:
                self.reconnect_interval = min(self.reconnect_interval * 2, 900)
                _LOGGER.error(
                    "MQTT error: %s. Reconnecting in %s seconds",
                    err,
                    self.reconnect_interval,
                )
                await asyncio.sleep(self.reconnect_interval)
                self.create_client()  # reset connect/reconnect futures

    async def _subscribe_manager(self, manager: any) -> None:
        """Connect and subscribe to manager topics."""
        async with AsyncExitStack() as stack:
            tasks: Set[asyncio.Task] = set()

            # Connect to the MQTT broker.
            await stack.enter_async_context(self.asyncio_client)
            # Reset the reconnect interval after successful connection.
            self.reconnect_interval = 1

            publish_task = asyncio.create_task(self._handle_publish())
            tasks.add(publish_task)

            # Messages that doesn't match a filter will get logged and handled here.
            messages = await stack.enter_async_context(
                self.asyncio_client.unfiltered_messages()
            )

            messages_task = asyncio.create_task(
                handle_messages(messages, manager.receive_message)
            )
            tasks.add(messages_task)

            topic = f"{manager.relay_topic}"
            await self.subscribe(topic)

            # Wait for everything to complete (or fail due to, e.g., network errors).
            await asyncio.gather(*tasks)


async def handle_messages(messages: Any, callback: Callable[[str, str], None]) -> None:
    """Handle messages with callback."""
    async for message in messages:
        payload = message.payload.decode()
        _LOGGER.debug("Received message topic: %s, payload: %s", message.topic, payload)
        callback(message.topic, payload)
