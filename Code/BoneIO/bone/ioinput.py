"""GPIOInputButton to receive signals."""
from gpiozero import Button
from functools import partial
from typing import Callable
from datetime import datetime, timedelta
import logging
import asyncio
from .const import SINGLE, DOUBLE, LONG, ClickTypes

_LOGGER = logging.getLogger(__name__)
DEBOUNCE_DURATION = timedelta(seconds=1)
LONG_PRESS_DURATION = timedelta(seconds=1)


class GpioInputButton:
    """Represent Gpio input switch."""

    def __init__(
        self,
        pin: str,
        press_callback: Callable[[ClickTypes, str], None],
    ) -> None:
        """Setup GPIO Input Button"""
        self._pin = pin
        self._loop = asyncio.get_running_loop()
        self._press_callback = press_callback
        self._button = Button(pin=self._pin, bounce_time=0.005)
        self._first_press_timestamp = None
        self._is_long_press = False
        self._second_press_timestamp = None
        self._second_check = False
        self._button.when_pressed = self.handle_press
        _LOGGER.debug("Configured listening for input pin %s", self._pin)

    def handle_press(self) -> None:
        """Handle the button press callback"""
        # Ignore if we are in a long press
        if self._is_long_press:
            return
        now = datetime.now()

        # Debounce button
        if (
            self._first_press_timestamp is not None
            and now - self._first_press_timestamp < DEBOUNCE_DURATION
        ):
            self._second_press_timestamp = now

        # Second click debounce.
        if (
            self._second_press_timestamp is not None
            and now - self._second_press_timestamp < DEBOUNCE_DURATION
        ):
            return

        if not self._first_press_timestamp:
            self._first_press_timestamp = now

        self._loop.call_soon_threadsafe(
            self._loop.call_later,
            0.1,
            self.check_press_length,
        )

    def check_press_length(self) -> None:
        """Check if it's a single, double or long press"""
        # Check if button is still pressed
        if self._button.is_pressed:
            # Schedule a new check
            self._loop.call_soon_threadsafe(
                self._loop.call_later,
                0.1,
                self.check_press_length,
            )

            # Handle edge case due to multiple clicks
            if self._first_press_timestamp is None:
                return

            # Check if we reached a long press
            diff = datetime.now() - self._first_press_timestamp
            if not self._is_long_press and diff > LONG_PRESS_DURATION:
                self._is_long_press = True
                _LOGGER.debug("Long button press, call callback")
                self._loop.call_soon_threadsafe(
                    partial(self._press_callback, LONG, self._pin)
                )
            return

        # Handle short press
        if not self._is_long_press:
            if not self._second_press_timestamp and not self._second_check:
                # let's try to check if second click will atempt
                self._second_check = True
                self._loop.call_soon_threadsafe(
                    self._loop.call_later,
                    0.3,
                    self.check_press_length,
                )
                return
            if self._second_check:
                if self._second_press_timestamp:
                    _LOGGER.debug(
                        "Double click event, roznica %s",
                        self._second_press_timestamp - self._first_press_timestamp,
                    )
                    self._loop.call_soon_threadsafe(
                        partial(self._press_callback, DOUBLE, self._pin)
                    )

                else:
                    _LOGGER.debug("One click event, call callback")
                    self._loop.call_soon_threadsafe(
                        partial(self._press_callback, SINGLE, self._pin)
                    )

        # Clean state on button released
        self._first_press_timestamp = None
        self._second_press_timestamp = None
        self._second_check = False
        self._is_long_press = False
