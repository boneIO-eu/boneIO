from Adafruit_BBIO import GPIO
import time
from threading import Timer
from threading import Thread


def setup_input(pin, pull_mode):
    """Set up a GPIO as input."""

    GPIO.setup(pin, GPIO.IN, GPIO.PUD_DOWN if pull_mode == "DOWN" else GPIO.PUD_UP)


def write_output(pin, value):
    """Write a value to a GPIO."""

    GPIO.output(pin, value)


def read_input(pin):
    """Read a value from a GPIO."""

    return GPIO.input(pin) is GPIO.HIGH


def edge_detect(pin, event_callback, bounce):
    """Add detection for RISING and FALLING events."""

    GPIO.add_event_detect(pin, GPIO.BOTH, callback=event_callback, bouncetime=bounce)


class IOInput:

    inputStateDic = {}
    inputPin = None
    hostname = None
    mqttClient = None

    def __init__(self, inputPinParam, hostname, mqttClient):

        try:

            self.inputPin = inputPinParam
            self.hostname = hostname
            self.mqttClient = mqttClient

            self.inputStateDic = {
                "inputState": False,
                "inputPressTime": 0,
                "inputReleaseTime": 0,
                "inputPreviousReleaseTime": 0,
                "inputClick": 0,
            }
            setup_input(self.inputPin, "UP")
            edge_detect

            GPIO.add_event_detect(self.inputPin, GPIO.BOTH)

        except Exception as ex:
            # logging.exception(str(ex))
            print("IOInput.__init__ error:", str(ex))

    def __del__(self):

        GPIO.cleanup()

    def one_click_wait(self, topic):

        try:
            if (
                time.time() - self.inputStateDic["inputReleaseTime"] > 0.3
                and self.inputStateDic["inputReleaseTime"] != 0
            ):
                # print(topic + "/oneClick")
                self.mqttClient.publish(topic + "/oneClick", 1)
                self.inputStateDic["inputPressTime"] = 0
                self.inputStateDic["inputReleaseTime"] = 0
                self.inputStateDic["inputPreviousReleaseTime"] = 0
                self.inputStateDic["inputClick"] = 0
        except Exception as ex:
            # logging.exception(str(ex))
            print("IOInput.one_click_wait error:", str(ex))

    def on_input_event(self, inputPinParam):

        try:
            inputState = GPIO.input(self.inputPin)

            topic = self.hostname + "/input/" + str(self.inputPin)
            # print (topic)

            if inputState == 0 and not self.inputStateDic["inputState"]:
                # print(topic + "/pressed")
                self.mqttClient.publish(topic + "/pressed", 1)
                self.inputStateDic["inputState"] = True
                self.inputStateDic["inputPressTime"] = time.time()
                time.sleep(0.1)
            elif inputState == 1 and self.inputStateDic["inputState"]:
                # print(topic + "/released")
                self.mqttClient.publish(topic + "/released", 1)
                self.inputStateDic["inputState"] = False
                self.inputStateDic["inputReleaseTime"] = time.time()
                self.inputStateDic["inputClick"] += 1
                # Run timer to fire OneClick if nothing else happened
                t = Timer(0.4, self.one_click_wait, args=[topic])
                t.start()

                time.sleep(0.1)

            if (
                self.inputStateDic["inputReleaseTime"]
                - self.inputStateDic["inputPressTime"]
                > 1
                and self.inputStateDic["inputReleaseTime"]
                - self.inputStateDic["inputPressTime"]
                < 5
            ):
                # print(topic + "/longClick")
                self.mqttClient.publish(topic + "/longClick", 1)
                self.inputStateDic["inputPressTime"] = 0
                self.inputStateDic["inputReleaseTime"] = 0
                self.inputStateDic["inputPreviousReleaseTime"] = 0
                self.inputStateDic["inputClick"] = 0
            elif (
                self.inputStateDic["inputReleaseTime"]
                - self.inputStateDic["inputPreviousReleaseTime"]
                < 0.3
                and self.inputStateDic["inputClick"] == 2
            ):
                # print(topic + "/doubleClick")
                self.mqttClient.publish(topic + "/doubleClick", 1)
                self.inputStateDic["inputPressTime"] = 0
                self.inputStateDic["inputReleaseTime"] = 0
                self.inputStateDic["inputClick"] = 0
            self.inputStateDic["inputPreviousReleaseTime"] = self.inputStateDic[
                "inputReleaseTime"
            ]
        except Exception as ex:
            # logging.exception(str(ex))
            print("IOInput.on_input_event error:", str(ex))

    def callback_thread(self):

        try:
            # print("Thread starting for...", self.inputPin)
            GPIO.add_event_callback(self.inputPin, callback=self.on_input_event)
        except Exception as ex:
            # logging.exception(str(ex))
            print("IOInput.callback_thread error:", str(ex))

    def input_start(self):

        try:
            # print("Input starting for...", self.inputPin)
            callbackThread = Thread(target=self.callback_thread)
            callbackThread.start()
        except Exception as ex:
            # logging.exception(str(ex))
            print("IOInput.input_start error:", str(ex))
