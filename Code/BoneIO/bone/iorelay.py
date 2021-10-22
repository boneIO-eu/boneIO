"""GPIO Relay module."""
from Adafruit_BBIO.GPIO import HIGH, LOW

import asyncio
from typing import Callable, Union
from .const import ON, OFF, STATE, RELAY
from .gpio import setup_output, read_input, write_output
import logging

_LOGGER = logging.getLogger(__name__)


class GpioRelay:
    """Represents GPIO Relay output"""

    def __init__(
        self,
        pin: str,
        send_message: Callable[[str, Union[str, dict]], None],
        topic_prefix: str,
    ) -> None:
        """Initialize Gpio relay."""
        self._pin = pin
        setup_output(self._pin)
        write_output(self.pin, LOW)
        self._send_message = send_message
        self._relay_topic = f"{topic_prefix}/{RELAY}/"
        self._loop = asyncio.get_running_loop()
        _LOGGER.debug("Setup relay with pin %s", self._pin)

    @property
    def is_active(self) -> str:
        """Is relay active."""
        print("Stat", read_input(self.pin))
        return ON if read_input(self.pin, on_off=HIGH) else OFF

    @property
    def pin(self) -> str:
        """PIN of the relay"""
        return self._pin

    def turn_on(self) -> None:
        """Call turn on action."""
        print("writing UP state", self.pin, self.is_active)
        write_output(self.pin, HIGH)
        self._loop.call_soon_threadsafe(self.send_state)

    def turn_off(self) -> None:
        """Call turn off action."""
        print("low state", self.pin, self.is_active)
        write_output(self.pin, LOW)
        self._loop.call_soon_threadsafe(self.send_state)

    def send_state(self) -> None:
        """Send state to Mqtt on action."""
        self._send_message(
            topic=f"{self._relay_topic}{self._pin}", payload={STATE: self.is_active}
        )
