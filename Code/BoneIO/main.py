from .bone.ioinput import IOInput
from .bone.iorelay import IORelay
import paho.mqtt.client as mqtt
import time
import socket
import logging
import sys
import datetime
from daemon import runner

_base_path = "/home/debian/bone-gpio"


class App:
    mqttClient = None

    def __init__(self):
        self.stdin_path = "/dev/null"
        # self.stdout_path = '/dev/tty'
        self.stdout_path = _base_path + "/debug.log"
        self.stderr_path = _base_path + "/error.log"

    def run(self):
        try:
            hostname = socket.gethostname()
            brokerAddress = "localhost"

            mqttClient = mqtt.Client()
            mqttClient.connect(brokerAddress, 1883)
            mqttClient.loop_start()

            relayPinList = []

            # Add gpio 11-18 to list
            for pinNum in range(11, 19):
                relayPinList.append("P9_" + str(pinNum))
            # Add gpio 21-31 to list
            for pinNum in range(21, 32):
                relayPinList.append("P9_" + str(pinNum))

            # Add gpio 42 to list
            relayPinList.append("P9_42")

            # Start relays
            for relayPin in relayPinList:
                IORelay(relayPin, hostname, mqttClient).relay_start()

            # Generate input pin list
            inputPinList = ("P8_" + str(pin) for pin in range(3, 47))

            # Start inputs
            for inputPin in inputPinList:
                IOInput(inputPin, hostname, mqttClient).input_start()

            # input("P.ress any key...")

            while True:
                time.sleep(90)

        except (SystemExit, KeyboardInterrupt):
            # Normal exit getting a signal from the parent process
            pass
        except Exception as ex:
            print(str(datetime.datetime.now()) + " Exception: " + str(ex))
            # logging.exception(str(ex))
            sys.stdout.flush()
        finally:
            logging.info("Finishing")


app = App()
app.run()
daemon_runner = runner.DaemonRunner(app)
daemon_runner.do_action()
