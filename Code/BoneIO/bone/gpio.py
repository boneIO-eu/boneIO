from Adafruit_BBIO import GPIO


def setup_output(pin):
    """Set up a GPIO as output."""

    GPIO.setup(pin, GPIO.OUT, pull_up_down=GPIO.PUD_DOWN)


def setup_input(pin, pull_mode="UP"):
    """Set up a GPIO as input."""

    GPIO.setup(pin, GPIO.IN, GPIO.PUD_DOWN if pull_mode == "DOWN" else GPIO.PUD_UP)


def write_output(pin, value):
    """Write a value to a GPIO."""

    GPIO.output(pin, value)


def read_input(pin, on_off=GPIO.LOW):
    """Read a value from a GPIO."""
    return GPIO.input(pin) is on_off


def edge_detect(pin, callback, bounce):
    """Add detection for RISING and FALLING events."""

    GPIO.add_event_detect(pin, GPIO.FALLING, callback=callback, bouncetime=bounce)
