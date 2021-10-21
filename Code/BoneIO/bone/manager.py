from .ioinput import GpioInputButton
from .iorelay import GpioRelay
from .const import SINGLE, RELAY, ON, OFF, ONLINE, STATE, ClickTypes
from typing import Callable, Optional, Union, List


def ha_availibilty_message(topic, relay_id):
    """Create availability topic for HA."""
    return {
        "availability": [{"topic": f"{topic}/{STATE}"}],
        "command_topic": f"{topic}/relay/{relay_id}/set",
        "device": {
            "identifiers": [topic],
            "manufacturer": "BoneIO",
            "model": "BoneIO Relay Board",
            "name": f"BoneIO {topic}",
            "sw_version": "0.0.1",
        },
        "name": f"Relay {relay_id}",
        "payload_off": OFF,
        "payload_on": OFF,
        "state_topic": f"{topic}/{RELAY}/{relay_id}",
        "unique_id": f"{topic}{RELAY}{relay_id}",
        "value_template": "{{ value_json.state }}",
    }


class Manager:
    """Manager to communicate MQTT with GPIO inputs and outputs."""

    def __init__(
        self,
        send_message: Callable[[str, Union[str, dict]], None],
        topic_prefix: str,
        relay_pins: List,
        input_pins: List,
        ha_discovery: bool = True,
        ha_discovery_prefix: str = "homeassistant",
        relay_input_map: Optional[List] = None,
    ) -> None:
        """Initialize the manager."""
        self.send_message = send_message
        self._topic_prefix = topic_prefix
        self.relay_topic = f"{topic_prefix}/{RELAY}/+/set"
        self._input_pins = input_pins

        self.output = {
            gpio: GpioRelay(
                gpio, send_message=self.send_message, topic_prefix=topic_prefix
            )
            for gpio in relay_pins
        }
        self._relay_input_map = relay_input_map
        for out in self.output.values():
            out.send_state()
            if ha_discovery:
                self.send_ha_autodiscovery(relay=out.pin, prefix=ha_discovery_prefix)

        self.buttons = [
            GpioInputButton(pin=pin, press_callback=self.press_callback)
            for pin in self._input_pins
        ]

        self.send_message(topic=f"{topic_prefix}/{STATE}", payload=ONLINE)

    def press_callback(self, x: ClickTypes, inpin: str) -> None:
        """Press callback to use in input gpio.
        If relay input map is provided also toggle action on relay."""
        self.send_message(topic=f"{self._topic_prefix}/input/{inpin}", payload=x)
        if x == SINGLE and self._relay_input_map:
            output_gpio = self._relay_input_map.get(inpin)
            if output_gpio and output_gpio in self.output:
                self.output.get(output_gpio).toggle()

    def send_ha_autodiscovery(self, relay: str, prefix: str) -> None:
        """Send HA autodiscovery information for each relay."""
        msg = ha_availibilty_message(self._topic_prefix, relay_id=relay)
        topic = f"{prefix}/switch/{self._topic_prefix}/switch/config"
        self.send_message(topic=topic, payload=msg)

    def receive_message(self, topic: str, message: str) -> None:
        """Callback for receiving action from Mqtt."""
        extracted_relay = topic.replace(f"{self._topic_prefix}/{RELAY}/", "").replace(
            "/set", ""
        )
        target_device = self.output.get(extracted_relay)
        if target_device:
            if message == ON:
                target_device.turn_on()
            elif message == OFF:
                target_device.turn_off()
