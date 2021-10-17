import re
from typing import Tuple
import click
import logging
from colorlog import ColoredFormatter
from .mqtt_client import MQTTClient, Options, Manager, TOPIC_BONEIO
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
        "-d",
        "--debug",
        default=False,
        count=True,
        help="Set Debug mode. Single debug is debug of this lib. Second d is debug of aioxmpp as well.",
    ),
]

_gpio_options = [
    click.option(
        "--relay_prefix_ping",
        envvar="RELAY_PREFIX_PIN",
        type=str,
        required=True,
        default="P9_",
        help="Relay PIN prefix",
    ),
    click.option(
        "--rpin",
        "-r",
        multiple=True,
        required=True,
        help="Relay PIN list. Examples: 1, 11,15 for range. Can be specified multiple times",
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
    debug: int,
    relay_prefix_ping: str,
    rpin: Tuple,
):
    """Create rawscan of Bosch thermostat."""

    def extract_pin(pins):
        set_pins = set()
        for pin in rpin:
            if pin.isnumeric():
                set_pins.add(int(pin))
            else:
                test = re.findall("\d+", pin)
                for i in range(int(test[0]), int(test[1])):
                    set_pins.add(i)
        return set_pins

    print("test", extract_pin(rpin))
    if debug == 0:
        logging.basicConfig(level=logging.INFO)
    if debug > 0:
        logging.basicConfig(
            # colorfmt,
            datefmt=datefmt,
            level=logging.DEBUG,
            filename="out.log",
            filemode="a",
        )
        _LOGGER.info("Debug mode active")
        _LOGGER.debug(f"Lib version is {__version__}")

    client = MQTTClient(host=mqttserver, username=username, password=password)

    options = Options(send_message=client.send_message, topic_prefix=f"{TOPIC_BONEIO}/")
    manager = Manager(options)

    await client.start_client(manager)


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(cli())
