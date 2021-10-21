"""GPIO Relay module."""
from gpiozero import LED
import asyncio
from typing import Callable, Union
from .const import ON, OFF, STATE, RELAY


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
        self._led = LED(pin)
        self._send_message = send_message
        self._relay_topic = f"{topic_prefix}/{RELAY}/"
        self._loop = asyncio.get_running_loop()

    @property
    def is_active(self) -> str:
        """Is relay active."""
        return ON if self._led.is_active else OFF

    @property
    def pin(self) -> str:
        """PIN of the relay"""
        return self._pin

    def turn_on(self) -> None:
        """Call turn on action."""
        self._led.on()
        self._loop.call_soon_threadsafe(self.send_state)

    def turn_off(self) -> None:
        """Call turn off action."""
        self._led.off()
        self._loop.call_soon_threadsafe(self.send_state)

    def toggle(self) -> None:
        """Call toggle action."""
        self._led.toggle()
        self._loop.call_soon_threadsafe(self.send_state)

    def send_state(self) -> None:
        """Send state to Mqtt on action."""
        self._send_message(
            topic=f"{self._relay_topic}{self._pin}", payload={STATE: self.is_active}
        )
