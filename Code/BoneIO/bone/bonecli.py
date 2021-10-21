import re
import json


from typing import Tuple
import click
import logging
from colorlog import ColoredFormatter
from .mqtt_client import MQTTClient
from .manager import Manager
from .const import PAHO
from .version import __version__
import asyncio
from functools import wraps

_LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
fmt = "%(asctime)s %(levelname)s (%(threadName)s) [%(name)s] %(message)s"
datefmt = "%Y-%m-%d %H:%M:%S"
colorfmt = f"%(log_color)s{fmt}%(reset)s"
logging.getLogger().handlers[0].setFormatter(
    ColoredFormatter(
        colorfmt,
        datefmt=datefmt,
        reset=True,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red",
        },
    )
)


def add_options(options):
    def _add_options(func):
        for option in reversed(options):
            func = option(func)
        return func

    return _add_options


def coro(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@click.group(no_args_is_help=True)
@click.pass_context
@click.version_option(__version__)
@coro
async def cli(ctx):
    """A tool to run commands."""
    pass


_mqtt_options = [
    click.option(
        "--mqttserver",
        envvar="MQTT_SERVER",
        type=str,
        required=True,
        help="mqtt server",
    ),
    click.option(
        "--username",
        envvar="MQTT_USERNAME",
        type=str,
        required=False,
        help="Username",
    ),
    click.option(
        "--password",
        envvar="MQTT_PASSWORD",
        type=str,
        required=False,
        help="Password you set.",
    ),
    click.option(
        "--topic",
        envvar="TOPIC_BONEIO",
        type=str,
        default="boneIO",
        required=True,
        help="Main topic for boneIO to use.",
    ),
    click.option(
        "-d",
        "--debug",
        default=False,
        count=True,
        help="Set Debug mode. Single debug is debug of this lib. Second d is debug of aioxmpp as well.",
    ),
]

_gpio_options = [
    click.option(
        "--relay_prefix_pin",
        envvar="RELAY_PREFIX_PIN",
        type=str,
        required=True,
        default="P9",
        help="Relay PIN prefix",
    ),
    click.option(
        "--rpin",
        "-r",
        multiple=True,
        required=True,
        help="Relay PIN list. Examples: 1, 11,15 for range. Can be specified multiple times",
    ),
    click.option(
        "--input_prefix_pin",
        envvar="INPUT_PREFIX_PIN",
        type=str,
        required=True,
        default="P8",
        help="Input PIN prefix",
    ),
    click.option(
        "--ipin",
        "-i",
        multiple=True,
        required=True,
        help="Input PIN list. Examples: 1, 11,15 for range. Can be specified multiple times",
    ),
    click.option(
        "--ha_autodiscovery",
        "-ha",
        type=bool,
        default=False,
    ),
    click.option(
        "--ha_autodiscovery_prefix",
        type=str,
        default="homeassistant",
    ),
    click.option(
        "--relay_input_map",
        "-rp",
        type=str,
        help='Pass dict so it will automatically turn on relay eg for IN 3 to turn on relay 17: {"3":17}',
    ),
]


@cli.command()
@add_options(_mqtt_options)
@add_options(_gpio_options)
@click.pass_context
@coro
async def run(
    ctx,
    mqttserver: str,
    username: str,
    password: str,
    topic: str,
    debug: int,
    relay_prefix_pin: str,
    rpin: Tuple,
    input_prefix_pin: str,
    ipin: Tuple,
    ha_autodiscovery: bool,
    ha_autodiscovery_prefix: str,
    relay_input_map: str,
):
    """Run BoneIO."""
    if relay_prefix_pin != "" and relay_prefix_pin == input_prefix_pin:
        _LOGGER.info("Same PINs for input and relays. Exiting.")
        return

    def extract_pin(prefix, pins):
        set_pins = set()
        for pin in pins:
            if pin.isnumeric():
                set_pins.add(int(pin))
            else:
                test = re.findall(r"\d+", pin)
                for i in range(int(test[0]), int(test[1]) + 1):
                    set_pins.add(i)
        return [f"{prefix}{x}" for x in sorted(set_pins)]

    relay_pins = extract_pin(
        prefix=f"{relay_prefix_pin}_" if relay_prefix_pin else "", pins=rpin
    )
    input_pins = extract_pin(
        prefix=f"{input_prefix_pin}_" if input_prefix_pin else "", pins=ipin
    )
    if debug == 0:
        logging.getLogger().setLevel(logging.INFO)
    if debug > 0:
        logging.getLogger().setLevel(logging.DEBUG)

        _LOGGER.info("Debug mode active")
        _LOGGER.debug(f"Lib version is {__version__}")
    if debug > 1:
        logging.getLogger(PAHO).setLevel(logging.DEBUG)
    else:
        logging.getLogger(PAHO).setLevel(logging.WARN)

    client = MQTTClient(host=mqttserver, username=username, password=password)
    if relay_input_map:
        relay_input_map = json.loads(relay_input_map)

    manager = Manager(
        send_message=client.send_message,
        topic_prefix=topic,
        relay_pins=relay_pins,
        input_pins=input_pins,
        ha_discovery=ha_autodiscovery,
        ha_discovery_prefix=ha_autodiscovery_prefix,
        relay_input_map=relay_input_map,
    )
    await client.start_client(manager)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(cli())
